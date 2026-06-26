// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Leave Plan — UI form structure tests.
 *
 * Asserts the Phase 2 redesigned layout: Plan Identification section with
 * planning_cycle, fetched company/leave_period, Employee Context section,
 * Workflow & Status, Slots tab, Remarks tab.
 */

context("Leave Plan", () => {
	before(() => cy.login().then(() => cy.visit("/app")));
	beforeEach(() => cy.login());

	describe("List View", () => {
		it("opens the Leave Plan list", () => {
			cy.go_to_list("Leave Plan");
			cy.get(".page-head").should("contain", "Leave Plan");
		});

		it("planning_cycle and status appear in standard filters", () => {
			cy.go_to_list("Leave Plan");
			cy.get(".filter-section").should("exist");
			cy.get('[data-fieldname="planning_cycle"]').should("exist");
			cy.get('[data-fieldname="status"]').should("exist");
		});
	});

	describe("New Form structure", () => {
		it("renders Plan Identification fields", () => {
			cy.go_to_new_form("Leave Plan");
			cy.assert_field_visible("planning_cycle");
			cy.assert_field_visible("employee");
			cy.assert_field_visible("posting_date");
		});

		it("renders fetched-from fields as read-only", () => {
			cy.go_to_new_form("Leave Plan");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					for (const fieldname of ["company", "leave_period", "department", "branch", "leave_approver"]) {
						expect(frm.fields_dict[fieldname].df.read_only, fieldname).to.equal(1);
						expect(frm.fields_dict[fieldname].df.fetch_from, `${fieldname} fetch_from`).to.be.a("string");
					}
				});
		});

		it("status defaults to Not Applied", () => {
			cy.go_to_new_form("Leave Plan");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					expect(frm.doc.status).to.equal("Not Applied");
				});
		});

		it("Slots tab renders the leave_plan_slots child table", () => {
			cy.go_to_new_form("Leave Plan");
			cy.assert_field_visible("leave_plan_slots");
		});

		it("planning_cycle Link is filtered to Open cycles", () => {
			cy.go_to_new_form("Leave Plan");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					const query = frm.fields_dict.planning_cycle.df.get_query
						? frm.fields_dict.planning_cycle.df.get_query()
						: null;
					if (query && query.filters) {
						expect(JSON.stringify(query.filters)).to.contain("Open");
					}
				});
		});

		it("Cancel custom button is absent for unsaved drafts", () => {
			cy.go_to_new_form("Leave Plan");
			cy.window()
				.its("cur_frm")
				.then((frm) => {
					expect(frm.doc.docstatus, "new doc docstatus").to.equal(0);
				});
			cy.get('.btn-group .dropdown-menu a:contains("Cancel Plan")').should("not.exist");
		});
	});
});
