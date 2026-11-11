# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""HR notices on staff phones (My Desk phone app, phase P6; PUSH.md §1 and §4).

Two answers seal_hrms gives about a Notification Log, through hooks only (§3.15):

* :func:`kind_of` (``push_kind_providers``): which kind of notice it is, for
  Settings → Notifications on the phone, where a person turns kinds on and off.
  ``"hr"`` for notices about their own HR records and about HR work given to them
  (a handover to answer, a payout change decided). ``None`` for anything waiting
  for **their decision**: that is seal_desk's "approvals" kind, which a manager
  keeps on even when they silence HR. ``None`` too for records that are not HR's.
* :func:`message_for` (``push_message_providers``, seal_common's PWA-22 hook):
  what of the notice may show on a locked phone. Pay, payout details and advances
  go subject-only; leave of a medical kind gets a subject that does not name the
  leave type, and no summary.

Neither imports seal_common or seal_desk: they are called by those apps, with a
Notification Log, on sites where they are installed. Both fail quiet (a broken
classifier must not stop a notice), except that :func:`message_for` lets an error
reach seal_common, which then sends subject-only (it fails closed).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import formatdate

#: The kind seal_hrms adds to the phone's notification settings.
HR = "hr"

LEAVE, EXPENSE = "Leave Application", "Expense Claim"
CLAIM, TIMESHEET = "Time Off in Lieu Claim", "Timesheet"
ADVANCE, PAYSLIP = "Employee Advance", "Salary Slip"
PAYOUT, HANDOVER = "Payout Change Request", "Task Assignment"
SHIFT, ATTENDANCE = "Shift Request", "Attendance Request"
TRAVEL = "Travel Request"

#: Records whose notices are HR's. The section claims the same types (hooks.py
#: `seal_desk_app_sections`), so tapping one opens it in Self Service.
HR_DOCTYPES = frozenset({LEAVE, EXPENSE, CLAIM, TIMESHEET, ADVANCE, PAYSLIP, PAYOUT, HANDOVER, SHIFT, ATTENDANCE, TRAVEL})

#: Notices about these show only their subject on a locked phone: they are about pay.
SUBJECT_ONLY = frozenset({PAYSLIP, PAYOUT, ADVANCE})

#: Words in a leave type's name that make it about someone's health (Data Protection Act 2019, s.2:
#: health data is sensitive). Matched case-insensitively, as whole words or prefixes.
MEDICAL_WORDS = ("sick", "medical", "hospital", "illness", "health", "maternity", "paternity", "convalescen")


# ---------------------------------------------------------------- the kind


def kind_of(notification_log) -> str | None:
	"""``"hr"`` for a notice about an HR record that is not waiting for the recipient's decision, else None.

	Contract (seal_common/seal_desk P6): ``push_kind_providers = ["seal_hrms.my_desk.push.kind_of"]``,
	called with the Notification Log document. Never raises.
	"""
	try:
		doctype = notification_log.get("document_type")
		name = notification_log.get("document_name")
		user = notification_log.get("for_user")
		if doctype not in HR_DOCTYPES or not name or not user:
			return None
		if not frappe.db.exists(doctype, name):
			return HR  # deleted since: an HR notice all the same, and nothing to decide
		return None if waiting_for(user, doctype, name) else HR
	except Exception:
		frappe.log_error(
			title="Self Service: could not tell a notice's kind",
			reference_doctype="Notification Log",
			reference_name=notification_log.get("name"),
		)
		return None


def waiting_for(user: str, doctype: str, name: str) -> bool:
	"""The record is waiting for ``user``'s decision now, by the same rules as the Approvals inbox.

	``my_desk.approvals`` lists the person's own leave, claims and timesheets never; the
	named approver's, and those held for someone on leave, always. A site Workflow on
	leave or expense claims makes the workflow's steps the approval (seal_desk lists those):
	then a draft that is not the recipient's own counts as waiting for them.
	"""
	from seal_hrms.my_desk import approvals
	from seal_hrms.seal_hrms.handover import user_for_employee

	if doctype == LEAVE:
		doc = frappe.db.get_value(LEAVE, name, ["employee", "leave_approver", "status", "docstatus"], as_dict=True)
		if doc.docstatus != 0 or doc.status != "Open" or user_for_employee(doc.employee) == user:
			return False
		return approvals._has_workflow(LEAVE) or doc.leave_approver in approvals.approvers_for(user, "leave_approval")

	if doctype == EXPENSE:
		doc = frappe.db.get_value(EXPENSE, name, ["employee", "expense_approver", "approval_status", "docstatus"], as_dict=True)
		if doc.docstatus != 0 or doc.approval_status != "Draft" or user_for_employee(doc.employee) == user:
			return False
		return approvals._has_workflow(EXPENSE) or doc.expense_approver in approvals.approvers_for(user, "expense_approval")

	if doctype == CLAIM:
		from seal_hrms.seal_hrms.toil import access, workflow

		doc = frappe.db.get_value(CLAIM, name, ["employee", "approver", "status", "docstatus"], as_dict=True)
		if doc.docstatus != 0 or doc.status not in workflow.WAITING_STATES or user_for_employee(doc.employee) == user:
			return False
		return doc.approver in approvals.approvers_for(user, access.AUTHORITY)

	if doctype == TIMESHEET:
		from seal_hrms.seal_hrms.timesheets import approval

		if not frappe.get_meta(TIMESHEET).has_field("custom_approval_state"):
			return False
		doc = frappe.db.get_value(TIMESHEET, name, ["employee", "custom_approver", "custom_approval_state", "docstatus"], as_dict=True)
		if doc.docstatus != 0 or doc.custom_approval_state != approval.WAITING or user_for_employee(doc.employee) == user:
			return False
		return doc.custom_approver in approvals.approvers_for(user, approval.AUTHORITY)

	if doctype == PAYOUT:
		from seal_hrms.seal_hrms import payout_change

		doc = frappe.get_doc(PAYOUT, name)
		return doc.status == payout_change.WAITING and payout_change.can_decide(doc, user)

	if doctype == SHIFT:
		doc = frappe.db.get_value(SHIFT, name, ["employee", "approver", "status", "docstatus"], as_dict=True)
		return doc.docstatus == 0 and doc.status == "Draft" and doc.approver == user and user_for_employee(doc.employee) != user

	if doctype == TRAVEL:
		from seal_hrms.seal_hrms import travel

		doc = frappe.get_doc(TRAVEL, name)
		# Waiting at the workflow's approval step for this person: their direct report's, or any for HR.
		if doc.docstatus != 0 or doc.get(travel.STATE_FIELD) != travel.WAITING or travel.user_of(doc.employee) == user:
			return False
		return travel.manager_user_of(doc.employee) == user or not travel.is_narrowed(user)

	# Payslips, advances, attendance requests and handovers ask nothing of the recipient that the
	# Approvals inbox carries (a handover is answered on Self Service's Cover screen).
	return False


# ---------------------------------------------------------------- what shows on a locked phone


def message_for(notification_log) -> dict | None:
	"""A safe subject or summary for HR notices about pay or health; None for everything else.

	Contract: seal_common ``push_message_providers`` (``messaging/push.py`` ``message_for_log``):
	``{"subject"?, "summary"?, "private"?}``; ``private: True`` sends the subject alone.
	"""
	doctype = notification_log.get("document_type")
	name = notification_log.get("document_name")
	if doctype not in HR_DOCTYPES or not name:
		return None
	if doctype == PAYSLIP:
		return {"subject": _payslip_subject(name, notification_log.get("for_user")), "private": True}
	if doctype in SUBJECT_ONLY:
		return {"private": True}
	if doctype == LEAVE:
		leave_type = frappe.db.get_value(LEAVE, name, "leave_type")
		if leave_type and is_medical(leave_type):
			return {"subject": _leave_subject(name, notification_log.get("for_user")), "private": True}
	return None


def is_medical(leave_type: str) -> bool:
	"""The leave type's name says it is about health (:data:`MEDICAL_WORDS`)."""
	words = frappe.scrub(leave_type).split("_")
	return any(word.startswith(stem) for word in words for stem in MEDICAL_WORDS)


def _payslip_subject(name: str, user: str | None) -> str:
	""""Your payslip for 1 Nov to 30 Nov" (no amounts; a site's own Notification may put net pay in its subject)."""
	from seal_hrms.seal_hrms.handover import user_for_employee

	slip = frappe.db.get_value(PAYSLIP, name, ["employee", "employee_name", "start_date", "end_date"], as_dict=True)
	if not slip:
		return _("A payslip")
	period = _("{0} to {1}").format(formatdate(slip.start_date), formatdate(slip.end_date))
	if user and user_for_employee(slip.employee) == user:
		return _("Your payslip for {0}").format(period)
	return _("Payslip for {0}, {1}").format(slip.employee_name, period)


def _leave_subject(name: str, user: str | None) -> str:
	"""A leave notice's subject without the leave type, the reason or the dates' purpose."""
	from seal_hrms.seal_hrms.handover import user_for_employee

	leave = frappe.db.get_value(LEAVE, name, ["employee", "employee_name"], as_dict=True)
	if user and user_for_employee(leave.employee) == user:
		return _("An update on your leave application")
	return _("Leave application from {0}").format(leave.employee_name)
