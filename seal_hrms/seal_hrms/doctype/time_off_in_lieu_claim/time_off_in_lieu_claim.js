// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/* global seal_hrms */

// The banner (Now / Next / Do) follows the claim's status and who is looking,
// as the server worked it out in onload. Sending and deciding are the Frappe
// Workflow's (the Actions menu); the server checks who may take each action.

const TOIL_API = "seal_hrms.seal_hrms.toil";
const AUTHORISE_FIRST = "Authorise first, then confirm the hours";
const PLANNING = ["Draft", "Returned", "Waiting for Authorisation"];
const WAITING = ["Waiting for Approval", "Waiting for Authorisation"];
/** Actions that send a claim back or refuse it: the person must be told why. */
const NEEDS_REASON = ["Return", "Reject"];

frappe.ui.form.on("Time Off in Lieu Claim", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			frappe.call("seal_hrms.seal_hrms.task_assignment_access.my_employee").then((r) => {
				if (r.message) frm.set_value("employee", r.message);
			});
		}
	},

	employee(frm) {
		if (!frm.is_new() || !frm.doc.employee) return;
		frappe
			.call({
				method: `${TOIL_API}.approval.mode_for`,
				args: { employee: frm.doc.employee },
			})
			.then((r) => {
				frm.doc.mode = r.message;
				frm.trigger("refresh");
			});
	},

	before_workflow_action(frm) {
		if (NEEDS_REASON.includes(frm.selected_workflow_action)) return ask_reason(frm);
	},

	refresh(frm) {
		const onload = frm.doc.__onload || {};
		const first = frm.doc.mode === AUTHORISE_FIRST;
		show_columns(frm, first);
		if (frm.is_new()) {
			seal_hrms.show_where_it_is(frm, {
				type: "info",
				items: [
					{ label: __("Now"), text: __("A new claim, not yet saved.") },
					{
						label: __("Next"),
						text: first
							? __(
									"Once saved and sent, your leave approver agrees the extra work before you do it."
							  )
							: __("Once saved and sent, your leave approver decides it."),
					},
					{
						label: __("Do"),
						text: first
							? __(
									"List each day of extra work you plan, with the hours, then click {0}.",
									[`<b>${__("Save")}</b>`]
							  )
							: __(
									"List each day you worked extra (or click {0}), then click {1}.",
									[`<b>${__("Fill from Records")}</b>`, `<b>${__("Save")}</b>`]
							  ),
					},
				],
			});
		} else {
			seal_hrms.show_where_it_is(frm, onload.where_it_is);
			if (window.seal && window.seal.ProcessMap) window.seal.ProcessMap.attach(frm);
		}

		const editable =
			frm.doc.docstatus === 0 && ["Draft", "Returned"].includes(frm.doc.status || "Draft");
		const confirming = frm.doc.docstatus === 0 && frm.doc.status === "Authorised";
		if ((editable && !first) || confirming) {
			if (frm.is_new() || onload.can_send) add_fill_buttons(frm);
		}
		if (frm.is_new()) return;

		// Sending and deciding are the workflow's: the form's Actions menu.
		if (frm.doc.docstatus === 0 && WAITING.includes(frm.doc.status)) frm.disable_save();
		if (frm.doc.status === "Approved" && onload.is_mine && frm.doc.days_left > 0) {
			frm.add_custom_button(__("Apply for Leave"), () => {
				frappe.new_doc("Leave Application", {
					employee: frm.doc.employee,
					leave_type: frm.doc.leave_type,
				});
			}).addClass("btn-primary");
		}
	},
});

/** Planned hours while the work is being agreed; hours worked once it is authorised. */
function show_columns(frm, first) {
	const planning = first && PLANNING.includes(frm.doc.status || "Draft");
	const grid = frm.fields_dict.lines.grid;
	grid.update_docfield_property("planned_hours", "hidden", first ? 0 : 1);
	grid.update_docfield_property("planned_hours", "in_list_view", first ? 1 : 0);
	grid.update_docfield_property("planned_hours", "read_only", planning ? 0 : 1);
	grid.update_docfield_property("hours", "read_only", planning ? 1 : 0);
	frm.refresh_field("lines");
}

function add_fill_buttons(frm) {
	const fill = (source) => {
		if (!frm.doc.employee) {
			frappe.msgprint(__("Pick the employee first."));
			return;
		}
		const today = frappe.datetime.get_today();
		frappe.prompt(
			[
				{
					fieldname: "from_date",
					fieldtype: "Date",
					label: __("From"),
					reqd: 1,
					default: frappe.datetime.add_days(today, -30),
				},
				{
					fieldname: "to_date",
					fieldtype: "Date",
					label: __("To"),
					reqd: 1,
					default: today,
				},
			],
			(values) => {
				frappe
					.call({
						method: `${TOIL_API}.evidence.get_extra_time`,
						args: { employee: frm.doc.employee, source, ...values },
						freeze: true,
					})
					.then((r) => apply_found(frm, r.message || []));
			},
			source === "Attendance" ? __("Fill from attendance") : __("Fill from timesheets"),
			__("Fill")
		);
	};
	frm.add_custom_button(__("Attendance"), () => fill("Attendance"), __("Fill from Records"));
	frm.add_custom_button(__("Timesheets"), () => fill("Timesheet"), __("Fill from Records"));
}

/** New days are added; when confirming authorised days, their hours worked are filled in. */
function apply_found(frm, found) {
	const by_date = Object.fromEntries(
		(frm.doc.lines || []).map((line) => [line.work_date, line])
	);
	let added = 0;
	let filled = 0;
	if (frm.doc.status === "Authorised") {
		found.forEach((row) => {
			const line = by_date[row.work_date];
			if (line && !line.hours) {
				line.hours = row.hours;
				filled += 1;
			}
		});
	} else {
		// A new claim starts with one blank row; filling from records replaces it.
		frm.doc.lines = (frm.doc.lines || []).filter((line) => line.work_date);
		found
			.filter((row) => !by_date[row.work_date])
			.forEach((row) => {
				frm.add_child("lines", { work_date: row.work_date, hours: row.hours });
				added += 1;
			});
	}
	frm.refresh_field("lines");
	if (!added && !filled) {
		frappe.show_alert({
			message: __("Nothing more to fill in those dates."),
			indicator: "orange",
		});
	} else if (added) {
		frappe.show_alert({
			message: __("{0} days added. Say what the work was on each, then save.", [added]),
			indicator: "green",
		});
	} else {
		frappe.show_alert({
			message: __("Hours filled in on {0} days. Check them, then save.", [filled]),
			indicator: "green",
		});
	}
}

/**
 * Ask for the reason before Return or Reject, and save it first: Frappe reloads
 * the claim before acting, so the reason must already be on it. Closing the
 * dialog cancels the action. Same shape as seal_iam's decision note.
 */
function ask_reason(frm) {
	const action = frm.selected_workflow_action;
	frappe.dom.unfreeze();
	return new Promise((resolve, reject) => {
		let settled = false;
		const d = new frappe.ui.Dialog({
			title: action === "Reject" ? __("Reject the claim") : __("Return the claim"),
			fields: [
				{
					fieldname: "reason",
					fieldtype: "Small Text",
					label: __("Reason"),
					reqd: 1,
					description:
						action === "Reject"
							? __("Say why it is refused; the person reads this.")
							: __(
									"Say what to change; the person reads this before sending it again."
							  ),
				},
			],
			primary_action_label: __(action),
			primary_action(values) {
				settled = true;
				d.hide();
				frappe
					.call({
						method: `${TOIL_API}.workflow.set_decision_note`,
						args: { name: frm.doc.name, note: values.reason },
					})
					.then(() => {
						frappe.dom.freeze();
						resolve();
					}, reject);
			},
		});
		d.onhide = () => settled || reject();
		d.show();
	});
}
