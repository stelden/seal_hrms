# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""
Put employee payout details onto the fields payment rails actually read.

An employee's details live on two records — a Contact for mobile money, a Bank
Account for bank transfers — but the rails downstream read stock ERPNext fields:

* mobile money reads `Employee.cell_number`;
* every bank rail resolves the beneficiary through ERPNext's
  `get_party_bank_account`, i.e. a `Bank Account` with `is_default = 1`.

`fetch_from` keeps `cell_number` in step with the Contact going forward. This
module handles what `fetch_from` cannot: records that already exist, Contacts
Frappe queued but never created, and Bank Accounts saved before `is_default` was
being set — which exist, show on the Employee, and are invisible to every payment
path.

Doing this here — in the app that owns Employee — is what lets the disbursement
and bank-integration apps stay ignorant of each other: they read stock fields and
never this module.

Everything is idempotent and additive. Existing values are never overwritten and
existing Bank Accounts are never edited, so a re-run is a no-op.
"""

import frappe
from frappe import _

from seal_common.seal_common.mno import (
    is_valid_kenya_mobile_no,
    normalize_kenya_mobile_no,
)


@frappe.whitelist()
def sync_employee_payout_details(employees=None, company=None):
    """Desk entry point — see :func:`sync_payout_details`."""
    frappe.only_for(("System Manager", "HR Manager", "Accounts Manager"))
    return sync_payout_details(employees=employees, company=company)


def sync_payout_details(employees=None, company=None, commit=False):
    """Align each employee's stock fields with the records they point at.

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
    report = {"considered": len(names), "phones_set": 0, "contacts_linked": 0,
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
        ["name", "employee_name", "company", "user_id", "cell_number",
         "custom_contact", "custom_salary_bank_account"],
        as_dict=True,
    )
    if not emp:
        report["skipped"].append({"employee": name, "reason": _("Employee not found.")})
        return

    mobile = _sync_mobile(emp, report)
    bank = _sync_bank(emp, report)

    if not (mobile or bank):
        report["skipped"].append({
            "employee": name,
            "reason": _("Cannot be paid — needs a Contact with a mobile number, or a bank account."),
        })


# ── mobile money ─────────────────────────────────────────────────────────────

def _sync_mobile(emp, report):
    """Link the User's Contact if missing, then mirror its number onto `cell_number`."""
    contact = emp.custom_contact or _adopt_user_contact(emp, report)
    if not contact:
        return False

    number = frappe.db.get_value("Contact", contact, "mobile_no") \
        or frappe.db.get_value("Contact", contact, "phone")
    if not number:
        return False

    if emp.cell_number and is_valid_kenya_mobile_no(emp.cell_number):
        return True  # already usable — never rewrite what payroll may rely on

    normalized = normalize_kenya_mobile_no(number)
    # Validate the normaliser's own output: it is lenient about input it cannot
    # actually resolve, and a wrong mobile number sends money to a stranger.
    if not (normalized and is_valid_kenya_mobile_no(normalized)):
        report["skipped"].append({
            "employee": emp.name,
            "reason": _("Mobile number {0} is not a valid Kenyan number.").format(number),
        })
        return False

    frappe.db.set_value("Employee", emp.name, "cell_number", normalized,
                        update_modified=False)
    report["phones_set"] += 1
    return True


def _adopt_user_contact(emp, report):
    """Find the Contact belonging to this employee's User, and link it.

    Frappe creates a Contact per User in a **background job**, so it may never
    have run; and because it adopts any Contact matching the user's email, one
    User can end up owning several. Where that is ambiguous the choice is left to
    a human rather than guessed — paying the wrong number is not recoverable.
    """
    if not emp.user_id:
        return None

    candidates = frappe.get_all(
        "Contact", filters={"user": emp.user_id}, pluck="name", order_by="creation asc"
    )
    if not candidates:
        return None
    if len(candidates) > 1:
        report["skipped"].append({
            "employee": emp.name,
            "reason": _("User {0} has {1} Contacts — pick the right one on the employee record.")
            .format(emp.user_id, len(candidates)),
        })
        return None

    frappe.db.set_value("Employee", emp.name, "custom_contact", candidates[0],
                        update_modified=False)
    report["contacts_linked"] += 1
    return candidates[0]


# ── bank rail ────────────────────────────────────────────────────────────────

def _sync_bank(emp, report):
    """Ensure the employee's Bank Account is one ERPNext can resolve."""
    if frappe.db.exists("Bank Account", {
        "party_type": "Employee", "party": emp.name, "is_default": 1, "disabled": 0,
    }):
        return True

    # An account exists but nothing can resolve it — the exact state
    # seal_hrms.api.create_bank_account used to leave records in.
    orphan = frappe.db.get_value("Bank Account", {
        "party_type": "Employee", "party": emp.name, "disabled": 0,
    }, "name")
    if not orphan:
        return False

    frappe.db.set_value("Bank Account", orphan, "is_default", 1, update_modified=False)
    if not emp.custom_salary_bank_account:
        frappe.db.set_value("Employee", emp.name, "custom_salary_bank_account", orphan,
                            update_modified=False)
    report["defaults_fixed"] += 1
    return True
