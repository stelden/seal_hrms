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
# Handovers still in play. A returned, cancelled or pre-1.3.0 (Legacy) handover
# names somebody who is no longer expected to do anything.
LIVE = ("Awaiting Acceptance", "Accepted", "Active")


@health_check(label="Cover during leave", category=Category.DATA)
def cover_assigned_to_inactive_staff():
    """Work handed to somebody who has left.

    The assignment still reads as covered, so nobody looks for another pair of
    hands until the work is already late.
    """
    if not frappe.db.table_exists(ASSIGNMENT):
        return []
    total = frappe.db.count(ASSIGNMENT, {"docstatus": 1, "status": ("in", LIVE)})
    if not total:
        return []
    rows = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT a.name) FROM `tabTask Assignment` a
        LEFT JOIN `tabTask Assignment ToDo` r
               ON r.parent = a.name AND r.parenttype = 'Task Assignment'
        INNER JOIN `tabEmployee` e ON e.name = IFNULL(NULLIF(r.task_assignee, ''), a.task_assignee)
        WHERE a.docstatus = 1 AND a.status IN %(live)s AND e.status != 'Active'
        """,
        {"live": LIVE},
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
    total = frappe.db.count(ASSIGNMENT, {"docstatus": 1, "status": ("in", LIVE)})
    if not total:
        return []
    orphaned = frappe.db.count(ASSIGNMENT, {
        "docstatus": 1, "status": ("in", LIVE), "task_assignee": ("is", "not set"),
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


@health_check(label="Work returned after leave", category=Category.DATA)
def work_left_with_stand_ins():
    """Work that stayed on a stand-in's list after the leave it covered ended.

    Two ways it happens: the daily return has not run (scheduler off, or a
    record it could not process), or it is left over from before 1.3.0 and the
    one-off return had to skip it — its owner has left, or someone has since
    moved it on. Either way the owner thinks the stand-in has it, and the
    stand-in thinks it was only temporary.
    """
    if not frappe.db.table_exists(ASSIGNMENT):
        return []
    today = frappe.utils.today()
    overdue = frappe.db.sql(
        """
        SELECT COUNT(*) FROM `tabTask Assignment`
        WHERE docstatus = 1 AND status = 'Active' AND leave_to < %s
        """,
        (today,),
    )[0][0]
    # The same rule the one-off return used, so the two never disagree. What
    # the return could move, it did; anything still here was skipped by it.
    from seal_hrms.seal_hrms.legacy_handover import find_stranded

    returnable, skipped = find_stranded()
    legacy = len(returnable) + len(skipped)
    if not (overdue or legacy):
        return []
    return Finding(
        severity=Severity.DEGRADED,
        title=_("Some work is still with stand-ins after the leave ended"),
        detail=_(
            "{0} handover(s) should have been returned by now, and {1} older task(s) "
            "could not be returned automatically. Open each and return the work, "
            "or reassign it deliberately."
        ).format(overdue, legacy),
        count=overdue + legacy,
        state=State.MISCONFIGURED,
        link="/app/task-assignment?status=Active",
    )


@health_check(label="Cover agreed before leave", category=Category.DATA)
def leave_started_without_agreed_cover():
    """Approved leave under way while its handover still waits for an answer, or was declined.

    Nothing moves until a stand-in agrees, so this work is sitting on the list
    of someone who is away. The approval policy exists to prevent it; this is
    where it shows when the policy is off or was bypassed.
    """
    if not frappe.db.table_exists(ASSIGNMENT):
        return []
    count = frappe.db.sql(
        """
        SELECT COUNT(*) FROM `tabTask Assignment` a
        INNER JOIN `tabLeave Application` la ON la.name = a.leave_application
        WHERE a.docstatus = 1 AND a.status IN ('Awaiting Acceptance', 'Declined')
          AND la.docstatus = 1 AND la.status = 'Approved'
          AND la.from_date <= %(today)s AND la.to_date >= %(today)s
        """,
        {"today": frappe.utils.today()},
    )[0][0]
    if not count:
        return []
    return Finding(
        severity=Severity.DEGRADED,
        title=_("Some staff are on leave with nobody agreed to cover their work"),
        detail=_(
            "Their handover is still waiting for an answer, or was declined, so the "
            "work has stayed on the list of someone who is away."
        ),
        count=count,
        state=State.MISSING,
        link="/app/task-assignment?status=Awaiting%20Acceptance",
    )


@health_check(label="Approvals while away", category=Category.DATA)
def approvals_with_nobody_to_give_them():
    """Someone approving in an absent colleague's place is now away themselves.

    Approval does not pass on down a chain (seal_hrms.acting), so their team's
    requests wait for two people who are both on leave.
    """
    if not frappe.db.table_exists("Task Assignment Authority"):
        return []
    count = frappe.db.sql(
        """
        SELECT COUNT(DISTINCT r.name) FROM `tabTask Assignment Authority` r
        INNER JOIN `tabTask Assignment` a ON a.name = r.parent AND r.parenttype = 'Task Assignment'
        INNER JOIN `tabLeave Application` la
                ON la.employee = IFNULL(NULLIF(r.task_assignee, ''), a.task_assignee)
               AND la.docstatus = 1 AND la.status = 'Approved'
               AND la.from_date <= %(today)s AND la.to_date >= %(today)s
        WHERE a.docstatus = 1 AND a.status = 'Active' AND r.acceptance = 'Accepted'
        """,
        {"today": frappe.utils.today()},
    )[0][0]
    if not count:
        return []
    return Finding(
        severity=Severity.DEGRADED,
        title=_("Some approvals are waiting on two people who are both away"),
        detail=_(
            "The person approving in a colleague's place has gone on leave too. "
            "Approval does not pass on again, so name someone else or ask HR to approve."
        ),
        count=count,
        state=State.MISSING,
        link="/app/task-assignment?status=Active",
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
