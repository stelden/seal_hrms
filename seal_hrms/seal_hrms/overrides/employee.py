# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""
Employee payee integrity.

Both of these guard the same failure: money reaching the wrong person. They are
cheap to enforce here and expensive to unpick once a payment has gone out, so
they throw rather than warn.

1. **The Contact must belong to the employee's own User.** `Contact.user` carries
   no unique constraint, and Frappe *adopts* any Contact whose email matches when
   it creates one for a User — so a Supplier's Contact can end up carrying an
   employee's `user`. On this bench one account already owns three Contacts with
   two different mobile numbers. Picking the wrong one pays a stranger.

2. **The Bank Account must belong to this employee.** Nothing in ERPNext stops a
   Link field pointing at another party's account.

Deliberately NOT enforced: having either rail at all. A part-filled employee is
normal — the form says what is missing, and the app that tries to pay refuses.
"""

import frappe
from frappe import _

CONTACT_FIELD = "custom_contact"
BANK_ACCOUNT_FIELD = "custom_salary_bank_account"


def validate(doc, method=None):
    _validate_contact_belongs_to_user(doc)
    _validate_bank_account_belongs_to_employee(doc)


def _validate_contact_belongs_to_user(doc):
    contact = doc.get(CONTACT_FIELD)
    if not contact:
        return

    if not doc.get("user_id"):
        frappe.throw(
            _("{0} has a Contact but no User. Mobile payment details come from the "
              "employee's own User account — create the User first, or clear the Contact.")
            .format(doc.get("employee_name") or doc.name),
            title=_("User Required"),
        )

    owner = frappe.db.get_value("Contact", contact, "user")
    if owner != doc.user_id:
        frappe.throw(
            _("Contact {0} belongs to {1}, not to this employee's User ({2}). "
              "Pick a Contact for {2} instead — paying the wrong number is not recoverable.")
            .format(contact, owner or _("no user"), doc.user_id),
            title=_("Contact Belongs to Someone Else"),
        )


def _validate_bank_account_belongs_to_employee(doc):
    account = doc.get(BANK_ACCOUNT_FIELD)
    if not account or doc.is_new():
        # On insert the Employee has no name yet for the account to point at.
        return

    row = frappe.db.get_value(
        "Bank Account", account, ["party_type", "party"], as_dict=True
    ) or {}
    if row.get("party_type") == "Employee" and row.get("party") == doc.name:
        return

    frappe.throw(
        _("Bank Account {0} belongs to {1} {2}, not to this employee.").format(
            account, _(row.get("party_type") or "no party"), row.get("party") or ""
        ),
        title=_("Bank Account Belongs to Someone Else"),
    )
