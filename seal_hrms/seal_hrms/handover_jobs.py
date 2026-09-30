# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Daily work for Task Assignments.

Each assignment is handled in its own try/except and committed on its own, so
one broken record cannot hold up everybody else's return.
"""

import frappe
from frappe.utils import add_days, getdate, today

from seal_hrms.seal_hrms import handover
from seal_hrms.seal_hrms.handover import ASSIGNMENT, Status


def daily() -> None:
	"""Scheduler entry point: start cover, remind about returns, and return work."""
	remind_to_prepare()
	activate_started_leave()
	remind_before_return()
	hand_back_ended_leave()


def _each(names, fn, title: str) -> list[str]:
	"""Run `fn` per record, so one failure cannot stop the rest.

	A savepoint rather than a full rollback undoes only the failed record, and
	leaves a test's own fixtures alone.
	"""
	done = []
	for name in names:
		frappe.db.savepoint("task_assignment_job")
		try:
			if fn(name):
				done.append(name)
			if not frappe.flags.in_test:
				frappe.db.commit()
		except Exception:
			frappe.db.rollback(save_point="task_assignment_job")
			frappe.log_error(
				title=title, message=frappe.get_traceback(), reference_doctype=ASSIGNMENT, reference_name=name
			)
	return done


def remind_to_prepare(on_date=None) -> list[str]:
	"""Email people with leave coming up and nobody asked to cover their work. Once per leave (§3.7).

	Only for companies whose Task Assignment Policy switches the email on, and
	only for the kinds and lengths of leave that policy is about. The reminder
	window is a range, not an exact day, so a weekend never skips anyone (§3.8).
	Returns the leave applications reminded.
	"""
	from seal_hrms.seal_hrms import handover_notifications
	from seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy import covers, policy_for

	if not frappe.db.has_column("Leave Application", "custom_handover_reminder_sent"):
		return []
	on_date = getdate(on_date or today())
	reminded = []
	for company in frappe.get_all("Task Assignment Policy", filters={"email_prep_reminder": 1}, pluck="company"):
		policy = policy_for(company)
		horizon = add_days(on_date, int(policy.prep_reminder_days or 7))
		leaves = frappe.get_all(
			"Leave Application",
			filters=[
				["company", "=", company], ["docstatus", "<", 2], ["status", "in", ["Open", "Approved"]],
				["from_date", ">=", on_date], ["from_date", "<=", horizon],
				["custom_handover_reminder_sent", "=", 0],
			],
			fields=["name", "employee", "employee_name", "leave_type", "from_date", "to_date", "total_leave_days"],
		)
		for leave in leaves:
			if not covers(policy, leave.leave_type, leave.total_leave_days):
				continue
			if frappe.db.exists(ASSIGNMENT, {"leave_application": leave.name, "docstatus": ["<", 2]}):
				continue

			def remind(name, leave=leave):
				if frappe.db.get_value("Leave Application", name, "custom_handover_reminder_sent", for_update=True):
					return False
				frappe.db.set_value("Leave Application", name, "custom_handover_reminder_sent", 1, update_modified=False)
				handover_notifications.prepare_your_handover(
					leave, leave.employee_name, (getdate(leave.from_date) - on_date).days
				)
				return True

			reminded += _each([leave.name], remind, "Task Assignment: handover reminder not sent")
	return reminded


def activate_started_leave(on_date=None) -> list[str]:
	"""Move work for agreed handovers whose leave has started and been approved."""
	on_date = getdate(on_date or today())
	due = frappe.get_all(
		ASSIGNMENT,
		filters=[["docstatus", "=", 1], ["status", "=", Status.ACCEPTED], ["leave_from", "<=", on_date]],
		pluck="name",
	)
	return _each(due, lambda name: handover.maybe_activate(name, on_date), "Task Assignment: cover could not start")


def remind_before_return(on_date=None) -> list[str]:
	"""The day before the owner is back, ask stand-ins for a note. Once per handover (§3.7)."""
	on_date = getdate(on_date or today())
	due = frappe.get_all(
		ASSIGNMENT,
		filters=[
			["docstatus", "=", 1], ["status", "=", Status.ACTIVE], ["return_reminder_sent", "=", 0],
			["return_date", "<=", add_days(on_date, 1)], ["return_date", ">", on_date],
		],
		pluck="name",
	)

	def remind(name):
		if frappe.db.get_value(ASSIGNMENT, name, "return_reminder_sent", for_update=True):
			return False
		frappe.db.set_value(ASSIGNMENT, name, "return_reminder_sent", 1, update_modified=False)
		doc = frappe.get_doc(ASSIGNMENT, name)
		from seal_hrms.seal_hrms import handover_notifications

		for employee in handover.stand_ins(doc):
			handover_notifications.return_note_due(doc, employee)
		return True

	return _each(due, remind, "Task Assignment: return reminder not sent")


def hand_back_ended_leave(on_date=None) -> list[str]:
	"""Return the work of everyone back at work today. Returns the assignments handled."""
	on_date = getdate(on_date or today())
	due = frappe.get_all(
		ASSIGNMENT,
		filters=[["docstatus", "=", 1], ["status", "=", Status.ACTIVE], ["return_date", "<=", on_date]],
		pluck="name",
	)
	# A handover that took effect before return dates existed has only its leave dates.
	due += frappe.get_all(
		ASSIGNMENT,
		filters=[["docstatus", "=", 1], ["status", "=", Status.ACTIVE], ["return_date", "is", "not set"],
		         ["leave_to", "<", on_date]],
		pluck="name",
	)
	return _each(due, handover.hand_back, "Task Assignment: work could not be returned")
