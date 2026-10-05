# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, time_diff_in_hours

def on_submit(doc, method=None):
    # A rejected application is still submitted: the cover it asked for is off.
    if doc.status == "Rejected":
        withdraw_task_assignments(doc)
    elif doc.status == "Approved":
        start_cover_if_due(doc)
    from seal_hrms.seal_hrms import acting

    acting.record_acting_approval(doc, doc.leave_approver, "leave_approval")


def on_update(doc, method=None):
    """Keep an unsubmitted handover's dates in step; reach an absent approver's stand-in."""
    if doc.docstatus != 0:
        return
    from seal_hrms.seal_hrms import acting

    acting.share_new_document(doc, doc.leave_approver, "leave_approval")
    from seal_hrms.seal_hrms.handover import return_date_for

    for name in frappe.get_all(
        "Task Assignment",
        filters={"leave_application": doc.name, "docstatus": ["<", 2], "status": ["not in", ["Active", "Handed Back"]]},
        pluck="name",
    ):
        frappe.db.set_value("Task Assignment", name, {
            "leave_from": doc.from_date,
            "leave_to": doc.to_date,
            "leave_days": doc.total_leave_days,
            "return_date": return_date_for(doc.employee, doc.to_date),
        }, update_modified=False)


def start_cover_if_due(doc):
    """Approval can be the last thing missing, when the leave has already begun."""
    from seal_hrms.seal_hrms import handover

    for name in frappe.get_all(
        "Task Assignment", filters={"leave_application": doc.name, "docstatus": 1, "status": "Accepted"}, pluck="name"
    ):
        handover.maybe_activate(name)


def on_cancel(doc, method=None):
    # Runs before Frappe's linked-document check, so cancelling the handovers
    # here is also what lets the leave itself be cancelled.
    withdraw_task_assignments(doc)


def validate(doc, method=None):
    check_cover_before_submission(doc)
    check_cover_before_approval(doc)
    if _is_being_approved(doc):
        from seal_hrms.seal_hrms import acting

        acting.refuse_self_approval(doc, doc.employee, doc.leave_approver, "leave_approval")
    _check_application_timing(doc)


def before_workflow_action(doc, method=None, action=None, **kwargs):
    """Intercept workflow actions: block applying/forwarding if mandatory handover is missing."""
    check_cover_before_submission(doc, is_workflow_action=True)


def _get_workflow_initial_state(doctype: str) -> str | None:
    """Get the initial state name of the active workflow for this doctype dynamically."""
    try:
        from frappe.model.workflow import get_workflow_name
        wf_name = get_workflow_name(doctype)
        if not wf_name:
            return None
        wf = frappe.get_cached_doc("Workflow", wf_name)
        if wf and wf.is_active and wf.states:
            return wf.states[0].state
    except Exception:
        pass
    return None


def _is_being_submitted_or_applied(doc, is_workflow_action=False) -> bool:
    if is_workflow_action:
        # In a workflow, intercept the action if the doc is at the initial state moving forward
        init_state = _get_workflow_initial_state(doc.doctype)
        curr_state = doc.get("workflow_state")
        if not init_state or not curr_state or curr_state == init_state:
            return True
        return False

    if doc.docstatus == 1 and (doc.is_new() or getattr(doc, "_action", None) == "submit"):
        return True
    before = doc.get_doc_before_save()
    if before and before.docstatus == 0 and doc.docstatus == 1:
        return True

    # If workflow is active and document is transitioning away from the initial workflow state
    init_state = _get_workflow_initial_state(doc.doctype)
    workflow_state = doc.get("workflow_state")
    if init_state and workflow_state and before:
        before_state = before.get("workflow_state")
        if before_state == init_state and workflow_state != init_state:
            return True

    return False


def check_cover_before_submission(doc, is_workflow_action=False):
    """Enforce handover policy when staff submit or apply for leave."""
    if not _is_being_submitted_or_applied(doc, is_workflow_action):
        return

    from seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy import (
        is_required_on_submission,
        is_acceptance_required_before_submission,
        applies_to,
        policy_for,
    )

    policy = policy_for(doc.company)
    if not applies_to(policy, doc.leave_type, doc.total_leave_days):
        return

    if not is_required_on_submission(policy):
        return

    if not doc.name:
        frappe.throw(
            _("Please save this Leave Application as draft first, then click 'Prepare Handover' to name your stand-in before submitting."),
            title=_("Handover Required"),
        )

    # Check for existing Task Assignment for this leave application
    assignments = frappe.get_all(
        "Task Assignment",
        filters={"leave_application": doc.name, "docstatus": ["<", 2]},
        fields=["name", "status", "task_assignee", "docstatus"],
    )
    if not assignments or not assignments[0].task_assignee:
        frappe.throw(
            _("A handover is mandatory for this leave application. Please click 'Prepare Handover' on the form and choose your stand-in before submitting."),
            title=_("Handover Required"),
        )

    if is_acceptance_required_before_submission(policy):
        accepted = any(a.status in ("Accepted", "Active") for a in assignments)
        if not accepted:
            current_status = assignments[0].status or _("Draft")
            frappe.throw(
                _("Your stand-in must accept the handover before you can submit this leave application. Current handover status is '{0}'.").format(
                    _(current_status)
                ),
                title=_("Stand-in Acceptance Required"),
            )


def _is_being_approved(doc) -> bool:
    if doc.status != "Approved":
        return False
    if doc.is_new() or getattr(doc, "_action", None) == "submit":
        return True
    before = doc.get_doc_before_save()
    return bool(before) and before.status != "Approved"


def check_cover_before_approval(doc):
    """Apply the company's handover policy at the moment leave is approved.

    In validate, not on_submit: the approval has to be refused before it is
    written, and a status set to Approved without submitting must be caught too.
    """
    if not _is_being_approved(doc):
        return
    from seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy import (
        WARN, is_required_on_approval, applies_to, policy_for,
    )

    policy = policy_for(doc.company)
    if not applies_to(policy, doc.leave_type, doc.total_leave_days):
        return
    agreed = frappe.db.exists(
        "Task Assignment",
        {"leave_application": doc.name, "docstatus": 1, "status": ["in", ["Accepted", "Active"]]},
    )
    if agreed:
        return
    message = _(
        "Nobody has agreed to cover {0}'s work during this leave yet. "
        "Ask them to prepare a handover, and their stand-in to accept it."
    ).format(doc.employee_name or doc.employee)
    if is_required_on_approval(policy):
        frappe.throw(message, title=_("Cover Not Arranged"))
    elif policy.requirement == WARN:
        frappe.msgprint(message, title=_("Cover Not Arranged"), indicator="orange")


def _check_application_timing(doc):
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
