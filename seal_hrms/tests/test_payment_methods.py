# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What a payee can be paid by, and who their details actually belong to.

Two things are worth defending here.

The first is that rails are **independent**. An employee with a phone and no bank
account is payable by mobile money, not "unpayable"; one with both is payable
either way and nothing on the record decides which. The old model could not say
this — it made the payee nominate one rail up front.

The second is **ownership**. `Contact.user` carries no unique constraint and
Frappe adopts any Contact whose email matches when it creates one for a User, so
a Supplier's Contact can end up carrying an employee's user. On this bench one
account already owns three Contacts with two different mobile numbers. If the
wrong one is picked, money goes to a stranger and does not come back — so the
tests reproduce that shape rather than a tidy one.
"""

import frappe
from frappe.tests import IntegrationTestCase

from seal_hrms.seal_hrms import payment_methods
from seal_hrms.seal_hrms.api import create_bank_account

COMPANY = "_Test Company"
BANK = "Co-operative Bank of Kenya Ltd"


def _user(email, first, last):
    if frappe.db.exists("User", email):
        return email
    return frappe.get_doc({
        "doctype": "User", "email": email, "first_name": first, "last_name": last,
        "enabled": 1, "user_type": "System User", "send_welcome_email": 0,
    }).insert(ignore_permissions=True).name


def _contact(first, last, user=None, mobile=None, links=None):
    """A Contact, optionally owned by a User and/or linked to a party."""
    doc = frappe.get_doc({
        "doctype": "Contact", "first_name": first, "last_name": last, "user": user,
    })
    if mobile:
        doc.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})
    for link_doctype, link_name in (links or []):
        doc.append("links", {"link_doctype": link_doctype, "link_name": link_name})
    return doc.insert(ignore_permissions=True)


class PaymentMethodsTest(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.skip = not frappe.db.exists("Company", COMPANY)

    def setUp(self):
        if self.skip:
            self.skipTest(f"{COMPANY} is not on this site")
        self._bank = self._ensure_bank()

    def _ensure_bank(self):
        if frappe.db.exists("Bank", BANK):
            return BANK
        return frappe.get_doc({"doctype": "Bank", "bank_name": BANK}).insert(
            ignore_permissions=True).name

    def _employee(self, first, last, user_email=None, mobile=None):
        """An employee, optionally with a User and that User's Contact."""
        name = frappe.db.get_value(
            "Employee", {"employee_name": f"{first} {last}", "company": COMPANY}
        )
        if not name:
            name = frappe.get_doc({
                "doctype": "Employee", "first_name": first, "last_name": last,
                "company": COMPANY, "gender": "Female", "date_of_birth": "1991-02-14",
                "date_of_joining": "2023-08-01", "status": "Active",
                "cell_number": mobile or "254700000000",
            }).insert(ignore_permissions=True).name
        self.addCleanup(self._purge, name)

        if user_email:
            user = _user(user_email, first, last)
            frappe.db.set_value("Employee", name, "user_id", user, update_modified=False)
            if mobile:
                contact = _contact(first, last, user=user, mobile=mobile)
                frappe.db.set_value("Employee", name, "custom_contact", contact.name,
                                    update_modified=False)
        return name

    def _give_bank_account(self, employee, account_no="01100112233"):
        ba = create_bank_account("Employee", employee, f"{employee} account",
                                 account_no, self._bank)
        frappe.db.set_value("Employee", employee, "custom_salary_bank_account", ba.name,
                            update_modified=False)
        return ba

    def _purge(self, employee):
        for name in frappe.get_all("Bank Account",
                                   {"party_type": "Employee", "party": employee}, pluck="name"):
            frappe.delete_doc("Bank Account", name, force=True, ignore_permissions=True)

    # ── the rails are independent ────────────────────────────────────────────

    def test_mobile_only(self):
        emp = self._employee("Aisha", "Hassan", "aisha.hassan@example.com", "254712000001")
        methods = payment_methods.get_payee_payment_methods("Employee", emp)

        self.assertIsNotNone(methods["mobile"])
        self.assertEqual(methods["mobile"]["account_no"], "254712000001")
        self.assertIsNone(methods["bank"])
        self.assertIn("Bank account", methods["missing"])

    def test_bank_only(self):
        emp = self._employee("Boniface", "Kimani")
        self._give_bank_account(emp, "01100112244")
        methods = payment_methods.get_payee_payment_methods("Employee", emp)

        self.assertIsNone(methods["mobile"])
        self.assertIsNotNone(methods["bank"])
        self.assertEqual(methods["bank"]["account_no"], "01100112244")
        self.assertEqual(methods["bank"]["provider"], self._bank)

    def test_both_rails_and_neither_is_preferred(self):
        emp = self._employee("Caroline", "Wafula", "caroline.wafula@example.com", "254712000002")
        self._give_bank_account(emp, "01100112255")
        methods = payment_methods.get_payee_payment_methods("Employee", emp)

        self.assertIsNotNone(methods["mobile"])
        self.assertIsNotNone(methods["bank"])
        self.assertEqual(methods["missing"], [])
        # Nothing on the record says which one to use — that is the point.
        self.assertNotIn("preferred", frappe.as_json(methods).lower())

    def test_neither_rail(self):
        emp = self._employee("Dennis", "Mutua")
        methods = payment_methods.get_payee_payment_methods("Employee", emp)

        self.assertIsNone(methods["mobile"])
        self.assertIsNone(methods["bank"])
        self.assertEqual(len(methods["missing"]), 2)

    def test_can_pay_by(self):
        emp = self._employee("Esther", "Njeri", "esther.njeri@example.com", "254712000003")
        self.assertTrue(payment_methods.can_pay_by("Employee", emp, "mobile"))
        self.assertFalse(payment_methods.can_pay_by("Employee", emp, "bank"))

    def test_unknown_party_type_is_refused(self):
        with self.assertRaises(frappe.ValidationError):
            payment_methods.get_payee_payment_methods("Customer", "whoever")

    # ── ownership ────────────────────────────────────────────────────────────

    def test_a_user_with_several_contacts_resolves_the_linked_one(self):
        """The real dev.local shape: one user, several Contacts, different numbers."""
        emp = self._employee("Faith", "Chelimo", "faith.chelimo@example.com", "254712000004")
        user = frappe.db.get_value("Employee", emp, "user_id")

        # A Supplier contact that adopted the same user — different number.
        decoy = _contact("Faith", "Chelimo Supplies", user=user, mobile="254799999999")
        self.addCleanup(frappe.delete_doc, "Contact", decoy.name, force=True)

        methods = payment_methods.get_payee_payment_methods("Employee", emp)
        # The employee's OWN linked contact, not whichever the user also owns.
        self.assertEqual(methods["mobile"]["account_no"], "254712000004")

    def test_a_contact_belonging_to_someone_else_is_refused_on_save(self):
        from seal_hrms.seal_hrms.overrides.employee import validate

        emp = self._employee("Grace", "Atieno", "grace.atieno@example.com", "254712000005")
        stranger = _user("stranger.payee@example.com", "Stranger", "Payee")
        foreign = _contact("Stranger", "Payee", user=stranger, mobile="254788888888")
        self.addCleanup(frappe.delete_doc, "Contact", foreign.name, force=True)

        doc = frappe.get_doc("Employee", emp)
        doc.custom_contact = foreign.name
        with self.assertRaises(frappe.ValidationError):
            validate(doc)

    def test_a_contact_without_a_user_is_refused(self):
        from seal_hrms.seal_hrms.overrides.employee import validate

        emp = self._employee("Hannah", "Barasa")
        orphan = _contact("Hannah", "Barasa Personal", mobile="254777777777")
        self.addCleanup(frappe.delete_doc, "Contact", orphan.name, force=True)

        doc = frappe.get_doc("Employee", emp)
        doc.custom_contact = orphan.name
        self.assertFalse(doc.user_id)
        with self.assertRaises(frappe.ValidationError):
            validate(doc)

    def test_another_employees_bank_account_is_refused(self):
        from seal_hrms.seal_hrms.overrides.employee import validate

        mine = self._employee("Irene", "Wangui")
        theirs = self._employee("James", "Onyango")
        their_account = self._give_bank_account(theirs, "01100112266")

        doc = frappe.get_doc("Employee", mine)
        doc.custom_salary_bank_account = their_account.name
        with self.assertRaises(frappe.ValidationError):
            validate(doc)

    def test_a_disabled_bank_account_is_not_a_rail(self):
        emp = self._employee("Kevin", "Ochieng")
        ba = self._give_bank_account(emp, "01100112277")
        frappe.db.set_value("Bank Account", ba.name, "disabled", 1)

        self.assertIsNone(payment_methods.get_payee_payment_methods("Employee", emp)["bank"])
