# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""We must not declare Custom Fields that belong to another app.

`sync_customizations` **upserts** by `(dt, fieldname)` — it updates whatever it
finds rather than skipping it (frappe/modules/utils.py). So when two apps declare
the same field, the one that migrates last silently rewrites the other's
attributes: its `permlevel`, its `depends_on`, its `mandatory_depends_on`. Nothing
errors and nothing is logged; the field simply changes meaning.

That had really happened here. This app re-declared fourteen hrms core fields and
csf_ke's whole statutory block, and csf_ke's own patch deletes and recreates that
block at permlevel 0 — undoing the permlevel 2 this app applies to the same
fields. Whichever ran last won.

These tests read the app's JSON, not the database, because the declaration is what
causes the conflict. They fail the moment a field owned elsewhere reappears in our
file, which is the only reliable guard — the damage is invisible at runtime.
"""

import json
import unittest
from pathlib import Path

import frappe

# `get_app_path` returns the inner package (apps/seal_hrms/seal_hrms), while
# custom/ lives under the module directory below it.
CUSTOM_DIR = Path(frappe.get_app_path("seal_hrms")) / "seal_hrms" / "custom"

# Owned by hrms (hrms/setup.py) and csf_ke (csf_ke/.../custom/employee.json).
# Both are on this bench, so both can migrate after us.
FOREIGN_EMPLOYEE_FIELDS = {
    # hrms core
    "approvers_section", "column_break_45", "default_shift", "employment_type",
    "expense_approver", "grade", "health_insurance_section",
    "health_insurance_provider", "health_insurance_no", "job_applicant",
    "leave_approver", "payroll_cost_center", "salary_cb", "shift_request_approver",
    "employee_advance_account",
    # csf_ke statutory block
    "national_id", "nssf_no", "nhif_no", "tax_id", "statutory",
    "bank_branch_name", "custom_sort_code",
}

# Removed with the multi-rail payee model. Kept as a list so a revert is loud.
RETIRED_PAYMENT_FIELDS = {
    "custom_preferred_payment_method",
    "custom_bank_account",
    "custom_mpesa_contact",
    "custom_account_name",
    "custom_account_no",
    "custom_mpesa_salary_contact",
    "custom_mpesa_salary_mobile_no",
    "custom_new_bank_account",
    "custom_new_mpesa_contact",
    "custom_new_mpesa_salary_contact",
    "custom_new_salary_bank_account",
    "custom_create_contact",
}


def _declared(doctype_file):
    """Fieldnames this app declares for a doctype.

    A missing file raises rather than returning an empty set: every assertion
    below would otherwise pass vacuously, and a silently-green ownership test is
    worse than none.
    """
    path = CUSTOM_DIR / doctype_file
    if not path.exists():
        raise AssertionError(f"expected customisations at {path}")
    with open(path) as fh:
        data = json.load(fh)
    return {f["fieldname"] for f in data.get("custom_fields", [])}


class FieldOwnershipTest(unittest.TestCase):
    def test_we_do_not_declare_other_apps_employee_fields(self):
        clash = sorted(_declared("employee.json") & FOREIGN_EMPLOYEE_FIELDS)
        self.assertEqual(
            clash, [],
            "seal_hrms must not declare fields owned by hrms or csf_ke — whichever "
            f"app migrates last rewrites the other's attributes: {clash}",
        )

    def test_retired_payment_fields_are_not_reintroduced(self):
        back = sorted(_declared("employee.json") & RETIRED_PAYMENT_FIELDS)
        self.assertEqual(
            back, [],
            f"these encode the retired single-preferred-rail model: {back}",
        )

    def test_every_declared_field_is_ours(self):
        """Anything we declare is either a custom_ field or a layout element."""
        theirs = sorted(
            name for name in _declared("employee.json")
            if not name.startswith("custom_")
        )
        self.assertEqual(
            theirs, [],
            f"seal_hrms should only declare custom_* fields on Employee: {theirs}",
        )

    def test_the_surviving_payee_fields_are_present(self):
        declared = _declared("employee.json")
        for fieldname in ("custom_contact", "custom_salary_bank_account",
                          "custom_bank_account_name", "custom_bank_account_no",
                          "custom_bank_provider", "custom_mobile_account_name",
                          "custom_mobile_account_no", "custom_cell_number_provider"):
            self.assertIn(fieldname, declared)

    def test_field_order_does_not_pin_the_payment_fields(self):
        """`field_order` overrides `insert_after`, so a pinned field cannot move.

        The Payment Details fields are positioned by `insert_after`. Naming any of
        them in the layout snapshot would freeze it wherever the snapshot was
        taken — which is how the mobile provider ended up in Address & Contacts
        while the rest of its section sat in Overview.
        """
        with open(CUSTOM_DIR / "employee.json") as fh:
            data = json.load(fh)

        pinned = set()
        for ps in data.get("property_setters", []):
            if ps.get("property") == "field_order":
                pinned |= set(json.loads(ps["value"]))

        payment_fields = {
            "custom_payment_details", "custom_payment_details_cb0",
            "custom_bank_account_name", "custom_bank_account_no", "custom_bank_provider",
            "custom_mobile_account_name", "custom_mobile_account_no",
            "custom_cell_number_provider",
        }
        self.assertEqual(sorted(pinned & payment_fields), [])
        # And nothing deleted may linger there either.
        self.assertEqual(sorted(pinned & RETIRED_PAYMENT_FIELDS), [])


class EmployeeFormTest(unittest.TestCase):
    """The bits of the form an operator actually relies on."""

    def test_payment_details_renders_on_the_overview_tab(self):
        """Anchored mid-tab on purpose.

        Inserting after a tab's LAST field puts the new section after the
        following Tab Break, which landed Payment Details in "Joining".
        """
        meta = frappe.get_meta("Employee")
        tab = None
        placement = {}
        for field in meta.fields:
            if field.fieldtype == "Tab Break":
                tab = field.label or field.fieldname
            placement[field.fieldname] = tab

        for fieldname in ("custom_payment_details", "custom_bank_account_name",
                          "custom_bank_account_no", "custom_bank_provider",
                          "custom_mobile_account_name", "custom_mobile_account_no",
                          "custom_cell_number_provider"):
            self.assertEqual(placement.get(fieldname), "Overview", fieldname)

    def test_create_bank_account_is_offered_only_while_there_is_none(self):
        depends_on = frappe.get_meta("Employee").get_field(
            "custom_create_salary_bank_account").depends_on or ""
        self.assertIn("!doc.custom_salary_bank_account", depends_on.replace(" ", ""))

    def test_update_contact_is_offered_only_when_there_is_one(self):
        depends_on = frappe.get_meta("Employee").get_field(
            "custom_update_contact").depends_on or ""
        self.assertIn("doc.custom_contact", depends_on)
