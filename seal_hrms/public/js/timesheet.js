// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/* global seal_hrms */

// Timesheet approval (seal_hrms timesheets/approval.py). Only where the
// company's Working Time Policy asks for it: the server says so in onload.
// Elsewhere the Timesheet form is left exactly as ERPNext ships it.

const TIMESHEET_API = "seal_hrms.seal_hrms.timesheets.approval";

// ERPNext's new Timesheet looks the person up by login (`{user_id: me}`) on load.
// On sites where Employee.user_id is at a level staff cannot read, Frappe refuses
// that filter and staff meet a Permission Error before they type anything. This
// answers exactly that lookup, for the person's own record and harmless fields,
// through seal_hrms; every other call goes to Frappe untouched.
// [unsupervised — review]: the lasting fix is deciding who may read user_id.
(function answer_own_employee_lookup() {
	const original = frappe.db.get_value;
	if (original.__seal_hrms_own_employee) return;
	const SAFE = ["name", "company", "employee_name", "department"];
	const patched = function (doctype, filters, fieldname, callback, ...rest) {
		const fields = Array.isArray(fieldname) ? fieldname : [fieldname || "name"];
		const own =
			doctype === "Employee" &&
			filters &&
			typeof filters === "object" &&
			!Array.isArray(filters) &&
			Object.keys(filters).length === 1 &&
			filters.user_id === frappe.session.user &&
			fields.every((f) => SAFE.includes(f));
		if (!own) return original.call(this, doctype, filters, fieldname, callback, ...rest);
		return frappe
			.xcall("seal_hrms.seal_hrms.task_assignment_access.my_employee_fields", { fields })
			.then((message) => {
				message = message || {};
				if (callback) callback(message);
				return { message };
			});
	};
	patched.__seal_hrms_own_employee = true;
	frappe.db.get_value = patched;
})();

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
		const onload = frm.doc.__onload || {};
		if (!onload.approval_on) return;
		seal_hrms.show_where_it_is(frm, onload.where_it_is);
		const state = frm.doc.custom_approval_state || "Not Sent";

		if (frm.doc.docstatus === 0) {
			// Submitting is approving: the server refuses a plain Submit, so do not offer one.
			if (!frm.is_dirty()) frm.page.clear_primary_action();
			if (["Not Sent", "Returned"].includes(state) && onload.can_send) {
				frm.add_custom_button(__("Send for Approval"), () =>
					act(frm, "send_for_approval")
				).addClass("btn-primary");
			}
			if (state === "Waiting for Approval") {
				frm.disable_save();
				if (onload.can_decide) {
					frm.add_custom_button(__("Approve"), () => act(frm, "approve")).addClass(
						"btn-primary"
					);
					frm.add_custom_button(__("Return"), () => return_with_reason(frm));
				}
			}
		}
	},
});

function act(frm, method, args = {}) {
	const go = () =>
		frappe
			.call({
				method: `${TIMESHEET_API}.${method}`,
				args: { name: frm.doc.name, ...args },
				freeze: true,
			})
			.then(() => frm.reload_doc());
	return frm.is_dirty() ? frm.save().then(go) : go();
}

function return_with_reason(frm) {
	frappe.prompt(
		[
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("What needs changing"),
				reqd: 1,
			},
		],
		(values) => act(frm, "return_timesheet", { reason: values.reason }),
		__("Return the timesheet"),
		__("Send")
	);
}

// ---------------------------------------------------------------- the week grid
//
// Where the company fills timesheets in by the week (timesheets/week.py): a line
// per piece of work, a column per day. What is typed goes into
// custom_week_entries; the server writes the time lines from it on save.

const WEEK_API = "seal_hrms.seal_hrms.timesheets.week";
const KIND_LABELS = { "Rest day": __("Rest day"), "Public holiday": __("Public holiday") };

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
		seal_hrms_week.show(frm);
	},
	employee(frm) {
		frm.__seal_weekly = undefined;
		seal_hrms_week.show(frm);
	},
	custom_week_start(frm) {
		const start = frm.doc.custom_week_start;
		if (start && frappe.datetime.str_to_obj(start).getDay() !== 1) {
			const monday = frappe.datetime.add_days(
				start,
				-((frappe.datetime.str_to_obj(start).getDay() + 6) % 7)
			);
			frm.set_value("custom_week_start", monday);
			return;
		}
		seal_hrms_week.show(frm);
	},
});

const seal_hrms_week = {
	async show(frm) {
		const wrapper =
			frm.fields_dict.custom_week_grid && frm.fields_dict.custom_week_grid.$wrapper;
		if (!wrapper || !frm.doc.employee) return;
		if (frm.__seal_weekly === undefined) {
			const r = await frappe.call({
				method: `${WEEK_API}.weekly_for`,
				args: { employee: frm.doc.employee },
			});
			frm.__seal_weekly = r.message || { weekly: false };
		}
		if (!frm.__seal_weekly.weekly) {
			wrapper.empty();
			return;
		}
		if (!frm.doc.custom_week_start && frm.doc.docstatus === 0) {
			const today = frappe.datetime.get_today();
			const back = (frappe.datetime.str_to_obj(today).getDay() + 6) % 7;
			frm.set_value("custom_week_start", frappe.datetime.add_days(today, -back));
			return; // custom_week_start's handler draws it
		}
		// The server writes the time lines from the week, so the form must not ask for them.
		frm.set_df_property("time_logs", "read_only", 1);
		frm.set_df_property("time_logs", "reqd", 0);
		frm.remove_custom_button(__("Start Timer"));
		frm.remove_custom_button(__("Resume Timer"));
		const r = await frappe.call({
			method: `${WEEK_API}.week_context`,
			args: {
				employee: frm.doc.employee,
				week_start: frm.doc.custom_week_start,
				timesheet: frm.doc.name,
			},
		});
		this.draw(frm, wrapper, r.message);
	},

	editable(frm) {
		const state = frm.doc.custom_approval_state || "Not Sent";
		return frm.doc.docstatus === 0 && ["Not Sent", "Returned"].includes(state);
	},

	entries(frm) {
		try {
			return JSON.parse(frm.doc.custom_week_entries || "[]");
		} catch (e) {
			return [];
		}
	},

	store(frm, entries) {
		entries.forEach((entry, index) => (entry.row = index + 1));
		frm.doc.custom_week_entries = JSON.stringify(entries);
		frm.dirty();
	},

	draw(frm, wrapper, context) {
		const editable = this.editable(frm);
		let entries = this.entries(frm);
		if (!entries.length && editable) {
			entries = [
				{
					row: 1,
					activity_type: context.default_activity_type,
					hours: [0, 0, 0, 0, 0, 0, 0],
				},
			];
		}
		const days = context.days;
		const head = days
			.map((day) => {
				const date = frappe.datetime.str_to_obj(day.date);
				const name = moment(date).format("ddd D MMM");
				const marks = [];
				if (KIND_LABELS[day.kind]) marks.push(KIND_LABELS[day.kind]);
				if (day.leave_fraction)
					marks.push(day.leave_fraction === 1 ? __("On leave") : __("Half day leave"));
				const tint = marks.length ? "background: var(--subtle-fg);" : "";
				return `<th class="text-center" style="min-width: 76px; ${tint}">${frappe.utils.escape_html(
					name
				)}
					${marks
						.map(
							(m) =>
								`<div class="small text-muted">${frappe.utils.escape_html(
									m
								)}</div>`
						)
						.join("")}</th>`;
			})
			.join("");
		wrapper.html(`
			<div class="seal-week" style="overflow-x: auto;">
				<table class="table table-bordered table-sm" style="margin-bottom: 8px;">
					<thead><tr>
						<th style="min-width: 160px;">${__("Activity Type")}</th>
						<th style="min-width: 150px;">${__("Project")}</th>
						<th style="min-width: 150px;">${__("Task")}</th>
						<th style="min-width: 160px;">${__("What the work was")}</th>
						${head}
						<th class="text-right">${__("Total")}</th>
						${editable ? "<th></th>" : ""}
					</tr></thead>
					<tbody></tbody>
					<tfoot>
						<tr class="seal-week-totals"><th colspan="4">${__("Day total")}</th>
							${days.map(() => '<th class="text-right"></th>').join("")}<th class="text-right"></th>${
			editable ? "<th></th>" : ""
		}</tr>
						<tr class="text-muted"><td colspan="4">${__("Attendance (hours)")}</td>
							${days
								.map(
									(day) =>
										`<td class="text-right">${
											day.attendance_hours == null
												? "–"
												: frappe.format(day.attendance_hours, {
														fieldtype: "Float",
												  })
										}</td>`
								)
								.join("")}<td></td>${editable ? "<td></td>" : ""}</tr>
					</tfoot>
				</table>
				${
					editable
						? `<button class="btn btn-xs btn-default seal-week-add">${__(
								"Add a line"
						  )}</button>
						   ${
								context.previous_entries.length
									? `<button class="btn btn-xs btn-default seal-week-copy">${__(
											"Copy last week"
									  )}</button>`
									: ""
							}`
						: ""
				}
			</div>`);
		const tbody = wrapper.find("tbody");
		entries.forEach((entry, index) =>
			this.draw_line(frm, tbody, entries, entry, index, editable)
		);
		this.totals(wrapper, entries);
		wrapper.find(".seal-week-add").on("click", () => {
			entries.push({
				activity_type: context.default_activity_type,
				hours: [0, 0, 0, 0, 0, 0, 0],
			});
			this.store(frm, entries);
			this.draw(frm, wrapper, context);
		});
		wrapper.find(".seal-week-copy").on("click", () => {
			const copied = context.previous_entries.map((entry) => ({
				...entry,
				hours: [...(entry.hours || [])],
			}));
			this.store(frm, copied);
			this.draw(frm, wrapper, context);
			frappe.show_alert({
				message: __("Last week's lines copied. Change the hours to this week's."),
				indicator: "green",
			});
		});
	},

	draw_line(frm, tbody, entries, entry, index, editable) {
		const $row = $("<tr></tr>").appendTo(tbody);
		const link = (fieldname, options, get_query) => {
			const $cell = $("<td></td>").appendTo($row);
			if (!editable) {
				$cell.text(entry[fieldname] || "");
				return;
			}
			let drawing = true;
			const control = frappe.ui.form.make_control({
				df: {
					fieldtype: "Link",
					options,
					fieldname,
					placeholder: __(options),
					get_query,
					onchange: () => {
						if (drawing) return;
						entry[fieldname] = control.get_value() || null;
						if (fieldname === "project") entry.task = null;
						this.store(frm, entries);
					},
				},
				parent: $cell,
				only_input: true,
				render_input: true,
			});
			control.set_value(entry[fieldname] || "").then(() => (drawing = false));
		};
		link("activity_type", "Activity Type");
		link("project", "Project");
		link("task", "Task", () => ({ filters: entry.project ? { project: entry.project } : {} }));
		const $note = $("<td></td>").appendTo($row);
		if (editable) {
			$('<input class="form-control input-xs" type="text">')
				.val(entry.description || "")
				.appendTo($note)
				.on("change", (e) => {
					entry.description = e.target.value;
					this.store(frm, entries);
				});
		} else {
			$note.text(entry.description || "");
		}
		const hours = entry.hours || (entry.hours = [0, 0, 0, 0, 0, 0, 0]);
		for (let day = 0; day < 7; day++) {
			const $cell = $('<td class="text-right"></td>').appendTo($row);
			if (!editable) {
				$cell.text(hours[day] ? frappe.format(hours[day], { fieldtype: "Float" }) : "");
				continue;
			}
			$(
				'<input class="form-control input-xs text-right" type="number" min="0" max="23.98" step="0.25">'
			)
				.attr("aria-label", __("Hours"))
				.val(hours[day] || "")
				.appendTo($cell)
				.on("change", (e) => {
					hours[day] = flt(e.target.value);
					this.store(frm, entries);
					this.totals(tbody.closest(".seal-week"), entries);
				});
		}
		$row.append('<td class="text-right seal-week-line-total"></td>');
		if (editable) {
			$(
				`<td><button class="btn btn-xs btn-default" title="${__(
					"Remove this line"
				)}">✕</button></td>`
			)
				.appendTo($row)
				.find("button")
				.on("click", () => {
					entries.splice(index, 1);
					this.store(frm, entries);
					frm.trigger("refresh");
				});
		}
	},

	totals(wrapper, entries) {
		const per_day = [0, 0, 0, 0, 0, 0, 0];
		wrapper.find("tbody tr").each((index, row) => {
			const entry = entries[index] || { hours: [] };
			const line = (entry.hours || []).reduce((sum, h, day) => {
				per_day[day] += flt(h);
				return sum + flt(h);
			}, 0);
			$(row)
				.find(".seal-week-line-total")
				.text(frappe.format(line, { fieldtype: "Float" }));
		});
		const cells = wrapper.find(".seal-week-totals th.text-right");
		per_day.forEach((total, day) =>
			$(cells[day]).text(frappe.format(total, { fieldtype: "Float" }))
		);
		$(cells[7]).text(
			frappe.format(
				per_day.reduce((a, b) => a + b, 0),
				{ fieldtype: "Float" }
			)
		);
	},
};
