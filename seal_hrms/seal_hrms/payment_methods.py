# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""
What a payee can be paid by.

A payee is not "an M-Pesa person" or "a bank person" — they hold whatever details
they hold, and the rail is chosen when a payment is actually made, by whichever
app is making it. This module answers one question: *which rails can this payee
be paid on right now, and what is missing for the ones they cannot?*

It replaces `seal_hr_api.get_preferred_payment_method`, which asked the payee to
nominate a single preference up front and then hid the other rail's fields behind
`depends_on` — so a payee who could be paid two ways looked like they could only
be paid one, and the disbursing app had to reverse-engineer its rail out of that
one answer.

Works for Employee and Supplier alike, so a requisition paying a third party reads
the same shape as one paying staff.

**This module is a reader.** It never writes, and it never throws for incomplete
data: a half-configured payee is normal while a record is being filled in. Gaps
come back in `missing` for the caller to render or refuse on.
"""

import frappe
from frappe import _

MOBILE = "mobile"
BANK = "bank"

#: Where each party type keeps its Contact and its Bank Account.
#:
#: Employee holds a Contact chosen from its own User's, and one Bank Account —
#: this app owns both fields. Supplier's equivalents belong to
#: seal_imprest_management and keep their older names; they are read here, not
#: owned, and a bench without that app falls through to ERPNext's own
#: `default_bank_account` (see `_bank_rail`). `_value` tolerates either being
#: absent, so this works whatever combination of apps is installed.
_SOURCES = {
    "Employee": {"contact": "custom_contact", "bank_account": "custom_salary_bank_account"},
    "Supplier": {"contact": "custom_mpesa_contact", "bank_account": "custom_bank_account"},
}


@frappe.whitelist()
def get_payee_payment_methods(party_type: str, party: str) -> dict:
    """Return every rail this payee can be paid on.

    ``{"mobile": {...} | None, "bank": {...} | None, "missing": [...],
       "party": ..., "party_type": ...}``

    Each rail carries the same three values the payment file and the M-Pesa
    gateway both need — ``account_name``, ``account_no``, ``provider`` — plus the
    record they came from, so a caller that needs more (branch code, SWIFT) can
    fetch it without this module growing a field per rail.

    ``account_no`` is the mobile number for the mobile rail and the bank account
    number for the bank rail; ``provider`` is the mobile operator or the bank.
    """
    if party_type not in _SOURCES:
        frappe.throw(
            _("Unsupported payee type: {0}. Must be Employee or Supplier.").format(party_type)
        )
    if not (party and frappe.db.exists(party_type, party)):
        frappe.throw(_("{0} {1} not found").format(_(party_type), party))

    mobile = _mobile_rail(party_type, party)
    bank = _bank_rail(party_type, party)

    missing = []
    if not mobile:
        missing.append(_("Mobile number"))
    if not bank:
        missing.append(_("Bank account"))

    return {
        "party_type": party_type,
        "party": party,
        MOBILE: mobile,
        BANK: bank,
        # Empty only when the payee can be paid both ways. A caller wanting one
        # specific rail should test that rail, not this list.
        "missing": missing,
    }


def can_pay_by(party_type: str, party: str, rail: str) -> bool:
    """Whether one specific rail is available. Convenience over the dict above."""
    return bool(get_payee_payment_methods(party_type, party).get(rail))


# ── rails ────────────────────────────────────────────────────────────────────

def _mobile_rail(party_type: str, party: str) -> dict | None:
    """Mobile money details, from the payee's Contact.

    The number is read from the Contact rather than copied onto the payee, so
    there is one place to change it. `Employee.cell_number` mirrors it by
    `fetch_from` for the benefit of code that reads the stock field.
    """
    contact_field = _SOURCES[party_type]["contact"]
    contact = _value(party_type, party, contact_field)
    if not contact:
        return None

    row = frappe.db.get_value(
        "Contact", contact,
        ["name", "full_name", "mobile_no", "phone", "custom_mno"],
        as_dict=True,
    )
    if not row:
        return None

    number = row.get("mobile_no") or row.get("phone")
    if not number:
        # A Contact with no primary number cannot receive money. Frappe blanks
        # `mobile_no` whenever no child row carries `is_primary_mobile_no`, so
        # this is a normal state, not a broken one.
        return None

    return {
        "account_name": row.get("full_name") or _party_name(party_type, party),
        "account_no": number,
        "provider": row.get("custom_mno") or _operator(number),
        "source_doctype": "Contact",
        "source_name": row["name"],
    }


def _bank_rail(party_type: str, party: str) -> dict | None:
    """Bank details, from the payee's Bank Account record.

    Falls back to ERPNext's own party lookup, which is what every payment rail
    ultimately resolves against — so a Bank Account created outside our form is
    still found, provided it is flagged `is_default`.
    """
    from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

    account = _value(party_type, party, _SOURCES[party_type]["bank_account"]) \
        or _value(party_type, party, "default_bank_account")
    if not account:
        account = get_party_bank_account(party_type, party)
    if not account:
        return None

    row = frappe.db.get_value(
        "Bank Account", account,
        ["name", "account_name", "bank_account_no", "bank", "branch_code", "iban", "disabled"],
        as_dict=True,
    )
    if not row or row.get("disabled") or not row.get("bank_account_no"):
        return None

    return {
        "account_name": row.get("account_name") or _party_name(party_type, party),
        "account_no": row["bank_account_no"],
        "provider": row.get("bank"),
        "branch_code": row.get("branch_code"),
        "iban": row.get("iban"),
        "source_doctype": "Bank Account",
        "source_name": row["name"],
    }


# ── helpers ──────────────────────────────────────────────────────────────────

def _value(doctype: str, name: str, fieldname: str):
    """Read a field that may not exist — party doctypes differ by app install."""
    if not fieldname or not frappe.get_meta(doctype).has_field(fieldname):
        return None
    return frappe.db.get_value(doctype, name, fieldname)


def _party_name(party_type: str, party: str) -> str:
    title = frappe.get_meta(party_type).get_title_field()
    return frappe.db.get_value(party_type, party, title) or party


def _operator(number: str) -> str:
    """Mobile operator from the number itself.

    Only a fallback: `Contact.custom_mno` is the stored answer. seal_common owns
    the numbering plan, so it is asked rather than duplicated here, and a bench
    without seal_common simply reports no operator instead of failing.
    """
    try:
        from seal_common.seal_common.mno import get_mno_from_no
    except ImportError:
        return ""
    try:
        operator = get_mno_from_no(number)
    except Exception:
        return ""
    return "" if operator == "UNKNOWN" else (operator or "")
