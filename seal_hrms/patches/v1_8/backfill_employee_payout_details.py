# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Put existing employees' payout details onto the native ERPNext fields.

Payment rails read `Employee.cell_number` for mobile money and a default
`Bank Account` for every bank rail, but employee payee data on these sites lives
in the seal_hrms custom fields (`custom_mpesa_contact`, `custom_bank_account`,
`custom_account_no`) or in the stock free-text `bank_ac_no` / `bank_name`. The
result is employees who look fully configured yet cannot be paid by any rail.

This backfills what `payout_details.sync_employee_payout_details` would do for a
new record. It also repairs Bank Accounts created before
`api.create_bank_account` started setting `is_default` — those exist but
`get_party_bank_account` cannot resolve them, so they were invisible to every
payment path.

Idempotent and additive: existing `cell_number` values and existing Bank Accounts
are never overwritten, so a re-run changes nothing. Counts print to the deploy
log; per-employee gaps are reported rather than thrown, because a half-configured
employee is a data-entry task, not a migration failure.
"""

import frappe


def execute():
    from seal_hrms.seal_hrms.payout_details import sync_payout_details

    if not frappe.db.count("Employee", {"status": "Active"}):
        print("[seal_hrms] backfill_employee_payout_details: no active employees — no-op")
        return

    report = sync_payout_details(commit=True)

    print(
        "[seal_hrms] backfill_employee_payout_details: "
        f"considered={report['considered']} phones_set={report['phones_set']} "
        f"accounts_created={report['accounts_created']} "
        f"defaults_fixed={report['defaults_fixed']} skipped={len(report['skipped'])}"
    )

    if report["skipped"]:
        frappe.log_error(
            title="[seal_hrms] Employees still without payout details",
            message=frappe.as_json(report["skipped"]),
        )

    frappe.db.commit()
