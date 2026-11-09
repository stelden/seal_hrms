// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/* global seal_hrms */

// The banner (Now / Next / Do) and the buttons follow the claim's status and
// who is looking, as the server worked them out in onload; every action goes
// through an endpoint that checks again.

const TOIL_API = "seal_hrms.seal_hrms.toil";

frappe.ui.form.on("Time Off in Lieu Claim", {
	setup(frm) {
		frm.set_query("task", "lines", (doc, cdt, cdn) => {
			const line = locals[cdt][cdn];
			return { filters: line.project ? { project: line.project } : {} };
		});
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			frappe.call("seal_hrms.seal_hrms.task_assignment_access.my_employee").then((r) => {
				if (r.message) frm.set_value("employee", r.message);
			});
		}
	},

	refresh(frm) {
		const onload = frm.doc.__onload || {};
		if (frm.is_new()) {
			seal_hrms.show_where_it_is(frm, {
				type: "info",
				items: [
					{ label: __("Now"), text: __("A new claim, not yet saved.") },
					{
						label: __("Next"),
						text: __("Once saved and sent, your leave approver decides it."),
					},
					{
						label: __("Do"),
						text: __(
							"List each day you worked extra (or click {0}), then click {1}.",
							[`<b>${__("Fill from Records")}</b>`, `<b>${__("Save")}</b>`]
						),
					},
				],
			});
		} else {
			seal_hrms.show_where_it_is(frm, onload.where_it_is);
		}

		const editable = frm.doc.docstatus === 0 && ["Draft", "Returned"].includes(frm.doc.status);
		if (editable && (frm.is_new() || onload.can_send)) {
			add_fill_buttons(frm);
		}
		if (frm.is_new()) return;

		if (editable && onload.can_send) {
			frm.add_custom_button(__("Send for Approval"), () =>
				act(frm, "approval.send_for_approval")
			).addClass("btn-primary");
		}
		if (frm.doc.docstatus === 0 && frm.doc.status === "Waiting for Approval") {
			frm.disable_save();
			if (onload.can_decide) {
				frm.add_custom_button(__("Approve"), () => act(frm, "approval.approve")).addClass(
					"btn-primary"
				);
				frm.add_custom_button(
					__("Return"),
					() => with_reason(frm, "approval.return_claim", __("Return the claim")),
					__("Other")
				);
				frm.add_custom_button(
					__("Reject"),
					() => with_reason(frm, "approval.reject", __("Reject the claim")),
					__("Other")
				);
			}
		}
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

frappe.ui.form.on("Time Off in Lieu Claim Line", {
	project(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "task", null);
	},
});

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
					.then((r) => {
						const have = new Set((frm.doc.lines || []).map((line) => line.work_date));
						const found = (r.message || []).filter((row) => !have.has(row.work_date));
						if (!found.length) {
							frappe.show_alert({
								message: __("No more days with extra hours in those dates."),
								indicator: "orange",
							});
							return;
						}
						// A new claim starts with one blank row; fill from records replaces it.
						frm.doc.lines = (frm.doc.lines || []).filter((line) => line.work_date);
						found.forEach((row) => {
							const line = frm.add_child("lines", {
								work_date: row.work_date,
								hours: row.hours,
							});
							line.work_done = "";
						});
						frm.refresh_field("lines");
						frappe.show_alert({
							message: __(
								"{0} days added. Say what the work was on each, then save.",
								[found.length]
							),
							indicator: "green",
						});
					});
			},
			source === "Attendance" ? __("Fill from attendance") : __("Fill from timesheets"),
			__("Fill")
		);
	};
	frm.add_custom_button(__("Attendance"), () => fill("Attendance"), __("Fill from Records"));
	frm.add_custom_button(__("Timesheets"), () => fill("Timesheet"), __("Fill from Records"));
}

function act(frm, method, args = {}) {
	const go = () =>
		frappe
			.call({
				method: `${TOIL_API}.${method}`,
				args: { name: frm.doc.name, ...args },
				freeze: true,
			})
			.then(() => frm.reload_doc());
	return frm.is_dirty() ? frm.save().then(go) : go();
}

function with_reason(frm, method, title) {
	frappe.prompt(
		[
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("What the person needs to change or know"),
				reqd: 1,
			},
		],
		(values) => act(frm, method, { reason: values.reason }),
		title,
		__("Send")
	);
}
