// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Planning Cycle Member", {
	refresh(frm) {
		frm.set_query("employee", () => ({
			filters: {
				status: "Active",
				company: frm.doc.company || "",
			},
		}));
		frm.set_query("cycle", () => ({
			filters: { status: ["in", ["Draft", "Open"]] },
		}));
	},
});
