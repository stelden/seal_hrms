// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Leave Planning Pages — smoke tests for the three Phase 3 Pages and
 * the HR-facing workspace.
 */

context("Leave Planning — Pages and Workspace", () => {
	before(() => cy.login().then(() => cy.visit("/app")));
	beforeEach(() => cy.login());

	describe("Workspace", () => {
		it("Leave Planning Admin workspace is reachable", () => {
			cy.visit("/app/leave-planning-admin");
			cy.wait(1500);
			cy.get(".page-head").should("contain.text", "Leave Planning Admin");
		});
	});

	describe("Compliance Dashboard", () => {
		it("renders the page with default empty-state", () => {
			cy.visit("/app/leave-planning-compliance");
			cy.wait(1500);
			cy.get(".page-head").should("contain.text", "Leave Planning Compliance");
			cy.get(".layout-main-section").should("exist");
		});

		it("exposes the cycle filter field", () => {
			cy.visit("/app/leave-planning-compliance");
			cy.wait(1500);
			cy.assert_field_visible("cycle");
			cy.assert_field_visible("department");
			cy.assert_field_visible("status_filter");
		});
	});

	describe("Departmental Coverage Calendar", () => {
		it("renders for a default company selection", () => {
			cy.visit("/app/departmental-coverage-calendar");
			cy.wait(1500);
			cy.get(".page-head").should("contain.text", "Departmental Coverage Calendar");
			cy.assert_field_visible("company");
			cy.assert_field_visible("department");
			cy.assert_field_visible("leave_period");
		});

		it("loads data shell when a company is set", () => {
			cy.visit("/app/departmental-coverage-calendar");
			cy.wait(1500);
			cy.get(".layout-main-section").should("exist");
		});
	});

	describe("Org-wide Coverage Calendar", () => {
		it("renders for HR users", () => {
			cy.visit("/app/org-coverage-calendar");
			cy.wait(1500);
			cy.get(".page-head").should("contain.text", "Org-wide Coverage Calendar");
		});
	});
});
