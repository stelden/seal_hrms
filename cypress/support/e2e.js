// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import "./commands";

Cypress.on("uncaught:exception", () => {
	// Frappe Desk emits various ignorable warnings during navigation.
	return false;
});
