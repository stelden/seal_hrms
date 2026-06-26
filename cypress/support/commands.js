// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import "@testing-library/cypress/add-commands";
import "@4tw/cypress-drag-drop";
import "cypress-real-events/support";

// ============================================================================
// Authentication
// ============================================================================

Cypress.Commands.add("login", (email, password) => {
	if (!email) {
		email = Cypress.config("testUser") || "Administrator";
	}
	if (!password) {
		password = Cypress.env("adminPassword");
	}
	return cy.session([email, password], () => {
		return cy.request({
			url: "/api/method/login",
			method: "POST",
			body: { usr: email, pwd: password },
		});
	});
});

// ============================================================================
// API helpers
// ============================================================================

Cypress.Commands.add("call", (method, args = {}) => {
	return cy
		.window()
		.its("frappe.csrf_token")
		.then((csrf_token) => {
			return cy
				.request({
					url: `/api/method/${method}`,
					method: "POST",
					body: args,
					headers: {
						Accept: "application/json",
						"Content-Type": "application/json",
						"X-Frappe-CSRF-Token": csrf_token,
					},
					failOnStatusCode: false,
				})
				.then((res) => res.body);
		});
});

Cypress.Commands.add("get_doc", (doctype, name) => {
	return cy
		.window()
		.its("frappe.csrf_token")
		.then((csrf_token) => {
			return cy
				.request({
					method: "GET",
					url: `/api/resource/${doctype}/${name}`,
					headers: {
						Accept: "application/json",
						"X-Frappe-CSRF-Token": csrf_token,
					},
					failOnStatusCode: false,
				})
				.then((res) => res.body);
		});
});

Cypress.Commands.add("insert_doc", (doctype, args, ignore_duplicate = false) => {
	if (!args.doctype) args.doctype = doctype;
	return cy
		.window()
		.its("frappe.csrf_token")
		.then((csrf_token) => {
			return cy
				.request({
					method: "POST",
					url: `/api/resource/${doctype}`,
					body: args,
					headers: {
						Accept: "application/json",
						"Content-Type": "application/json",
						"X-Frappe-CSRF-Token": csrf_token,
					},
					failOnStatusCode: !ignore_duplicate,
				})
				.then((res) => {
					const codes = ignore_duplicate ? [200, 409] : [200];
					expect(res.status).to.be.oneOf(codes);
					return res.body && res.body.data;
				});
		});
});

Cypress.Commands.add("remove_doc", (doctype, name) => {
	return cy
		.window()
		.its("frappe.csrf_token")
		.then((csrf_token) => {
			return cy.request({
				method: "DELETE",
				url: `/api/resource/${doctype}/${name}`,
				headers: { "X-Frappe-CSRF-Token": csrf_token },
				failOnStatusCode: false,
			});
		});
});

// ============================================================================
// Frappe UI helpers
// ============================================================================

Cypress.Commands.add("go_to_list", (doctype) => {
	const slug = doctype.toLowerCase().replace(/ /g, "-");
	cy.visit(`/app/${slug}`);
	cy.wait(800);
});

Cypress.Commands.add("go_to_new_form", (doctype) => {
	const slug = doctype.toLowerCase().replace(/ /g, "-");
	cy.visit(`/app/${slug}/new?_=` + Date.now());
	cy.wait(800);
});

Cypress.Commands.add("assert_field_visible", (fieldname) => {
	cy.get(`[data-fieldname="${fieldname}"]`).should("exist");
});

Cypress.Commands.add("set_value", (fieldname, value) => {
	cy.window()
		.its("cur_frm")
		.then((frm) => frm.set_value(fieldname, value));
});
