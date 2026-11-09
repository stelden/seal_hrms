// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Working Time Policy", {
	setup(frm) {
		frm.set_query("leave_type", () => ({ filters: { is_compensatory: 1 } }));
	},

	refresh(frm) {
		// What stops time off in lieu working for this company (health/working_time.py).
		if (window.seal && window.seal.config_banner) window.seal.config_banner.show(frm);
	},
});
