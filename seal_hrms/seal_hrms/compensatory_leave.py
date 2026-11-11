# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Compensatory Leave Requests: who decides them, and where one has got to (Keith, 2026-11-11).

Frappe HR's Compensatory Leave Request earns leave for days worked on a holiday or day off:
submitting it adds those days to a compensatory leave type. Frappe HR names no approver (HR
submits it) and keeps no state beyond draft and submitted. seal_hrms adds, without changing
Frappe HR:

* **One way per leave type.** A leave type that a company banks time off in lieu into belongs to
  the Time Off in Lieu Claim, which counts hours (`toil.guards.compensatory_request` refuses a
  request on it). Requests are offered only for the other compensatory types (CL-1).
* **The approver** is the employee's leave approver, by Frappe HR's own rule for leave
  (`get_employee_leave_approver`): the request earns leave, so whoever approves the leave
  approves the earning (CL-2).
* **Where it is** is Frappe's own assignment (a ToDo): a new draft request is assigned to the
  approver, which notifies them, shares it with them and shows "Assigned to" on the desk. Their
  stand-in reaches it through the handover like any other leave approval. Approving submits it
  (Frappe HR's allocation); rejecting cancels the assignment with a reason. No new field and no
  status machine of our own (CL-3).

Where the site runs its own Frappe Workflow on Compensatory Leave Request (SEAL_DEV_RULES §1.23),
none of this assigns or decides: the workflow's steps are the approval (CL-4).
"""

from __future__ import annotations

import frappe
from frappe import _

DOCTYPE = "Compensatory Leave Request"
AUTHORITY = "leave_approval"

WAITING = "Waiting for Approval"
APPROVED = "Approved"
REJECTED = "Rejected"
NOT_SENT = "Not Sent"
CANCELLED = "Cancelled"


def has_workflow() -> bool:
	"""The site moves these requests by a Frappe Workflow of its own."""
	from frappe.model.workflow import get_workflow_name

	return bool(get_workflow_name(DOCTYPE))


def offered_leave_types() -> list[str]:
	"""Compensatory leave types a request may earn: every one not banked as time off in lieu (CL-1)."""
	from seal_hrms.seal_hrms.working_time.policy import toil_leave_types

	toil = toil_leave_types()
	return [t for t in frappe.get_all("Leave Type", filters={"is_compensatory": 1}, pluck="name", order_by="name asc") if t not in toil]


def approver_of(employee: str) -> str | None:
	"""Who approves this employee's requests: their leave approver, else their department's first (CL-2)."""
	from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

	return get_employee_leave_approver(employee) or None


def waiting_with(name: str) -> list[str]:
	"""Who the request is with now: the users holding an open assignment on it."""
	return frappe.get_all(
		"ToDo",
		filters={"reference_type": DOCTYPE, "reference_name": name, "status": "Open"},
		pluck="allocated_to",
		order_by="creation asc",
	)


def state_of(doc) -> str:
	"""Approved, Cancelled, Waiting for Approval, Rejected (assignment cancelled, none open) or Not Sent."""
	if doc.docstatus == 1:
		return APPROVED
	if doc.docstatus == 2:
		return CANCELLED
	if waiting_with(doc.name):
		return WAITING
	if frappe.db.exists("ToDo", {"reference_type": DOCTYPE, "reference_name": doc.name, "status": "Cancelled"}):
		return REJECTED
	return NOT_SENT


def last_reason(name: str) -> str | None:
	"""The newest comment on the request: a rejection's reason, as the approver wrote it."""
	from frappe.utils import strip_html

	content = frappe.db.get_value(
		"Comment",
		{"reference_doctype": DOCTYPE, "reference_name": name, "comment_type": "Comment"},
		"content",
		order_by="creation desc",
	)
	return strip_html(content).strip() if content else None


def send(doc) -> str | None:
	"""Assign a draft request to its approver and let them submit it. Returns the approver, or None.

	The assignment notifies them (bell and phone) and shares the request for reading; the submit
	share is Frappe HR's own for approvers (`share_doc_with_approver`), and a stand-in acting for
	them gets theirs from the handover (`acting.share_new_document`).
	"""
	from frappe.desk.form import assign_to
	from hrms.hr.utils import share_doc_with_approver

	from seal_hrms.seal_hrms import acting
	from seal_hrms.seal_hrms.handover import user_for_employee

	if doc.docstatus != 0 or has_workflow() or waiting_with(doc.name):
		return None
	approver = approver_of(doc.employee)
	if not approver or approver == user_for_employee(doc.employee):
		return None
	share_doc_with_approver(doc, approver)  # first, so the assignment finds them able to open it
	assign_to.add(
		{
			"assign_to": [approver],
			"doctype": DOCTYPE,
			"name": doc.name,
			"description": _("Compensatory leave request from {0} to approve").format(doc.employee_name or doc.employee),
		}
	)
	acting.share_new_document(doc, approver, AUTHORITY)
	return approver


def _close(name: str, status: str) -> None:
	"""Set every open assignment on the request to `status`, through ToDo's own save (it keeps "Assigned to" right)."""
	for todo in frappe.get_all("ToDo", filters={"reference_type": DOCTYPE, "reference_name": name, "status": "Open"}, pluck="name"):
		row = frappe.get_doc("ToDo", todo)
		row.status = status
		row.save(ignore_permissions=True)


def reject(doc) -> None:
	"""Take the request off the approver's list: its assignment is cancelled. The reason is a comment."""
	_close(doc.name, "Cancelled")


# ---------------------------------------------------------------- doc_events


def after_insert(doc, method=None) -> None:
	"""A new draft goes to its approver at once, from the phone or the desk (as a leave application does)."""
	send(doc)


def before_submit(doc, method=None) -> None:
	"""Whoever approves in the approver's place may not approve their own request."""
	from seal_hrms.seal_hrms import acting

	for approver in waiting_with(doc.name) or [approver_of(doc.employee)]:
		acting.refuse_self_approval(doc, doc.employee, approver, AUTHORITY)


def on_submit(doc, method=None) -> None:
	"""Approved: the assignment is done, and a stand-in's approval is noted on the timeline."""
	from seal_hrms.seal_hrms import acting

	named = waiting_with(doc.name)
	if named:
		acting.record_acting_approval(doc, named[0], AUTHORITY)
	_close(doc.name, "Closed")


def on_trash(doc, method=None) -> None:
	"""Withdrawn or deleted: nothing is left waiting on anyone's list."""
	_close(doc.name, "Cancelled")


# ---------------------------------------------------------------- the handover's kind


def pending(user: str) -> list[tuple[str, str]]:
	"""Requests waiting for `user` as approver, for the handover to share with their stand-in."""
	if not frappe.db.table_exists(DOCTYPE):
		return []
	names = frappe.get_all(
		"ToDo",
		filters={"reference_type": DOCTYPE, "allocated_to": user, "status": "Open"},
		pluck="reference_name",
	)
	if not names:
		return []
	return [(DOCTYPE, n) for n in frappe.get_all(DOCTYPE, filters={"name": ["in", names], "docstatus": 0}, pluck="name")]
