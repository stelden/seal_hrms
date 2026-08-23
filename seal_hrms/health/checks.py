# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Health checks for HR core.

This app is deliberately thin -- leave planning and imprest each own their own
scheduled work, and core ships none. What it does own is cover during leave,
and the failure that matters there is cover assigned to somebody who cannot
actually provide it: a colleague who has since left, or who turns out to be on
leave themselves for the same days.

Neither raises an error. The handover simply does not happen, and it is noticed
when somebody needs the work done.
"""

import frappe
from frappe import _

from seal_common.app_health import Category, Finding, Severity, State, health_check

ASSIGNMENT = "Task Assignment"


@health_check(label="Cover during leave", category=Category.DATA)
def cover_assigned_to_inactive_staff():
    """Work handed to somebody who has left.

    The assignment still reads as covered, so nobody looks for another pair of
    hands until the work is already late.
    """
    if not frappe.db.table_exists(ASSIGNMENT):
        return []
    total = frappe.db.count(ASSIGNMENT, {"docstatus": 1})
    if not total:
        return []
    rows = frappe.db.sql(
        """
        SELECT COUNT(*) FROM `tabTask Assignment` a
        INNER JOIN `tabEmployee` e ON e.name = a.task_assignee
        WHERE a.docstatus = 1 AND e.status != 'Active'
        """
    )
    count = rows[0][0] if rows else 0
    if not count:
        return []
    return Finding(
        severity=Severity.DEGRADED,
        title=_("Some work is covered by staff who have left"),
        detail=_(
            "The handover still reads as arranged, so nobody will look for "
            "someone else until the work is already late."
        ),
        count=count,
        total=total,
        state=State.MISCONFIGURED,
        link="/app/task-assignment",
    )


@health_check(label="Cover with nobody named", category=Category.DATA)
def cover_without_an_assignee():
    """A handover recorded against nobody."""
    if not frappe.db.table_exists(ASSIGNMENT):
        return []
    total = frappe.db.count(ASSIGNMENT, {"docstatus": 1})
    if not total:
        return []
    orphaned = frappe.db.count(ASSIGNMENT, {
        "docstatus": 1, "task_assignee": ("in", ["", None]),
    })
    if not orphaned:
        return []
    return Finding(
        severity=Severity.DEGRADED,
        title=_("Some handovers name nobody to do the work"),
        detail=_("The leave was approved but the work has not been passed to anyone."),
        count=orphaned,
        total=total,
        state=State.MISSING,
        link="/app/task-assignment",
    )


@health_check(label="Dependants on file", category=Category.CONFIGURATION)
def beneficiary_records_present():
    """Dependants matter when somebody has to claim on their behalf.

    Advisory: an organisation may genuinely not collect these. It is worth
    knowing which, rather than discovering it during a claim.
    """
    if not frappe.db.table_exists("Employee Dependent and Beneficiary"):
        return []
    active = frappe.db.count("Employee", {"status": "Active"})
    if not active:
        return []
    if frappe.db.count("Employee Dependent and Beneficiary"):
        return []
    return Finding(
        severity=Severity.ADVISORY,
        title=_("No dependants or beneficiaries are recorded for anyone"),
        detail=_(
            "If a claim has to be made on somebody's behalf, there is nobody "
            "on file to make it to."
        ),
        count=active,
        state=State.MISSING,
        link="/app/employee-dependent-and-beneficiary",
    )
