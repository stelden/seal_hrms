# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What a leave handover is waiting on each person for.

Plain records, answered on any site. My Desk turns them into desk items
(`seal_hrms/desk/providers.py`), but nothing here knows the desk exists, so the
same answers can feed a workspace, a report or an email.

Each record: kind, doctype, name, title, subtitle, due, route. `kind` uses the
desk's words: "approval" for something only this person can answer, "task" for
work to do, "draft" for something they started and have not sent,
"notification" for news.
"""

import frappe
from frappe import _
from frappe.utils import add_days, formatdate, getdate, today

from seal_hrms.seal_hrms.handover import ASSIGNMENT, Answer, Status, answers_for_itself, covered_by
from seal_hrms.seal_hrms.task_assignment_access import employee_for_user

#: How long a "your work is back" note stays on someone's desk.
WELCOME_BACK_DAYS = 3


def _record(kind, doctype, name, title, subtitle="", due=None):
	return frappe._dict(
		kind=kind, doctype=doctype, name=name, title=title, subtitle=subtitle, due=due,
		route=f"/app/{frappe.scrub(doctype).replace('_', '-')}/{name}",
	)


def work_for(user: str, on_date=None) -> list[frappe._dict]:
	"""Everything a handover needs from `user` today."""
	me = employee_for_user(user)
	if not me:
		return []
	on_date = getdate(on_date or today())
	return [
		*_handovers_to_prepare(me, on_date),
		*_my_handovers(me, on_date),
		*_asked_of_me(me),
		*_covering(me),
	]


def _handovers_to_prepare(me, on_date):
	"""Leave coming up with no handover started. The company's policy says how far ahead."""
	from seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy import policy_for

	company = frappe.db.get_value("Employee", me, "company")
	horizon = add_days(on_date, int(policy_for(company).prep_reminder_days or 7))
	leaves = frappe.get_all(
		"Leave Application",
		filters=[["employee", "=", me], ["docstatus", "<", 2], ["status", "in", ["Open", "Approved"]],
		         ["from_date", ">=", on_date], ["from_date", "<=", horizon]],
		fields=["name", "from_date", "to_date"],
	)
	out = []
	for leave in leaves:
		if frappe.db.exists(ASSIGNMENT, {"leave_application": leave.name, "docstatus": ["<", 2]}):
			continue
		out.append(_record(
			"task", "Leave Application", leave.name,
			_("Hand over your work before your leave on {0}").format(formatdate(leave.from_date)),
			_("Click Prepare Handover on the leave application."),
			due=str(leave.from_date),
		))
	return out


def _my_handovers(me, on_date):
	"""Handovers I own that need me: unsent, declined, or back with news."""
	out = []
	for row in frappe.get_all(
		ASSIGNMENT,
		filters=[["employee", "=", me], ["docstatus", "<", 2],
		         ["status", "in", [Status.DRAFT, Status.DECLINED, Status.HANDED_BACK]]],
		fields=["name", "status", "task_assignee_name", "leave_from", "handed_back_at"],
	):
		if row.status == Status.DRAFT:
			out.append(_record(
				"draft", ASSIGNMENT, row.name,
				_("Send your handover to {0}").format(row.task_assignee_name or _("a stand-in")),
				_("It is not sent until you submit it."), due=str(row.leave_from) if row.leave_from else None,
			))
		elif row.status == Status.DECLINED:
			out.append(_record(
				"task", ASSIGNMENT, row.name,
				_("Your stand-in cannot cover your leave"),
				_("Cancel the handover, then amend it with someone else."), due=str(row.leave_from) if row.leave_from else None,
			))
		elif row.handed_back_at and getdate(row.handed_back_at) >= add_days(on_date, -WELCOME_BACK_DAYS):
			out.append(_record(
				"notification", ASSIGNMENT, row.name,
				_("Welcome back: your work is on your list again"),
				_("Your stand-in's notes are on the Return tab."),
			))
	return out


def _asked_of_me(me):
	"""Handovers waiting for my answer: to cover work, or to approve in someone's place."""
	out = []
	for name in frappe.get_all(
		ASSIGNMENT, filters={"docstatus": 1, "status": ["in", [Status.AWAITING, Status.DECLINED]]}, pluck="name"
	):
		doc = frappe.get_doc(ASSIGNMENT, name)
		pending = (doc.task_assignee == me and doc.acceptance == Answer.PENDING) or any(
			answers_for_itself(doc, r) and r.task_assignee == me and r.acceptance == Answer.PENDING
			for r in doc.assignment_todos
		) or any(covered_by(doc, r) == me and r.acceptance == Answer.PENDING for r in doc.get("authorities") or [])
		if pending:
			out.append(_record(
				"approval", ASSIGNMENT, name,
				_("{0} has asked you to cover their leave").format(doc.employee_name),
				_("From {0}. Accept or decline.").format(formatdate(doc.leave_from)),
				due=str(doc.leave_from),
			))
	return out


def _covering(me):
	"""Handovers in effect where I am carrying someone's work."""
	out = []
	for name in frappe.get_all(ASSIGNMENT, filters={"docstatus": 1, "status": Status.ACTIVE}, pluck="name"):
		doc = frappe.get_doc(ASSIGNMENT, name)
		mine = [r for r in doc.assignment_todos if covered_by(doc, r) == me]
		approvals = [r for r in doc.get("authorities") or [] if covered_by(doc, r) == me]
		if not (mine or approvals or doc.task_assignee == me):
			continue
		out.append(_record(
			"task", ASSIGNMENT, name,
			_("Covering for {0} until {1}").format(doc.employee_name, formatdate(doc.return_date or doc.leave_to)),
			_("{0} task(s); leave them a note before they are back.").format(len(mine)),
			due=str(doc.return_date) if doc.return_date else None,
		))
	return out
