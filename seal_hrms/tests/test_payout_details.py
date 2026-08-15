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
        self.assertEqual(get_party_bank_account("Employee", emp), orphan.name)
        # Repaired in place, not duplicated.
        self.assertEqual(
            frappe.db.count("Bank Account", {"party_type": "Employee", "party": emp}), 1
        )

    def test_sync_is_idempotent(self):
        emp = _employee("Faith", "Nyambura", cell_number="254711223344")
        first = payout_details.sync_payout_details(employees=[emp])
        second = payout_details.sync_payout_details(employees=[emp])

        for key in ("phones_set", "contacts_linked", "defaults_fixed"):
            self.assertEqual(first[key], second[key], key)

    def test_sync_links_the_users_contact(self):
        """Adopt the Contact Frappe made for the User, so the link need not be manual."""
        user, contact = self._user_with_contact(
            "linkable.payee@example.com", "Linkable", "Payee", "254712909090"
        )
        emp = _employee("Linkable", "Payee", cell_number="254712909090")
        frappe.db.set_value("Employee", emp, {"user_id": user, "custom_contact": None},
                            update_modified=False)

        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["contacts_linked"], 1)
        self.assertEqual(frappe.db.get_value("Employee", emp, "custom_contact"), contact)

    def test_sync_refuses_to_guess_between_several_contacts(self):
        """One User can own several Contacts, with different numbers.

        Frappe adopts any Contact whose email matches rather than making a fresh
        one, and `Contact.user` is not unique. Guessing here would pay whichever
        number happened to sort first.
        """
        user, _ = self._user_with_contact(
            "ambiguous.payee@example.com", "Ambiguous", "Payee", "254712808080"
        )
        second = frappe.get_doc({
            "doctype": "Contact", "first_name": "Ambiguous", "last_name": "Payee Supplies",
            "user": user,
            "phone_nos": [{"phone": "254799000111", "is_primary_mobile_no": 1}],
        }).insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Contact", second.name, force=True)

        emp = _employee("Ambiguous", "Payee", cell_number="254712808080")
        frappe.db.set_value("Employee", emp, {"user_id": user, "custom_contact": None},
                            update_modified=False)

        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["contacts_linked"], 0)
        self.assertFalse(frappe.db.get_value("Employee", emp, "custom_contact"))
        self.assertTrue(any("has 2 Contacts" in s["reason"] for s in report["skipped"]))

    def _user_with_contact(self, email, first, last, mobile):
        """A User and the single Contact Frappe creates for it, carrying `mobile`.

        Frappe creates that Contact itself on User save, so the test uses it
        rather than adding a second one — which is what a real site looks like.
        """
        if not frappe.db.exists("User", email):
            frappe.get_doc({
                "doctype": "User", "email": email, "first_name": first,
                "last_name": last, "enabled": 1, "send_welcome_email": 0,
            }).insert(ignore_permissions=True)

        names = frappe.get_all("Contact", filters={"user": email}, pluck="name")
        self.assertEqual(len(names), 1, f"expected exactly one Contact for {email}")

        contact = frappe.get_doc("Contact", names[0])
        contact.set("phone_nos", [])
        contact.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})
        contact.save(ignore_permissions=True)
        return email, contact.name

    def test_an_01_number_normalises_and_is_stored(self):
        """`01` numbers are ordinary Kenyan mobiles under the CAK 2024 plan.

        `normalize_kenya_mobile_no` used to return `'254' + digits` for them
        instead of `'254' + digits[1:]`, producing a 13-digit string that failed
        its own validator — so every 01 subscriber was rejected as "not a Kenyan
        mobile number" whenever they typed their number the ordinary local way.
        Fixed in seal_common; this keeps it fixed.
        """
        user, contact = self._user_with_contact(
            "airtel.payee@example.com", "Airtel", "Payee", "0110 123456"
        )
        emp = _employee("Airtel", "Payee", cell_number="")
        frappe.db.set_value("Employee", emp, {
            "user_id": user, "custom_contact": contact, "cell_number": "",
        }, update_modified=False)

        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["phones_set"], 1)
        self.assertEqual(frappe.db.get_value("Employee", emp, "cell_number"), "254110123456")

    def test_sync_refuses_to_write_an_invalid_number(self):
        """The normaliser is lenient about input it cannot resolve, so its output
        is validated before being stored — a wrong number pays a stranger."""
        user = "badnumber.payee@example.com"
        if not frappe.db.exists("User", user):
            frappe.get_doc({
                "doctype": "User", "email": user, "first_name": "Ruth",
                "last_name": "Akinyi", "enabled": 1, "send_welcome_email": 0,
            }).insert(ignore_permissions=True)

        contact = frappe.get_doc({
            "doctype": "Contact", "first_name": "Ruth", "last_name": "Akinyi",
            "user": user, "phone_nos": [{"phone": "12345", "is_primary_mobile_no": 1}],
        }).insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact.name, force=True)

        emp = _employee("Ruth", "Akinyi", cell_number="")
        frappe.db.set_value("Employee", emp, {
            "user_id": user, "custom_contact": contact.name, "cell_number": "",
        }, update_modified=False)

        report = payout_details.sync_payout_details(employees=[emp])

        self.assertEqual(report["phones_set"], 0)
        self.assertFalse(frappe.db.get_value("Employee", emp, "cell_number"))
        self.assertTrue(any("not a valid Kenyan number" in s["reason"]
                            for s in report["skipped"]))
