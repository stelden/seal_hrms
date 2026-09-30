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
				["name", "status", "task_assignee_name"]
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
				} else if (frm.doc.status !== "Rejected") {
					frm.add_custom_button(__("Prepare Handover"), () => {
						frappe.call({
							method: "seal_hrms.seal_hrms.task_assignment_actions.prepare_from_leave",
							args: { leave_application: frm.doc.name },
							freeze: true,
							callback: (r) => r.message && frappe.set_route("Form", "Task Assignment", r.message),
						});
					});
				}
			});
	},
});
