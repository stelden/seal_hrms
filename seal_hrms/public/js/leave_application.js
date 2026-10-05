// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// A Leave Application shows whether its work is covered, and opens the handover.
frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.docstatus === 2) return;

		frappe.db
			.get_value(
				"Task Assignment",
				{ leave_application: frm.doc.name, docstatus: ["<", 2] },
				["name", "status", "task_assignee", "task_assignee_name", "acceptance"]
			)
			.then(({ message }) => {
				const handover = message && message.name ? message : null;
				if (handover) {
					const colour = { Accepted: "green", Active: "blue", Declined: "red", "Handed Back": "grey" }[handover.status] || "orange";
					frm.dashboard.add_indicator(
						__("Cover: {0} ({1})", [handover.task_assignee_name || __("nobody named"), __(handover.status)]),
						colour
					);
					frm.add_custom_button(__("Open Handover"), () => frappe.set_route("Form", "Task Assignment", handover.name));

					if (handover.status === "Declined") {
						frm.dashboard.set_headline_alert(
							__("The assigned stand-in declined to cover. Please click <b>Open Handover</b> to amend and choose another colleague."),
							"red"
						);
					}
				} else if (frm.doc.status !== "Rejected" && frm.doc.docstatus === 0) {
					frm.add_custom_button(__("Prepare Handover"), () => {
						frappe.call({
							method: "seal_hrms.seal_hrms.task_assignment_actions.prepare_from_leave",
							args: { leave_application: frm.doc.name },
							freeze: true,
							callback: (r) => r.message && frappe.set_route("Form", "Task Assignment", r.message),
						});
					}).addClass("btn-primary");

					// Check company policy to display guidance banner
					frappe.call({
						method: "seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy.policy_for",
						args: { company: frm.doc.company },
						callback(r) {
							const policy = r.message;
							if (policy && policy.requirement && policy.requirement !== "Off") {
								frm.dashboard.set_headline_alert(
									__("<b>Handover Notice:</b> A handover is required for this leave. Please click <b>Prepare Handover</b> to name your stand-in before submitting."),
									"orange"
								);
							}
						},
					});
				}
			});
	},
});

