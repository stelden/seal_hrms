// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Requisition", {
	refresh(frm) {
		frm.trigger("set_status_indicator");
		frm.trigger("add_lifecycle_buttons");
	},

	set_status_indicator(frm) {
		const colors = {
			Draft: "gray",
			"Pending Approval": "orange",
			Approved: "blue",
			Disbursed: "purple",
			Surrendered: "green",
			Returned: "green",
			Closed: "green",
			Cancelled: "red",
		};
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "gray");
		}
	},

	add_lifecycle_buttons(frm) {
		// Action buttons (Disburse / Surrender / Return) are wired in B3/B4.
		if (frm.doc.docstatus !== 1) return;
	},

	company(frm) {
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency").then((r) => {
				if (r && r.message) frm.set_value("currency", r.message.default_currency);
			});
		}
	},
});
