# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""People, leave and work for the Task Assignment tests.

Everything is created through the ORM (SEAL_DEV_RULES §1.9) so the real
controllers, hooks and assignment comments run. The cast is a small Nairobi
office: Wanjiku goes on leave, Otieno covers for her, Njeri is a second
colleague, and Achieng approves leave.
"""

import frappe
from frappe.desk.form import assign_to
from frappe.utils import add_days, today

COMPANY = "_Test Company"
LEAVE_TYPE = "Family Responsibility Leave"
DOMAIN = "kilimani-office.co.ke"

PEOPLE = {
	"wanjiku": ("Wanjiku", "Kamau", "Female"),
	"otieno": ("Otieno", "Ochieng", "Male"),
	"njeri": ("Njeri", "Mwangi", "Female"),
	"achieng": ("Achieng", "Odhiambo", "Female"),
}
PHONES = {"wanjiku": "254722418305", "otieno": "254733902614", "njeri": "254711560287", "achieng": "254745130968"}


def email(key: str) -> str:
	first, last, _gender = PEOPLE[key]
	return f"{first.lower()}.{last.lower()}@{DOMAIN}"


def ensure_user(key: str, roles=("Employee",)) -> str:
	"""A login, created before its Employee so HRMS links rather than duplicates the Contact."""
	address = email(key)
	first, last, _gender = PEOPLE[key]
	if not frappe.db.exists("User", address):
		user = frappe.new_doc("User")
		user.email = address
		user.first_name = first
		user.last_name = last
		user.send_welcome_email = 0
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", address)
	missing = [r for r in roles if r not in frappe.get_roles(address)]
	if missing:
		user.add_roles(*missing)
	return address


def ensure_employee(key: str) -> str:
	first, last, gender = PEOPLE[key]
	user = ensure_user(key)
	existing = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if existing:
		if frappe.db.get_value("Employee", existing, "status") != "Active":
			doc = frappe.get_doc("Employee", existing)
			doc.status = "Active"
			doc.relieving_date = None
			doc.save(ignore_permissions=True)
		return existing
	doc = frappe.new_doc("Employee")
	doc.first_name = first
	doc.last_name = last
	doc.gender = gender
	doc.date_of_birth = "1990-04-12"
	doc.date_of_joining = "2022-02-01"
	doc.status = "Active"
	doc.company = COMPANY
	doc.cell_number = PHONES[key]
	doc.user_id = user
	doc.holiday_list = frappe.db.get_value("Company", COMPANY, "default_holiday_list")
	doc.insert(ignore_permissions=True)
	return doc.name


def approver() -> str:
	return ensure_user("achieng", roles=("Employee", "Leave Approver"))


def ensure_leave_type() -> str:
	"""Unpaid, so no allocation is needed, and with no notice period to trip over."""
	if not frappe.db.exists("Leave Type", LEAVE_TYPE):
		doc = frappe.new_doc("Leave Type")
		doc.leave_type_name = LEAVE_TYPE
		doc.is_lwp = 1
		doc.include_holiday = 1
		doc.insert(ignore_permissions=True)
	doc = frappe.get_doc("Leave Type", LEAVE_TYPE)
	# This site's Leave Type defaults to five days' notice; family emergencies give none.
	for field in ("custom_minimum_leave_application_days", "custom_min_application_advance_days", "custom_min_leave_days"):
		if doc.meta.has_field(field) and doc.get(field):
			doc.set(field, 0)
	doc.save(ignore_permissions=True)
	return LEAVE_TYPE


def leave(employee: str, start_offset: int, days: int, status: str = "Open", submit: bool = False):
	"""A leave application `start_offset` days from today, lasting `days` days."""
	doc = frappe.new_doc("Leave Application")
	doc.employee = employee
	doc.leave_type = ensure_leave_type()
	doc.from_date = add_days(today(), start_offset)
	doc.to_date = add_days(today(), start_offset + days - 1)
	doc.leave_approver = approver()
	doc.description = "Family matters upcountry in Nyeri"
	doc.status = status
	doc.insert(ignore_permissions=True)
	if submit:
		doc.submit()
	return doc


def project_task(subject: str) -> str:
	"""Something to be assigned. Plain Employees cannot open a Task, so a stand-in needs a share."""
	doc = frappe.new_doc("Task")
	doc.subject = subject
	doc.insert(ignore_permissions=True)
	return doc.name


def assign(task: str, user: str, assigned_by: str = "Administrator") -> str:
	"""Put a Task on someone's list the way Frappe's Assign To does, and return the ToDo."""
	previous = frappe.session.user
	frappe.set_user(assigned_by)
	try:
		assign_to.add({"assign_to": [user], "doctype": "Task", "name": task, "description": f"Follow up: {task}"})
	finally:
		frappe.set_user(previous)
	return frappe.db.get_value(
		"ToDo", {"reference_type": "Task", "reference_name": task, "allocated_to": user, "status": "Open"}, "name"
	)


def handover(employee: str, stand_in: str, la, rows: list[dict], submit: bool = True):
	doc = frappe.new_doc("Task Assignment")
	doc.employee = employee
	doc.leave_application = la.name
	doc.task_assignee = stand_in
	doc.task_description = "<p>Keep the Westlands branch reconciliations moving and answer supplier calls.</p>"
	for row in rows:
		doc.append("assignment_todos", row)
	doc.insert(ignore_permissions=True)
	if submit:
		doc.submit()
	return doc


def as_user(user: str, fn, *args, **kwargs):
	"""Call `fn` as `user`, and always come back as Administrator."""
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


def agree(ta, *stand_in_keys):
	"""Each named stand-in accepts their part."""
	from seal_hrms.seal_hrms import task_assignment_actions

	for key in stand_in_keys:
		as_user(email(key), task_assignment_actions.respond, ta.name, "Accepted")
	ta.reload()
	return ta


def approve(la):
	la.reload()
	la.status = "Approved"
	la.submit()
	return la


def take_effect(ta, la, *stand_in_keys):
	"""Everything a handover needs before work moves: agreement, approval, and the leave begun."""
	from seal_hrms.seal_hrms import handover

	approve(la)
	agree(ta, *(stand_in_keys or ("otieno",)))
	handover.maybe_activate(ta.name, on_date=la.from_date)
	ta.reload()
	return ta


def open_todos(user: str, task: str) -> list[str]:
	return frappe.get_all(
		"ToDo",
		filters={"reference_type": "Task", "reference_name": task, "allocated_to": user, "status": "Open"},
		pluck="name",
	)


def cleanup(employees: list[str]) -> None:
	"""Remove what the tests created for these people, leaving the people themselves."""
	users = [frappe.db.get_value("Employee", e, "user_id") for e in employees]
	for name in frappe.get_all("Task Assignment", filters={"employee": ["in", employees]}, pluck="name"):
		doc = frappe.get_doc("Task Assignment", name)
		if doc.docstatus == 1:
			doc.flags.ignore_permissions = True
			doc.cancel()
		frappe.delete_doc("Task Assignment", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Leave Application", filters={"employee": ["in", employees]}, pluck="name"):
		doc = frappe.get_doc("Leave Application", name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Leave Application", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("ToDo", filters={"allocated_to": ["in", users]}, pluck="name"):
		frappe.delete_doc("ToDo", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("DocShare", filters={"user": ["in", users], "share_doctype": "Task"}, pluck="name"):
		frappe.delete_doc("DocShare", name, force=1, ignore_permissions=True)
