# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What stand-ins and owners do to a submitted Task Assignment.

A stand-in does not have write permission on someone else's handover, and a
submitted handover is not edited through the form. So these endpoints write
with `db_set` / `ignore_permissions`, and every one of them checks its caller
first (SEAL_DEV_RULES §2.15): the stand-in named on the rows, the owner, or HR.
Nothing here is reachable merely by being logged in.
"""

import frappe
from frappe import _

from seal_hrms.seal_hrms import handover, handover_notifications
from seal_hrms.seal_hrms.handover import ASSIGNMENT, Answer, Status, answers_for_itself, covered_by
from seal_hrms.seal_hrms.task_assignment_access import can_prepare_for, employee_for_user

_ANSWERABLE = (Status.AWAITING, Status.ACCEPTED, Status.DECLINED)


def _submitted(name: str):
	doc = frappe.get_doc(ASSIGNMENT, name)
	if doc.docstatus != 1:
		frappe.throw(_("{0} has not been sent to the stand-in yet.").format(name))
	return doc


def _me() -> str:
	me = employee_for_user(frappe.session.user)
	if not me:
		frappe.throw(_("Your login is not linked to a member of staff."), frappe.PermissionError)
	return me


def _require_owner_or_hr(doc) -> None:
	if not can_prepare_for(doc.employee):
		frappe.throw(_("Only {0} or HR can do this.").format(doc.employee_name), frappe.PermissionError)


@frappe.whitelist()
def respond(name: str, answer: str, reason: str | None = None) -> dict:
	"""A stand-in agrees to cover their part of the handover, or declines it with a reason."""
	if answer not in (Answer.ACCEPTED, Answer.DECLINED):
		frappe.throw(_("Answer Accepted or Declined."))

	# Lock first: two stand-ins answering at once must not overwrite each other's status.
	frappe.db.get_value(ASSIGNMENT, name, "name", for_update=True)
	doc = _submitted(name)
	if answer == Answer.DECLINED and not (reason or "").strip():
		frappe.throw(_("Say why you cannot cover it, so {0} can ask someone else.").format(doc.employee_name))
	me = _me()
	mine_as_main = doc.task_assignee == me
	my_rows = [row for row in doc.assignment_todos if answers_for_itself(doc, row) and row.task_assignee == me]
	if not (mine_as_main or my_rows):
		frappe.throw(_("You are not named as a stand-in on {0}.").format(name), frappe.PermissionError)
	if doc.status not in _ANSWERABLE:
		frappe.throw(_("{0} can no longer be answered: it is {1}.").format(name, _(doc.status)))

	reason = reason.strip() if answer == Answer.DECLINED else None
	if mine_as_main:
		doc.db_set({"acceptance": answer, "decline_reason": reason}, update_modified=False)
	for row in my_rows:
		row.db_set({"acceptance": answer, "decline_reason": reason}, update_modified=False)

	doc.add_comment("Info", _("{0} {1} covering this.").format(
		frappe.utils.get_fullname(frappe.session.user),
		_("agreed to") if answer == Answer.ACCEPTED else _("declined"),
	) + (f" {frappe.utils.escape_html(reason)}" if reason else ""))
	return _settle(name)


@frappe.whitelist()
def respond_authority(name: str, row: str, answer: str, reason: str | None = None) -> dict:
	"""A stand-in agrees, or declines, to approve one kind of thing in the owner's place.

	Separate from `respond` on purpose (decision T2): agreeing to cover someone's
	work is not agreeing to sign for them, so each approval is answered on its own.
	"""
	if answer not in (Answer.ACCEPTED, Answer.DECLINED):
		frappe.throw(_("Answer Accepted or Declined."))
	frappe.db.get_value(ASSIGNMENT, name, "name", for_update=True)
	doc = _submitted(name)
	me = _me()
	target = next((r for r in doc.get("authorities") or [] if r.name == row), None)
	if not target:
		frappe.throw(_("That approval is not on {0}.").format(name))
	if covered_by(doc, target) != me:
		frappe.throw(_("Only the person named to approve this can answer for it."), frappe.PermissionError)
	if doc.status not in _ANSWERABLE:
		frappe.throw(_("{0} can no longer be answered: it is {1}.").format(name, _(doc.status)))
	if answer == Answer.DECLINED and not (reason or "").strip():
		frappe.throw(_("Say why you cannot approve this, so {0} can ask someone else.").format(doc.employee_name))

	reason = reason.strip() if answer == Answer.DECLINED else None
	target.db_set({"acceptance": answer, "decline_reason": reason}, update_modified=False)
	doc.add_comment("Info", _("{0} {1} approving {2} in {3}'s place.").format(
		frappe.utils.get_fullname(frappe.session.user),
		_("agreed to") if answer == Answer.ACCEPTED else _("declined"),
		(target.authority_label or target.authority).lower(),
		doc.employee_name,
	) + (f" {frappe.utils.escape_html(reason)}" if reason else ""))
	return _settle(name)


def _settle(name: str) -> dict:
	"""Work out the handover's status from everyone's answers, and start it if that was the last thing missing."""
	doc = frappe.get_doc(ASSIGNMENT, name)
	overall = handover.overall_answer(doc)
	status = {Answer.ACCEPTED: Status.ACCEPTED, Answer.DECLINED: Status.DECLINED}.get(overall, Status.AWAITING)
	if status != doc.status:
		doc.db_set("status", status, update_modified=False)
		if status in (Status.ACCEPTED, Status.DECLINED):
			handover_notifications.answered(doc, status)
	activated = handover.maybe_activate(name)
	return {"status": Status.ACTIVE if activated else status}


@frappe.whitelist()
def add_note(name: str, row: str, note: str) -> None:
	"""The stand-in records what they did on one piece of work."""
	doc = _submitted(name)
	me = _me()
	target = next((r for r in doc.assignment_todos if r.name == row), None)
	if not target:
		frappe.throw(_("That task is not on {0}.").format(name))
	if covered_by(doc, target) != me:
		frappe.throw(_("Only whoever covers this task can leave notes on it."), frappe.PermissionError)
	target.db_set("stand_in_notes", note, update_modified=False)


@frappe.whitelist()
def leave_return_note(name: str, note: str) -> None:
	"""A stand-in leaves the owner a note for when they come back."""
	doc = _submitted(name)
	me = _me()
	if me not in handover.stand_ins(doc):
		frappe.throw(_("Only a stand-in on {0} can leave the return note.").format(name), frappe.PermissionError)
	doc.db_set("return_summary", note, update_modified=False)


@frappe.whitelist()
def return_work(name: str) -> dict:
	"""The owner is back early, or HR is ending the cover: give everything back now."""
	doc = _submitted(name)
	_require_owner_or_hr(doc)
	if doc.status != Status.ACTIVE:
		frappe.throw(_("Nothing has been handed over on {0} yet, so there is nothing to return.").format(name))
	handover.hand_back(name)
	return {"status": frappe.db.get_value(ASSIGNMENT, name, "status")}


@frappe.whitelist()
def prepare_from_leave(leave_application: str) -> str:
	"""Start a handover for a leave application, pre-filled with the owner's open work.

	Returns the existing handover if there already is one that is not cancelled.
	"""
	leave = frappe.db.get_value(
		"Leave Application", leave_application, ["name", "employee", "docstatus"], as_dict=True
	)
	if not leave:
		frappe.throw(_("Leave application {0} was not found.").format(leave_application))
	if not can_prepare_for(leave.employee):
		frappe.throw(_("You can only prepare a handover for your own leave."), frappe.PermissionError)
	if leave.docstatus == 2:
		frappe.throw(_("This leave has been cancelled, so there is nothing to hand over."))

	existing = frappe.db.get_value(
		ASSIGNMENT, {"leave_application": leave.name, "docstatus": ["<", 2]}, "name"
	)
	if existing and frappe.db.exists(ASSIGNMENT, existing):
		return existing

	from seal_hrms.seal_hrms.doctype.task_assignment.task_assignment import get_employee_tasks

	doc = frappe.new_doc(ASSIGNMENT)
	doc.employee = leave.employee
	doc.leave_application = leave.name
	doc.task_description = ""
	try:
		for todo in get_employee_tasks(leave.employee):
			doc.append("assignment_todos", {
				"todo": todo.name,
				"description": todo.description,
				"priority": todo.priority,
				"due_date": todo.date,
				"reference_type": todo.reference_type,
				"reference_name": todo.reference_name,
			})
	except Exception:
		pass

	from seal_hrms.seal_hrms.acting import suggest_authorities

	try:
		for authority in suggest_authorities(leave.employee):
			doc.append("authorities", authority)
	except Exception:
		pass

	# Mandatory fields (stand-in, description) are the owner's to fill in the form.
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return doc.name
