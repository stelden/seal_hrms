// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Surrender", {
	onload(frm) {
		frm.set_query("return_bank_account", () => ({
			filters: {
				company: frm.doc.company,
				account_type: ["in", ["Bank", "Cash"]],
				is_group: 0,
			},
		}));
		frm.set_query("expense_requisition", () => ({
			filters: { status: ["in", ["Disbursed", "Surrendered"]], docstatus: 1 },
		}));
	},

	expense_requisition(frm) {
		// Seed the lines from the disbursed requisition (the controller also seeds on save).
		if (!frm.doc.expense_requisition || (frm.doc.items && frm.doc.items.length)) return;
		frappe.db.get_doc("Expense Requisition", frm.doc.expense_requisition).then((req) => {
			frm.set_value("total_disbursed", req.disbursed_amount);
			(req.items || []).forEach((ln) => {
				const row = frm.add_child("items");
				row.expense_type = ln.expense_type;
				row.description = ln.description;
				row.account = ln.account;
				row.disbursed_amount = ln.amount;
				row.actual_amount = ln.amount;
			});
			frm.refresh_field("items");
			frm.trigger("recompute");
		});
	},

	recompute(frm) {
		const actual = (frm.doc.items || []).reduce((s, r) => s + flt(r.actual_amount), 0);
		frm.set_value("total_actual", actual);
		frm.set_value("amount_to_return", Math.max(flt(frm.doc.total_disbursed) - actual, 0));
	},
});

frappe.ui.form.on("Expense Surrender Detail", {
	actual_amount(frm) {
		frm.trigger("recompute");
	},
	items_remove(frm) {
		frm.trigger("recompute");
	},
});
