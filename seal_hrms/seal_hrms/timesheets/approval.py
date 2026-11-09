# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Timesheet approval: staff send their timesheet to their approver, who approves or returns it.

Where a company's Working Time Policy says timesheets need approval, a
timesheet for an employee is submitted only by approving it: the person (or HR)
sends it, and their approver, whoever approves in that approver's place during
their leave, or HR approves it (submits) or returns it with a reason. Frappe HR
lets anyone with Employee Self Service submit their own timesheet
(WORKING_TIME_DESIGN.md F8); `before_submit` here closes that, list bulk submit
included. Where approval is off, nothing here does anything and timesheets
behave as stock.

The approver is the leave approver, or the line manager ("Reports To") where the
company says so, falling back to the leave approver when the line manager has
no login (decision D8, recommended option, `[unsupervised — review]`). The
approver reaches the timesheet through a share, as Frappe HR's leave approvers
do: approvers hold no role on Timesheet.

State lives in `custom_approval_state`, moved only by these endpoints (an
in-process flag, as for time off claims, SEAL_DEV_RULES §3.2). Every endpoint
checks its caller first (§2.15).
"""

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import now_datetime
from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

from seal_hrms.seal_hrms import acting
from seal_hrms.seal_hrms.handover import user_for_employee
from seal_hrms.seal_hrms.toil import access
from seal_hrms.seal_hrms.working_time.policy import policy_for

TIMESHEET = "Timesheet"
AUTHORITY = "timesheet_approval"
TRANSITION = "seal_timesheet_transition"
NOT_SENT, WAITING, RETURNED, APPROVED = "Not Sent", "Waiting for Approval", "Returned", "Approved"
LINE_MANAGER = "Line manager"


@contextmanager
def transition(name: str):
	previous = frappe.flags.get(TRANSITION)
	frappe.flags[TRANSITION] = name
	try:
		yield
	finally:
		frappe.flags[TRANSITION] = previous


def in_transition(doc) -> bool:
	return bool(doc.name) and frappe.flags.get(TRANSITION) == doc.name


def applies(doc) -> bool:
	"""Approval is on for this timesheet: it is a person's, at a company that asks for it."""
	return bool(doc.get("employee") and doc.get("company") and policy_for(doc.company).timesheet_approval)


def approver_for(employee: str, company: str) -> str | None:
	"""The person who approves this employee's timesheets, by the company's rule."""
	if policy_for(company).timesheet_approver == LINE_MANAGER:
		manager = frappe.db.get_value("Employee", employee, "reports_to")
		user = frappe.db.get_value("Employee", manager, "user_id") if manager else None
		if user:
			return user
	return get_employee_leave_approver(employee) or None


def can_decide(doc, user: str | None = None) -> bool:
	"""The approver, whoever approves in their place, or HR. Never the person themselves."""
	user = user or frappe.session.user
	if user_for_employee(doc.employee) == user:
		return False
	approver = doc.get("custom_approver")
	if access.is_backoffice(user) or (approver and approver == user):
		return True
	return bool(approver) and acting.acting_stand_in(approver, AUTHORITY) == user


def require_decider(doc) -> None:
	if user_for_employee(doc.employee) == frappe.session.user:
		frappe.throw(_("This is your own timesheet. Someone else must approve it."), frappe.PermissionError)
	if not can_decide(doc):
		frappe.throw(
			_("Only {0}, or whoever approves in their place, can approve this timesheet.").format(
				doc.get("custom_approver_name") or doc.get("custom_approver") or _("the approver")
			),
			frappe.PermissionError,
		)


# ---------------------------------------------------------------- doc events


def validate(doc, method=None) -> None:
	"""Timesheet validate: the approval state moves only by sending or deciding; no edits while waiting."""
	if not applies(doc):
		return
	if in_transition(doc):
		return
	before = doc.get_doc_before_save()
	previous = (before.get("custom_approval_state") if before else None) or NOT_SENT
	if before is None and not doc.get("custom_approval_state"):
		doc.custom_approval_state = NOT_SENT
	if (doc.get("custom_approval_state") or NOT_SENT) != previous:
		frappe.throw(
			_("A timesheet's approval changes only by sending it or deciding it."), frappe.PermissionError
		)
	if previous == WAITING:
		frappe.throw(
			_("This timesheet is with {0}. Ask them to return it before changing it.").format(
				doc.get("custom_approver_name") or doc.get("custom_approver")
			),
			title=_("Waiting for Approval"),
		)
	if previous in (NOT_SENT, RETURNED):
		doc.custom_approver = approver_for(doc.employee, doc.company)


def before_submit(doc, method=None) -> None:
	"""Timesheet before_submit: where approval is on, only approving submits a person's timesheet."""
	if not applies(doc):
		return
	if not in_transition(doc) or doc.get("custom_approval_state") != APPROVED:
		frappe.throw(
			_("Send this timesheet for approval: {0} approves it, which submits it.").format(
				doc.get("custom_approver_name") or doc.get("custom_approver") or _("the approver")
			),
			title=_("Needs Approval"),
		)
	require_decider(doc)
	acting.refuse_self_approval(doc, doc.employee, doc.custom_approver, AUTHORITY)


def on_submit(doc, method=None) -> None:
	if applies(doc):
		acting.record_acting_approval(doc, doc.get("custom_approver"), AUTHORITY)


def before_cancel(doc, method=None) -> None:
	"""Timesheet before_cancel: staff do not cancel a timesheet their approver approved."""
	if applies(doc) and user_for_employee(doc.employee) == frappe.session.user:
		if not access.is_backoffice(frappe.session.user):
			frappe.throw(
				_("Your approver approved this timesheet. Ask them or HR to cancel it."),
				frappe.PermissionError,
			)


def on_update(doc, method=None) -> None:
	if applies(doc) and doc.get("custom_approval_state") == WAITING:
		acting.share_new_document(doc, doc.get("custom_approver"), AUTHORITY)


def onload(doc, method=None) -> None:
	"""Timesheet onload: tell the form where approval is and what this viewer may do."""
	if doc.is_new() or not applies(doc):
		return
	from seal_hrms.seal_hrms.timesheets import stage

	user = frappe.session.user
	doc.set_onload("approval_on", True)
	doc.set_onload("can_send", access.can_send(doc, user))
	doc.set_onload("can_decide", can_decide(doc, user))
	doc.set_onload("where_it_is", stage.where_it_is(doc, user))


# ---------------------------------------------------------------- endpoints


def _load(name: str):
	doc = frappe.get_doc(TIMESHEET, name)
	doc.check_permission("read")
	if not applies(doc):
		frappe.throw(_("Timesheets at {0} do not need approval.").format(doc.company or _("this company")))
	return doc


def _share(doc, user: str | None) -> None:
	if not user or frappe.db.exists(
		"DocShare", {"share_doctype": TIMESHEET, "share_name": doc.name, "user": user}
	):
		return
	frappe.share.add_docshare(
		TIMESHEET, doc.name, user, read=1, write=1, submit=1, flags={"ignore_share_permission": True}
	)


@frappe.whitelist(methods=["POST"])
def send_for_approval(name: str) -> str:
	"""The person (or HR) sends a timesheet to its approver."""
	doc = _load(name)
	access.require_self_or_hr(doc.employee)
	if doc.docstatus != 0 or (doc.get("custom_approval_state") or NOT_SENT) not in (NOT_SENT, RETURNED):
		frappe.throw(_("Only a timesheet not yet sent, or returned, can be sent."))
	doc.custom_approver = approver_for(doc.employee, doc.company)
	if not doc.custom_approver:
		frappe.throw(
			_("Nobody approves {0}'s timesheets. Ask HR to set a leave approver or a line manager.").format(
				doc.employee_name
			),
			title=_("No Approver"),
		)
	from seal_hrms.seal_hrms.timesheets import effort

	effort.check_before_sending(doc)
	doc.custom_approval_state = WAITING
	doc.custom_sent_on = now_datetime()
	doc.custom_return_reason = None
	with transition(doc.name):
		doc.save()
	_share(doc, doc.custom_approver)
	from seal_hrms.seal_hrms.timesheets import notifications

	notifications.sent(doc)
	return doc.custom_approval_state


@frappe.whitelist(methods=["POST"])
def approve(name: str) -> str:
	"""The approver approves the timesheet, which submits it."""
	doc = _load(name)
	require_decider(doc)
	if doc.docstatus != 0 or doc.get("custom_approval_state") != WAITING:
		frappe.throw(_("This timesheet is not waiting for approval."))
	doc.custom_approval_state = APPROVED
	doc.custom_approved_by = frappe.session.user
	with transition(doc.name):
		doc.submit()
	from seal_hrms.seal_hrms.timesheets import notifications

	notifications.decided(doc, "approved")
	return doc.custom_approval_state


@frappe.whitelist(methods=["POST"])
def return_timesheet(name: str, reason: str | None = None) -> str:
	"""The approver sends the timesheet back with what to change."""
	doc = _load(name)
	require_decider(doc)
	if doc.docstatus != 0 or doc.get("custom_approval_state") != WAITING:
		frappe.throw(_("This timesheet is not waiting for approval."))
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("Say what needs changing: the person reads this to put it right."))
	doc.custom_approval_state = RETURNED
	doc.custom_return_reason = reason
	doc.custom_approved_by = frappe.session.user
	with transition(doc.name):
		doc.save()
	from seal_hrms.seal_hrms.timesheets import notifications

	notifications.decided(doc, "returned")
	return doc.custom_approval_state


# ---------------------------------------------------------------- handover kind


def holds_timesheet_approval(user: str) -> bool:
	"""Approves timesheets at some company that asks for approval: as a leave approver or a line manager."""
	from seal_hrms.seal_hrms.working_time.policy import POLICY

	if not frappe.db.table_exists(POLICY):
		return False
	companies = frappe.get_all(POLICY, filters={"timesheet_approval": 1}, pluck="company")
	if not companies:
		return False
	if frappe.db.exists(
		"Employee", {"leave_approver": user, "status": "Active", "company": ["in", companies]}
	):
		return True
	me = frappe.db.get_value("Employee", {"user_id": user}, "name")
	return bool(
		me
		and frappe.db.exists("Employee", {"reports_to": me, "status": "Active", "company": ["in", companies]})
	)


def pending_timesheet_approvals(user: str) -> list[tuple[str, str]]:
	return [
		(TIMESHEET, name)
		for name in frappe.get_all(
			TIMESHEET,
			filters={"custom_approver": user, "docstatus": 0, "custom_approval_state": WAITING},
			pluck="name",
		)
	]
