// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Concurrency Rule", {
	refresh(frm) {
		frm.set_query("leave_type", () => ({
			filters: { custom_is_plannable: 1 },
		}));
		frm.set_query("department", () => ({
			filters: { company: frm.doc.company || "" },
		}));
	},
});
