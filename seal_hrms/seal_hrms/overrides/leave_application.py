# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, time_diff_in_hours

def on_submit(doc, method=None):
    # A rejected application is still submitted: the cover it asked for is off.
    if doc.status == "Rejected":
        withdraw_task_assignments(doc)


def on_cancel(doc, method=None):
    # Runs before Frappe's linked-document check, so cancelling the handovers
    # here is also what lets the leave itself be cancelled.
    withdraw_task_assignments(doc)


def validate(doc, method=None):
    # These are application-time (creation) rules only. Guarding on is_new()
    # prevents them from re-firing on every later save (approval, cancellation,
    # edits of historical leave), which would otherwise block those updates
    # because the original posting_date is now in the past.
    if not doc.is_new():
        return

    if getdate(doc.posting_date) < getdate(today()):
        frappe.throw(_("Posting date cannot be before today."))

    min_application_days = frappe.get_value(
        "Leave Type", doc.leave_type, "custom_minimum_leave_application_days"
    )

    if min_application_days:
        if time_diff_in_hours(doc.from_date, doc.posting_date) < (min_application_days * 24):
            frappe.throw(_(f"You cannot apply for <b>{doc.leave_type}</b> less than <b>{min_application_days}</b> days before the start date."))

def withdraw_task_assignments(doc):
    """Call off the handovers for leave that will not happen.

    Cancelling a Task Assignment gives back anything already handed over (see
    `TaskAssignment.on_cancel`). Drafts are left for their owner to delete: they
    moved nothing, and may be reused for replacement leave.
    """
    for name in frappe.get_all(
        "Task Assignment",
        filters={"leave_application": doc.name, "docstatus": 1},
        pluck="name",
    ):
        assignment = frappe.get_doc("Task Assignment", name)
        assignment.flags.ignore_permissions = True
        assignment.cancel()
