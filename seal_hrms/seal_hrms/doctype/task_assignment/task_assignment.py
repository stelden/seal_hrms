# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Task Assignment — who covers a member of staff's work while they are on leave.

The controller is a gate (SEAL_DEV_RULES §3.1): it checks the record makes
sense and refuses it if not. Moving the work is `seal_hrms.handover`'s job; the
controller only decides when to ask for it.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from seal_hrms.seal_hrms import handover, handover_notifications
from seal_hrms.seal_hrms.handover import Answer, Status, answers_for_itself, return_date_for, user_for_employee
from seal_hrms.seal_hrms.task_assignment_access import can_prepare_for


class TaskAssignment(Document):
	def validate(self):
		if not self.posting_date:
			self.posting_date = today()
		self._validate_leave_application()
		self._validate_stand_in()
		if self.docstatus == 0:
			self.status = Status.DRAFT
			self.return_date = return_date_for(self.employee, self.leave_to)

	def before_submit(self):
		self._validate_logins()
		# Submitting sends the handover to the stand-ins. Each answers for what
		# they cover; nothing moves until they all have and the leave starts.
		self.acceptance = Answer.PENDING
		self.decline_reason = None
		for row in self.assignment_todos:
			row.acceptance = Answer.PENDING if answers_for_itself(self, row) else None
			row.decline_reason = None
		# Approving in someone's place is always agreed on its own row (decision T2).
		for row in self.get("authorities") or []:
			row.acceptance = Answer.PENDING
			row.decline_reason = None
		self.status = Status.AWAITING

	def on_submit(self):
		for employee, rows in handover.stand_ins(self).items():
			handover_notifications.asked_to_cover(self, employee, rows)

	def on_cancel(self):
		status = frappe.db.get_value(self.doctype, self.name, "status")
		if status == Status.ACTIVE:
			handover.hand_back(self.name, final_status=Status.CANCELLED)
			handover_notifications.assignment_withdrawn(self, self.task_assignee)
		else:
			self.db_set("status", Status.CANCELLED, update_modified=False)

	def _validate_leave_application(self):
		if not self.leave_application:
			return
		leave = frappe.db.get_value(
			"Leave Application",
			self.leave_application,
			["employee", "from_date", "to_date", "docstatus"],
			as_dict=True,
		)
		if not leave:
			return
		if leave.employee != self.employee:
			frappe.throw(_("This leave belongs to someone else. Choose one of {0}'s own leave applications.").format(
				self.employee_name or self.employee
			))
		if self.is_new() and leave.docstatus == 2:
			frappe.throw(_("This leave application has been cancelled, so there is nothing to cover."))

	def _validate_stand_in(self):
		self._validate_authorities()
		for row in [*self.assignment_todos, *(self.get("authorities") or [])]:
			if row.task_assignee and row.task_assignee != self.task_assignee:
				self._check_can_cover(row.task_assignee, frappe.db.get_value("Employee", row.task_assignee, "employee_name"))
		if self.task_assignee:
			self._check_can_cover(self.task_assignee, self.task_assignee_name)

	def _validate_authorities(self):
		from seal_hrms.seal_hrms import acting

		kinds = acting.registry()
		seen = set()
		for row in self.get("authorities") or []:
			if row.authority not in kinds:
				frappe.throw(_("Row {0} of Approvals is not an approval this site knows about. Use Find What I Approve.").format(row.idx))
			if row.authority in seen:
				frappe.throw(_("{0} is listed twice under Approvals.").format(_(kinds[row.authority].label)))
			seen.add(row.authority)
			row.authority_label = _(kinds[row.authority].label)

	def _check_can_cover(self, stand_in, stand_in_name):
		if stand_in == self.employee:
			frappe.throw(_("You cannot cover your own work. Choose a colleague."))
		if frappe.db.get_value("Employee", stand_in, "status") != "Active":
			frappe.throw(_("{0} is no longer an active member of staff. Choose someone else.").format(
				stand_in_name or stand_in
			))
		if self.docstatus == 0:
			away = stand_in_leave_overlapping(stand_in, self.leave_from, self.leave_to)
			if away:
				frappe.throw(_(
					"{0} is on leave themselves between {1} and {2} ({3}). Choose someone else, or change the dates."
				).format(stand_in_name or stand_in, away.from_date, away.to_date, away.name))

	def _validate_logins(self):
		if not user_for_employee(self.employee):
			frappe.throw(_("{0} has no login, so there is no work list to hand over from.").format(
				self.employee_name or self.employee
			))
		for employee in handover.stand_ins(self):
			if not user_for_employee(employee):
				frappe.throw(_("{0} has no login, so work cannot be passed to them. Ask HR to give them one, or choose someone else.").format(
					frappe.db.get_value("Employee", employee, "employee_name") or employee
				))


def stand_in_leave_overlapping(employee: str, from_date, to_date):
	"""The stand-in's own leave that overlaps these dates, if any.

	Overlap, not containment: the 2024 check only caught leave falling entirely
	inside the dates, so a stand-in whose leave began a day early passed. Open
	applications count as well as approved ones — a clash found before approval
	is the useful one.
	"""
	if not (employee and from_date and to_date):
		return None
	rows = frappe.get_all(
		"Leave Application",
		filters=[
			["employee", "=", employee],
			["docstatus", "<", 2],
			["status", "in", ["Open", "Approved"]],
			["from_date", "<=", getdate(to_date)],
			["to_date", ">=", getdate(from_date)],
		],
		fields=["name", "from_date", "to_date"],
		limit=1,
	)
	return rows[0] if rows else None


@frappe.whitelist()
def get_employee_tasks(employee: str):
	"""The open work on an employee's list, to pre-fill a handover.

	Only the employee themselves or HR may read someone's list this way.
	"""
	if not employee:
		frappe.throw(_("Choose the member of staff first."))
	if not can_prepare_for(employee):
		frappe.throw(_("You can only prepare a handover for yourself."), frappe.PermissionError)

	user_id = frappe.db.get_value("Employee", employee, "user_id")
	if not user_id:
		frappe.throw(_("{0} has no login, so there is no work list to hand over.").format(employee))

	# get_all, not get_list: the caller has been checked above, and the ToDo
	# query condition would otherwise hide an employee's list from HR.
	return frappe.get_all(
		"ToDo",
		filters={"allocated_to": user_id, "status": "Open"},
		fields=["name", "description", "priority", "date", "reference_type", "reference_name"],
		order_by="date asc",
	)


@frappe.whitelist()
def get_assignable_employees(doctype, txt, searchfield, start, page_len, filters):
	"""Colleagues who could cover: active, in the same company, and not away themselves."""
	employee = filters.get("employee")
	leave_application = filters.get("leave_application")
	if not employee:
		return []

	company = frappe.db.get_value("Employee", employee, "company")
	leave = (
		frappe.db.get_value("Leave Application", leave_application, ["from_date", "to_date"], as_dict=True)
		if leave_application
		else None
	)

	candidates = frappe.get_all(
		"Employee",
		filters=[
			["company", "=", company],
			["status", "=", "Active"],
			["name", "!=", employee],
			["employee_name", "like", f"%{txt or ''}%"],
		],
		fields=["name", "employee_name"],
		order_by="employee_name asc",
	)
	if leave:
		return [
			[emp.name, emp.employee_name]
			for emp in candidates
			if not stand_in_leave_overlapping(emp.name, leave.from_date, leave.to_date)
		]
	return [[emp.name, emp.employee_name] for emp in candidates]

