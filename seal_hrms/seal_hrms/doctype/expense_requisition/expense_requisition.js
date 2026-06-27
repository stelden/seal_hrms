// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Requisition", {
	refresh(frm) {
		frm.trigger("set_status_indicator");
		frm.trigger("add_lifecycle_buttons");
	},

	set_status_indicator(frm) {
		const colors = {
			Draft: "gray", "Pending Approval": "orange", Approved: "blue", Disbursed: "purple",
			Surrendered: "yellow", Returned: "green", Closed: "green", Cancelled: "red",
		};
		if (frm.doc.status) frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "gray");
	},

	add_lifecycle_buttons(frm) {
		if (frm.doc.docstatus !== 1) return;
		const to_disburse = flt(frm.doc.approved_amount) - flt(frm.doc.disbursed_amount);
		if (to_disburse > 0.01 && !frm.doc.dispatched) {
			frm.add_custom_button(__("Disburse"), () => {
				frappe.call({
					method: "seal_hrms.seal_hrms.overrides.payment_entry.get_disbursement_payment_entry",
					args: { requisition: frm.doc.name },
					freeze: true,
					freeze_message: __("Building disbursement payment…"),
					callback(r) {
						if (r.message) {
							const doc = frappe.model.sync(r.message)[0];
							frappe.set_route("Form", doc.doctype, doc.name);
						}
					},
				});
			}, __("Create"));
		}
		if (flt(frm.doc.disbursed_amount) > 0) {
			frm.add_custom_button(__("Expense Surrender"), () => {
				frappe.new_doc("Expense Surrender", { expense_requisition: frm.doc.name });
			}, __("Create"));
		}
	},

	company(frm) {
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency").then((r) => {
				if (r && r.message) frm.set_value("currency", r.message.default_currency);
			});
		}
	},
});
