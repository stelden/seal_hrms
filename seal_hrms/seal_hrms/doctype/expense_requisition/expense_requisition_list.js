// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.listview_settings["Expense Requisition"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const map = {
			Draft: "gray",
			"Pending Approval": "orange",
			Approved: "blue",
			Disbursed: "purple",
			Surrendered: "yellow",
			Returned: "green",
			Closed: "green",
			Cancelled: "red",
		};
		return [__(doc.status), map[doc.status] || "gray", "status,=," + doc.status];
	},
};
