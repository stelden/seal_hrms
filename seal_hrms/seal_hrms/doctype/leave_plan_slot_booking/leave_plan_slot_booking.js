// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Plan Slot Booking", {
	refresh(frm) {
		frm.disable_save();
	},
});
