// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// Payout Change Request: staff send, HR approves or rejects. The server decides who may
// do what (onload flags) and checks it again on every call (seal_hrms.seal_hrms.payout_change).

const PCR_API = "seal_hrms.seal_hrms.payout_change.";

// Sending and approving need a fresh check of who is asking, where the site has one
// (seal_common's step-up). When the server asks, confirm the password and try again.
function pcr_call(frm, method, args, done) {
	frappe.call({
		method: PCR_API + method,
		args: Object.assign({ name: frm.doc.name }, args || {}),
		freeze: true,
		callback: () => {
			frm.reload_doc();
			if (done) done();
		},
		error: (r) => {
			if (r && r.exc_type === "VerificationNeeded") {
				frappe.prompt(
					{ fieldname: "password", fieldtype: "Password", label: __("Password"), reqd: 1 },
					(values) =>
						frappe.call({
							method: "seal_common.api.v1.sign_in.verify_password",
							args: { password: values.password },
							callback: () => pcr_call(frm, method, args, done),
						}),
					__("Confirm It Is You"),
					__("Continue")
				);
			}
		},
	});
}

frappe.ui.form.on("Payout Change Request", {
	refresh(frm) {
		if (window.seal && seal.config_banner) seal.config_banner.show(frm);
		const can = frm.doc.__onload || {};
		if (frm.is_new()) return;
		if (can.can_send) {
			frm.add_custom_button(__("Send to HR"), () => {
				const go = () => pcr_call(frm, "send");
				frm.is_dirty() ? frm.save().then(go) : go();
			}).addClass("btn-primary");
		}
		if (can.can_decide) {
			frm.add_custom_button(__("Approve"), () => {
				frappe.prompt(
					{
						fieldname: "effective_from",
						fieldtype: "Date",
						label: __("Effective From"),
						default: frappe.datetime.get_today(),
						reqd: 1,
						description: __("Payments made before this day use the old details."),
					},
					(values) => pcr_call(frm, "approve", { effective_from: values.effective_from }),
					__("Approve Payout Change"),
					__("Approve")
				);
			}, __("Decide"));
			frm.add_custom_button(__("Reject"), () => {
				frappe.prompt(
					{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 },
					(values) => pcr_call(frm, "reject", { reason: values.reason }),
					__("Reject Payout Change"),
					__("Reject")
				);
			}, __("Decide"));
		}
		if (can.can_withdraw) {
			frm.add_custom_button(__("Withdraw"), () =>
				frappe.confirm(__("Withdraw this request? HR will not look at it."), () => pcr_call(frm, "withdraw"))
			);
		}
	},
	onload(frm) {
		// Staff ask for themselves: fill in their own Employee.
		if (frm.is_new() && !frm.doc.employee) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
				if (r && r.message && r.message.name) frm.set_value("employee", r.message.name);
			});
		}
	},
});
