// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

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
					const colour =
						{ Accepted: "green", Active: "blue", Declined: "red", "Handed Back": "grey" }[
							handover.status
						] || "orange";
					frm.dashboard.add_indicator(
						__("Cover: {0} ({1})", [handover.task_assignee_name || __("nobody named"), __(handover.status)]),
						colour
					);
					frm.add_custom_button(__("Open Handover"), () =>
						frappe.set_route("Form", "Task Assignment", handover.name)
					);

					if (handover.status === "Declined") {
						frm.dashboard.set_headline_alert(
							__("The assigned stand-in declined to cover. Please click <b>Open Handover</b> to amend and choose another colleague."),
							"red"
						);
					} else if (handover.status === "Awaiting Acceptance") {
						frm.dashboard.set_headline_alert(
							__("Handover sent to <b>{0}</b>. Awaiting their acceptance.", [handover.task_assignee_name || handover.task_assignee]),
							"orange"
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

					// Check HR Settings to display guidance banner
					frappe.db
						.get_value("HR Settings", "HR Settings", [
							"leave_approver_mandatory_in_leave_application",
							"custom_leave_handover_requirement",
						])
						.then(({ message }) => {
							if (
								message &&
								message.leave_approver_mandatory_in_leave_application &&
								message.custom_leave_handover_requirement &&
								message.custom_leave_handover_requirement !== "Off"
							) {
								frm.dashboard.set_headline_alert(
									__("<b>Handover Notice:</b> A handover is required for this leave. Please click <b>Prepare Handover</b> to name your stand-in before submitting."),
									"orange"
								);
							}
						});
				}
			});
	},

	before_workflow_action(frm) {
		return check_handover_before_action(frm);
	},

	before_submit(frm) {
		return check_handover_before_action(frm);
	},
});

function check_handover_before_action(frm) {
	return new Promise((resolve, reject) => {
		if (frm.is_new() || !frm.doc.name) {
			return resolve();
		}

		frappe.db
			.get_value("HR Settings", "HR Settings", [
				"leave_approver_mandatory_in_leave_application",
				"custom_leave_handover_requirement",
				"custom_leave_handover_min_days",
			])
			.then(({ message: settings }) => {
				if (
					!settings ||
					!settings.leave_approver_mandatory_in_leave_application ||
					!settings.custom_leave_handover_requirement ||
					settings.custom_leave_handover_requirement === "Off"
				) {
					return resolve();
				}

				const min_days = flt(settings.custom_leave_handover_min_days || 0);
				const leave_days = flt(frm.doc.total_leave_days || 0);
				if (min_days > 0 && leave_days < min_days) {
					return resolve();
				}

				frappe.db
					.get_value(
						"Task Assignment",
						{ leave_application: frm.doc.name, docstatus: ["<", 2] },
						["name", "status", "task_assignee", "task_assignee_name", "docstatus"]
					)
					.then(({ message: handover }) => {
						if (!handover || !handover.name || !handover.task_assignee) {
							frappe.dom.unfreeze();
							frappe.msgprint({
								title: __("Handover Mandatory"),
								indicator: "red",
								message: __(
									"A handover is mandatory for this leave application. Please click <b>Prepare Handover</b> to choose your stand-in before proceeding."
								),
								primary_action: {
									label: __("Prepare Handover"),
									action(dialog) {
										dialog.hide();
										frappe.dom.unfreeze();
										frappe.call({
											method: "seal_hrms.seal_hrms.task_assignment_actions.prepare_from_leave",
											args: { leave_application: frm.doc.name },
											freeze: true,
											callback: (r) => r.message && frappe.set_route("Form", "Task Assignment", r.message),
										});
									},
								},
								on_hide() {
									frappe.dom.unfreeze();
									frm.refresh();
								},
							});
							frappe.validated = false;
							return reject();
						}

						const req = settings.custom_leave_handover_requirement;
						if (req === "Require Acceptance before Submission" || req === "Require on Approval") {
							if (handover.status !== "Accepted" && handover.status !== "Active") {
								frappe.dom.unfreeze();
								frappe.msgprint({
									title: __("Stand-in Acceptance Required"),
									indicator: "orange",
									message: __(
										"Your stand-in (<b>{0}</b>) must accept the handover before you can apply or submit this leave application. Current handover status is <b>{1}</b>.",
										[handover.task_assignee_name || handover.task_assignee, handover.status || __("Draft")]
									),
									primary_action: {
										label: __("Open Handover"),
										action(dialog) {
											dialog.hide();
											frappe.dom.unfreeze();
											frappe.set_route("Form", "Task Assignment", handover.name);
										},
									},
									on_hide() {
										frappe.dom.unfreeze();
										frm.refresh();
									},
								});
								frappe.validated = false;
								return reject();
							}
						}

						return resolve();
					})
					.catch(() => {
						frappe.dom.unfreeze();
						resolve();
					});
			})
			.catch(() => {
				frappe.dom.unfreeze();
				resolve();
			});
	});
}
