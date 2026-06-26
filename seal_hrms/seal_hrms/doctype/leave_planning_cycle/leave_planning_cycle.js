// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Planning Cycle", {
	refresh(frm) {
		frm.set_query("leave_period", () => ({
			filters: {
				is_active: 1,
				company: frm.doc.company || "",
			},
		}));
	},
	company(frm) {
		frm.set_value("leave_period", null);
	},
});
