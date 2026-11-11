// Copyright (c) 2025, Stelden EA Ltd and contributors
// For license information, please see license.txt

// What is missing or wrong in this setup, from App Health (SEAL_DEV_RULES §1.18): for example
// phone screens set to ask "is it still you?" on a site that cannot ask yet.
frappe.ui.form.on("SEAL HRMS Settings", {
	refresh(frm) {
		if (window.seal && seal.config_banner) seal.config_banner.show(frm);
	},
});
