// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Leave Planning Cycle — UI smoke tests.
 * Asserts list view, form view, and core required-field structure.
 */

context("Leave Planning Cycle", () => {
	before(() => cy.login().then(() => cy.visit("/app")));
	beforeEach(() => cy.login());

	describe("List View", () => {
		it("opens the Leave Planning Cycle list", () => {
			cy.go_to_list("Leave Planning Cycle");
			cy.get(".page-head").should("contain", "Leave Planning Cycle");
		});

		it("shows standard filters", () => {
			cy.go_to_list("Leave Planning Cycle");
			cy.get(".filter-section").should("exist");
		});

		it("the status field is configured as in_standard_filter on the doctype", () => {
			cy.call("frappe.client.get", { doctype: "DocType", name: "Leave Planning Cycle" }).then((r) => {
				const status_field = (r.message.fields || []).find((f) => f.fieldname === "status");
				expect(status_field).to.exist;
				expect(status_field.in_standard_filter).to.equal(1);
			});
		});
	});

	describe("New Form", () => {
		it("renders the Cycle Definition section", () => {
			cy.go_to_new_form("Leave Planning Cycle");
			cy.assert_field_visible("cycle_name");
			cy.assert_field_visible("company");
			cy.assert_field_visible("leave_period");
			cy.assert_field_visible("status");
			cy.assert_field_visible("open_date");
			cy.assert_field_visible("submission_deadline");
		});

		it("status defaults to Draft and is read-only", () => {
			cy.go_to_new_form("Leave Planning Cycle");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					expect(frm.doc.status).to.equal("Draft");
					expect(frm.fields_dict.status.df.read_only).to.equal(1);
				});
		});

		it("scope_type defaults to All Employees", () => {
			cy.go_to_new_form("Leave Planning Cycle");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					expect(frm.doc.scope_type).to.equal("All Employees");
				});
		});

		it("employee/designation/group scope tabs hide unless scope is narrowed", () => {
			cy.go_to_new_form("Leave Planning Cycle");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					frm.set_value("scope_type", "By Department");
				});
			cy.wait(400);
			cy.assert_field_visible("departments");
		});

		it("reminder offsets default to spec-stated values", () => {
			cy.go_to_new_form("Leave Planning Cycle");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					expect(frm.doc.reminder_offsets_employee).to.equal("30,14,7,3,1");
					expect(frm.doc.reminder_offsets_manager).to.equal("7,1");
				});
		});
	});
});
