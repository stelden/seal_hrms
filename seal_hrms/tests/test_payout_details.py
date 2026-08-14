# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Employee payout details reaching the native ERPNext fields.

Payment rails read `Employee.cell_number` and a default `Bank Account`; this app
captures the same information in its own custom fields. If the copy across is
wrong, an employee looks fully configured and cannot be paid by anything — which
is the state these sites were actually in.

The `is_default` assertions matter more than they look: ERPNext resolves a
party's account with `get_party_bank_account`, which filters on `is_default = 1`.
An account created without it exists, is visible on the Employee, and is
invisible to every payment path.
"""

import frappe
from frappe.tests import IntegrationTestCase

from seal_hrms.seal_hrms import payout_details
from seal_hrms.seal_hrms.api import create_bank_account

COMPANY = "_Test Company"


def _employee(first, last, **values):
    """An Active employee. `cell_number` is passed at insert — it is mandatory here."""
    existing = frappe.db.get_value("Employee", {"employee_name": f"{first} {last}",
                                                "company": COMPANY})
    if existing:
        frappe.db.set_value("Employee", existing, values, update_modified=False)
        return existing

    doc = frappe.get_doc({
        "doctype": "Employee", "first_name": first, "last_name": last,
        "company": COMPANY, "gender": "Male", "date_of_birth": "1988-11-03",
        "date_of_joining": "2023-05-15", "status": "Active",
        "cell_number": values.get("cell_number") or "254700111222",
    }).insert(ignore_permissions=True)
    if values:
        frappe.db.set_value("Employee", doc.name, values, update_modified=False)
    return doc.name


class PayoutDetailsTest(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.skip = not frappe.db.exists("Company", COMPANY)

    def setUp(self):
        if self.skip:
            self.skipTest(f"{COMPANY} is not on this site")
        self._bank = self._ensure_bank()

    def _ensure_bank(self):
        name = "Co-operative Bank of Kenya Ltd"
        if frappe.db.exists("Bank", name):
            return name
        return frappe.get_doc({"doctype": "Bank", "bank_name": name}).insert(
            ignore_permissions=True).name

    def _purge_accounts(self, employee):
        for name in frappe.get_all("Bank Account",
                                   {"party_type": "Employee", "party": employee}, pluck="name"):
            frappe.delete_doc("Bank Account", name, force=True, ignore_permissions=True)

    # ── create_bank_account ──────────────────────────────────────────────────

    def test_first_account_is_the_default(self):
        emp = _employee("Brian", "Otieno")
        self._purge_accounts(emp)
        ba = create_bank_account("Employee", emp, "Brian Otieno", "01109988776", self._bank)
        self.addCleanup(self._purge_accounts, emp)

        self.assertTrue(ba.is_default)
        self.assertEqual(ba.company, COMPANY)

    def test_default_account_is_resolvable_by_erpnext(self):
        """The whole point: ERPNext's own lookup must find it."""
        from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

        emp = _employee("Samuel", "Kariuki")
        self._purge_accounts(emp)
        ba = create_bank_account("Employee", emp, "Samuel Kariuki", "01102233445", self._bank)
        self.addCleanup(self._purge_accounts, emp)

        self.assertEqual(get_party_bank_account("Employee", emp), ba.name)

    def test_second_account_does_not_steal_the_default(self):
        emp = _employee("Peter", "Mutiso")
        self._purge_accounts(emp)
        first = create_bank_account("Employee", emp, "Peter Mutiso", "01100001111", self._bank)
        second = create_bank_account("Employee", emp, "Peter Mutiso Savings",
                                     "01100002222", self._bank)
        self.addCleanup(self._purge_accounts, emp)

        self.assertTrue(first.is_default)
        self.assertFalse(second.is_default)

    def test_same_number_twice_for_one_party_is_refused(self):
        emp = _employee("Daniel", "Kiptoo")
        self._purge_accounts(emp)
        create_bank_account("Employee", emp, "Daniel Kiptoo", "01105556666", self._bank)
        self.addCleanup(self._purge_accounts, emp)

        with self.assertRaises(frappe.ValidationError):
            create_bank_account("Employee", emp, "Daniel Kiptoo", "01105556666", self._bank)

    def test_a_shared_account_number_does_not_block_another_party(self):
        """A global uniqueness check refused joint and pooled accounts outright."""
        one = _employee("Grace", "Wambui")
        two = _employee("Mercy", "Njoki")
        self._purge_accounts(one)
        self._purge_accounts(two)
        self.addCleanup(self._purge_accounts, one)
        self.addCleanup(self._purge_accounts, two)

        # Distinct account names only because Bank Account autonames as
        # "{account_name} - {bank}"; the point under test is the shared NUMBER.
        create_bank_account("Employee", one, "Grace Wambui", "01107778888", self._bank)
        shared = create_bank_account("Employee", two, "Mercy Njoki", "01107778888", self._bank)
        self.assertEqual(shared.bank_account_no, "01107778888")

    # ── sync_payout_details ──────────────────────────────────────────────────

    def test_sync_leaves_a_valid_phone_alone(self):
        emp = _employee("Joseph", "Maina", cell_number="254722334455")
        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["phones_set"], 0)
        self.assertEqual(
            frappe.db.get_value("Employee", emp, "cell_number"), "254722334455"
        )

    def test_sync_reports_an_employee_with_nothing_to_pay_to(self):
        emp = _employee("Victor", "Omondi", cell_number="")
        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["considered"], 1)
        self.assertEqual([s["employee"] for s in report["skipped"]], [emp])

    def test_sync_promotes_an_unresolvable_account_to_default(self):
        """Accounts created before `is_default` was set are repaired, not duplicated."""
        from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

        emp = _employee("Anne", "Chebet")
        self._purge_accounts(emp)
        self.addCleanup(self._purge_accounts, emp)
        orphan = frappe.get_doc({
            "doctype": "Bank Account", "account_name": "Anne Chebet",
            "party_type": "Employee", "party": emp,
            "bank_account_no": "01103334444", "bank": self._bank,
        }).insert(ignore_permissions=True)
        self.assertIsNone(get_party_bank_account("Employee", emp))  # invisible

        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["defaults_fixed"], 1)
        self.assertEqual(report["accounts_created"], 0)   # repaired, not duplicated
        self.assertEqual(get_party_bank_account("Employee", emp), orphan.name)

    def test_sync_is_idempotent(self):
        emp = _employee("Faith", "Nyambura", cell_number="254711223344")
        first = payout_details.sync_payout_details(employees=[emp])
        second = payout_details.sync_payout_details(employees=[emp])

        for key in ("phones_set", "accounts_created", "defaults_fixed"):
            self.assertEqual(first[key], second[key], key)

    def test_sync_refuses_to_write_an_invalid_number(self):
        """`normalize_kenya_mobile_no` returns an invalid 13-digit string for an
        01-prefixed number, so the normalised value is validated before it is
        stored — a wrong mobile number pays a stranger."""
        emp = _employee("Ruth", "Akinyi", cell_number="")
        frappe.db.set_value("Employee", emp, {
            "custom_preferred_payment_method": "Mpesa",
            "custom_account_no": "0110 123456",
        }, update_modified=False)

        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["phones_set"], 0)
        self.assertFalse(frappe.db.get_value("Employee", emp, "cell_number"))
        self.assertTrue(any("not a valid Kenyan number" in s["reason"]
                            for s in report["skipped"]))
