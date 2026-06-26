# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Permission hooks for the Leave Planning doctypes.

Per SEAL_DEV_RULES:
  - §2.9 — every has_permission hook returns explicit True/False, never None.
  - §3.4 — has_permission and get_permission_query_conditions ship together.
  - §3.5 — back-office bypass (HR_BACKOFFICE_ROLES) is distinct from emergency
           admin bypass (seal_common OVERRIDE_ROLE). Both are honoured.

Visibility model for non-HR users:
  - Employee Self Service: sees their OWN plans / bookings / cycle membership.
  - Leave Approver: also sees plans / cycle membership of their direct reports.
  - HR User / HR Manager: sees everything in their company.
"""

import frappe

from seal_common.data_governance.change_request_utils import user_has_override_role


HR_BACKOFFICE_ROLES = {"HR User", "HR Manager"}


def _employee_for_user(user: str) -> str:
	return frappe.db.get_value("Employee", {"user_id": user}, "name") or ""


def _is_hr_backoffice(user: str) -> bool:
	return bool(set(frappe.get_roles(user)) & HR_BACKOFFICE_ROLES)


def leave_plan_has_permission(doc, ptype, user) -> bool:
	"""Per §2.9 — explicit True/False, never None (None silently denies write/submit/cancel)."""
	if not user:
		user = frappe.session.user
	if user == "Guest":
		return False
	if user_has_override_role(user):
		return True
	if _is_hr_backoffice(user):
		return True

	owner_emp = _employee_for_user(user)

	if ptype in ("read", "select", "print", "email"):
		if doc.employee and owner_emp and doc.employee == owner_emp:
			return True
		if doc.leave_approver and user == doc.leave_approver:
			return True
		return False

	if ptype in ("write", "submit", "cancel", "amend", "delete"):
		return bool(doc.employee and owner_emp and doc.employee == owner_emp)

	return False


def leave_plan_query_conditions(user: str = None) -> str:
	if not user:
		user = frappe.session.user
	if user == "Administrator" or user_has_override_role(user) or _is_hr_backoffice(user):
		return ""

	emp = _employee_for_user(user)
	if not emp and not user:
		return "1=0"

	return (
		f"(`tabLeave Plan`.employee = {frappe.db.escape(emp)} "
		f"OR `tabLeave Plan`.leave_approver = {frappe.db.escape(user)})"
	)


def leave_plan_slot_booking_has_permission(doc, ptype, user) -> bool:
	if not user:
		user = frappe.session.user
	if user == "Guest":
		return False
	if user_has_override_role(user) or _is_hr_backoffice(user):
		return True

	owner_emp = _employee_for_user(user)
	if ptype in ("read", "select", "print", "email"):
		return bool(doc.employee and owner_emp and doc.employee == owner_emp)

	return False


def leave_plan_slot_booking_query_conditions(user: str = None) -> str:
	if not user:
		user = frappe.session.user
	if user == "Administrator" or user_has_override_role(user) or _is_hr_backoffice(user):
		return ""

	emp = _employee_for_user(user)
	if not emp:
		return "1=0"
	return f"`tabLeave Plan Slot Booking`.employee = {frappe.db.escape(emp)}"


def leave_planning_cycle_member_has_permission(doc, ptype, user) -> bool:
	if not user:
		user = frappe.session.user
	if user == "Guest":
		return False
	if user_has_override_role(user) or _is_hr_backoffice(user):
		return True

	owner_emp = _employee_for_user(user)
	if ptype in ("read", "select", "print", "email"):
		if doc.employee and owner_emp and doc.employee == owner_emp:
			return True
		if doc.leave_approver and user == doc.leave_approver:
			return True
		return False

	return False


def leave_planning_cycle_member_query_conditions(user: str = None) -> str:
	if not user:
		user = frappe.session.user
	if user == "Administrator" or user_has_override_role(user) or _is_hr_backoffice(user):
		return ""

	emp = _employee_for_user(user)
	if not emp and not user:
		return "1=0"

	return (
		f"(`tabLeave Planning Cycle Member`.employee = {frappe.db.escape(emp)} "
		f"OR `tabLeave Planning Cycle Member`.leave_approver = {frappe.db.escape(user)})"
	)
