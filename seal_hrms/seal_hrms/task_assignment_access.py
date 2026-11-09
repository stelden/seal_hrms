# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Who may see and change a Task Assignment.

Until 1.3.0 only System Manager had any permission on the doctype, so staff
could not prepare their own handover. Now:

  * the member of staff going on leave prepares, submits and cancels their own;
  * each stand-in can read the handovers that name them. They do not get write:
    anything they record on their own rows goes through endpoints that check
    the caller first (SEAL_DEV_RULES §2.15);
  * the leave approver of the linked leave can read it, so approval can see
    whether cover is arranged;
  * HR User, HR Manager and System Manager see and change everything.

Both hooks return a plain bool (§2.9) and ship together (§3.4).

The Employee links on the doctype set `ignore_user_permissions`. HRMS gives
every login an "Employee = themselves" User Permission, which would otherwise
hide a colleague's handover from the very stand-in it names, before either hook
here is asked.
"""

import frappe

ASSIGNMENT = "Task Assignment"
BACKOFFICE_ROLES = {"HR User", "HR Manager", "System Manager"}
READ_PTYPES = {"read", "select", "print", "email", "report", "export"}


def _is_backoffice(user: str) -> bool:
	return user == "Administrator" or bool(set(frappe.get_roles(user)) & BACKOFFICE_ROLES)


def employee_for_user(user: str) -> str | None:
	return frappe.db.get_value("Employee", {"user_id": user}, "name") or None


@frappe.whitelist()
def my_employee() -> str | None:
	"""The session user's own Employee record, for the handover form.

	The form cannot ask this itself: filtering Employee on `user_id` from the
	browser is refused for ordinary staff ("no permission to access field
	Employee.user_id"), which is exactly who a stand-in usually is. Reads the
	caller's own link only.
	"""
	return employee_for_user(frappe.session.user)


#: What a member of staff may read about their own Employee record from a form.
OWN_FIELDS = ("name", "company", "employee_name", "department")


@frappe.whitelist()
def my_employee_fields(fields: str | list | None = None) -> dict:
	"""The session user's own Employee record, the fields in OWN_FIELDS only.

	For forms that look the person up by login, which Frappe refuses for staff
	(Employee.user_id sits at a permission level they cannot read): ERPNext's new
	Timesheet does this on load. Answers for the caller's own record only, and
	only the harmless fields; anything else is refused.
	"""
	if isinstance(fields, str):
		fields = frappe.parse_json(fields) if fields.startswith("[") else [fields]
	fields = list(fields or ["name"])
	if any(f not in OWN_FIELDS for f in fields):
		frappe.throw(frappe._("Only {0} can be read this way.").format(", ".join(OWN_FIELDS)), frappe.PermissionError)
	me = employee_for_user(frappe.session.user)
	if not me:
		return {}
	return frappe.db.get_value("Employee", me, fields, as_dict=True) or {}


def can_prepare_for(employee: str, user: str | None = None) -> bool:
	"""Whether `user` may prepare or change a handover for `employee`."""
	user = user or frappe.session.user
	if _is_backoffice(user):
		return True
	return bool(employee) and employee_for_user(user) == employee


def _stand_ins(doc) -> set[str]:
	names = {doc.get("task_assignee")}
	for row in doc.get("assignment_todos") or []:
		names.add(row.get("task_assignee"))
	for row in doc.get("authorities") or []:
		names.add(row.get("task_assignee"))
	names.discard(None)
	names.discard("")
	return names


def has_permission(doc, ptype=None, user=None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if _is_backoffice(user):
		return True

	me = employee_for_user(user)
	if me and doc.get("employee") == me:
		return True

	if (ptype or "read") in READ_PTYPES:
		if me and me in _stand_ins(doc):
			return True
		leave = doc.get("leave_application")
		if leave and frappe.db.get_value("Leave Application", leave, "leave_approver") == user:
			return True
	return False


def query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if _is_backoffice(user):
		return ""

	quoted_user = frappe.db.escape(user)
	approver = (
		f"`tab{ASSIGNMENT}`.leave_application in "
		f"(select name from `tabLeave Application` where leave_approver = {quoted_user})"
	)
	me = employee_for_user(user)
	if not me:
		return approver

	quoted_me = frappe.db.escape(me)
	return (
		f"(`tab{ASSIGNMENT}`.employee = {quoted_me}"
		f" or `tab{ASSIGNMENT}`.task_assignee = {quoted_me}"
		f" or exists (select 1 from `tabTask Assignment ToDo` r where r.parent = `tab{ASSIGNMENT}`.name"
		f" and r.parenttype = '{ASSIGNMENT}' and r.task_assignee = {quoted_me})"
		f" or {approver})"
	)
