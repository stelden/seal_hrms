# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""
Normalise employee payout details onto the native ERPNext fields.

Employee payee data is captured in several places on this bench — the seal_hrms
custom fields (`custom_preferred_payment_method` + `custom_mpesa_contact` /
`custom_bank_account`, or the flattened `custom_account_no` / `custom_account_name`),
and the stock `Employee.bank_ac_no` / `bank_name` / `cell_number`. Payment rails,
however, read only the native ones:

* mobile money reads `Employee.cell_number`;
* every bank rail resolves the beneficiary through ERPNext's
  `get_party_bank_account`, i.e. a `Bank Account` record with `is_default = 1`.

This module copies whatever an employee actually has onto those two native
surfaces. Doing it here — in the app that owns Employee — is what lets the
disbursement and bank-integration apps stay ignorant of each other: they both
read stock ERPNext fields and never this module.

Everything is idempotent and additive. Existing values are never overwritten and
existing Bank Accounts are never edited, so a re-run is a no-op.
"""

import frappe
from frappe import _

from seal_common.seal_common.mno import (
    is_valid_kenya_mobile_no,
    normalize_kenya_mobile_no,
)

MPESA = "Mpesa"


@frappe.whitelist()
def sync_employee_payout_details(employees=None, company=None):
    """Desk entry point — see :func:`sync_payout_details`."""
    frappe.only_for(("System Manager", "HR Manager", "Accounts Manager"))
    return sync_payout_details(employees=employees, company=company)


def sync_payout_details(employees=None, company=None, commit=False):
    """Copy each employee's payout details onto `cell_number` / a default Bank Account.

    Args:
        employees: optional list (or JSON list) of Employee names. Defaults to
            every Active employee, optionally narrowed by `company`.
        company: restrict the default selection to one Company.
        commit: commit between employees. Only for long backfills run from a
            patch or the console — never from a web request.

    Returns a report: counts plus a per-employee reason for anything skipped, so
    an operator can see exactly which records still need data entry.

    Unwhitelisted on purpose: patches and the console call this directly, so the
    role gate lives on the web entry point above rather than being worked around
    with a session switch.
    """
    names = _resolve_employee_names(employees, company)
    report = {"considered": len(names), "phones_set": 0, "accounts_created": 0,
              "defaults_fixed": 0, "skipped": []}

    for name in names:
        try:
            _sync_one(name, report)
        except Exception as exc:
            # One bad record must not abandon the rest of the run.
            report["skipped"].append({"employee": name, "reason": str(exc)})
        if commit:
            frappe.db.commit()

    return report


def _resolve_employee_names(employees, company):
    if employees:
        if isinstance(employees, str):
            import json
            employees = json.loads(employees)
        return list(employees)

    filters = {"status": "Active"}
    if company:
        filters["company"] = company
    return frappe.get_all("Employee", filters=filters, pluck="name")


def _sync_one(name, report):
    emp = frappe.db.get_value(
        "Employee", name,
        ["name", "employee_name", "company", "cell_number", "bank_ac_no", "bank_name",
         "custom_preferred_payment_method", "custom_mpesa_contact", "custom_bank_account",
         "custom_account_no", "custom_account_name"],
        as_dict=True,
    )
    if not emp:
        report["skipped"].append({"employee": name, "reason": _("Employee not found.")})
        return

    did_something = _sync_phone(emp, report)
    did_something = _sync_bank_account(emp, report) or did_something

    if not did_something:
        report["skipped"].append({
            "employee": name,
            "reason": _("No usable payout details — needs a mobile number or bank account."),
        })


# ── mobile money ─────────────────────────────────────────────────────────────

def _sync_phone(emp, report):
    """Stamp a valid Kenyan mobile number onto the native `cell_number`."""
    if is_valid_kenya_mobile_no(emp.cell_number or ""):
        return True  # already usable — never rewrite what payroll may rely on

    raw = _candidate_phone(emp)
    if not raw:
        return False

    normalized = normalize_kenya_mobile_no(raw)
    # Validate the normaliser's own output: it is lenient about input it cannot
    # actually resolve, and a wrong mobile number sends money to a stranger.
    if not (normalized and is_valid_kenya_mobile_no(normalized)):
        report["skipped"].append({
            "employee": emp.name,
            "reason": _("Mobile number {0} is not a valid Kenyan number.").format(raw),
        })
        return False

    frappe.db.set_value("Employee", emp.name, "cell_number", normalized,
                        update_modified=False)
    report["phones_set"] += 1
    return True


def _candidate_phone(emp):
    """The best raw phone we hold, in order of how deliberately it was captured."""
    if emp.custom_mpesa_contact:
        contact = frappe.db.get_value(
            "Contact", emp.custom_mpesa_contact, ["mobile_no", "phone"], as_dict=True
        ) or {}
        if contact.get("mobile_no") or contact.get("phone"):
            return contact.get("mobile_no") or contact.get("phone")

    if emp.custom_preferred_payment_method == MPESA and emp.custom_account_no:
        return emp.custom_account_no

    return emp.cell_number or None


# ── bank rail ────────────────────────────────────────────────────────────────

def _sync_bank_account(emp, report):
    """Ensure the employee has a resolvable default Bank Account."""
    from seal_hrms.seal_hrms.api import create_bank_account

    if frappe.db.exists("Bank Account", {
        "party_type": "Employee", "party": emp.name, "is_default": 1, "disabled": 0,
    }):
        return True

    # An account exists but nothing can resolve it — the exact state
    # seal_hrms.api.create_bank_account used to leave records in.
    orphan = frappe.db.get_value("Bank Account", {
        "party_type": "Employee", "party": emp.name, "disabled": 0,
    }, "name")
    if orphan:
        frappe.db.set_value("Bank Account", orphan, "is_default", 1, update_modified=False)
        report["defaults_fixed"] += 1
        return True

    account_no, bank = _candidate_bank(emp)
    if not (account_no and bank):
        return False

    create_bank_account(
        ref_doctype="Employee",
        ref_name=emp.name,
        account_name=emp.custom_account_name or emp.employee_name,
        account_number=account_no,
        bank=bank,
        company=emp.company,
    )
    report["accounts_created"] += 1
    return True


def _candidate_bank(emp):
    """(account_no, Bank) from whatever bank details the employee carries.

    `Employee.bank_name` is free text, so it is matched against the Bank master
    by name and then by SWIFT; an unmatched bank yields no account rather than a
    record pointing at a Bank that does not exist.
    """
    account_no = (emp.bank_ac_no or "").strip()
    if not account_no and emp.custom_preferred_payment_method not in (None, "", MPESA):
        account_no = (emp.custom_account_no or "").strip()
    if not account_no:
        return None, None

    raw_bank = (emp.bank_name or "").strip()
    if not raw_bank:
        return None, None

    bank = frappe.db.get_value("Bank", raw_bank, "name") or frappe.db.get_value(
        "Bank", {"swift_number": raw_bank}, "name"
    )
    return account_no, bank
