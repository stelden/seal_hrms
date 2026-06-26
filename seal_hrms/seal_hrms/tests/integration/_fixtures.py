# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Shared fixture helpers for Leave Planning integration tests.

Per SEAL_DEV_RULES §1.9 — uses ORM (`frappe.new_doc().insert()` / `.submit()`)
so all hooks fire and the audit trail is real. No raw SQL inserts for fixture
creation. Realistic Kenyan names where employees are created.
"""

from datetime import timedelta

import frappe
from frappe.utils import getdate, today


COMPANY = "_Test Company"
HOLIDAY_LIST = "_Test Holiday List"


def ensure_plannable_leave_type(
	name: str,
	min_days_per_slot: int = 1,
	max_days_per_slot: int = 0,
	max_slots_per_plan: int = 0,
	min_application_advance_days: int = 0,
	max_leaves_allowed: int = 30,
) -> str:
	if frappe.db.exists("Leave Type", name):
		lt = frappe.get_doc("Leave Type", name)
	else:
		lt = frappe.new_doc("Leave Type")
		lt.leave_type_name = name
		lt.is_lwp = 0
		lt.is_compensatory = 0
		lt.is_encashable = 0
		lt.include_holiday = 1
	lt.custom_is_plannable = 1
	lt.custom_min_days_per_slot = min_days_per_slot
	lt.custom_max_days_per_slot = max_days_per_slot
	lt.custom_max_slots_per_plan = max_slots_per_plan
	lt.custom_min_application_advance_days = min_application_advance_days
	lt.max_leaves_allowed = max_leaves_allowed
	lt.save(ignore_permissions=True) if lt.name else lt.insert(ignore_permissions=True)
	# Bust the request-level cache that the LA on_submit hook reads via
	# frappe.get_cached_value — without this, a hook that fired earlier
	# with the pre-modification cache value will skip booking creation.
	frappe.clear_document_cache("Leave Type", lt.name)
	return lt.name


def ensure_leave_period(company: str = COMPANY) -> str:
	year = getdate().year
	year_start = f"{year}-01-01"
	year_end = f"{year}-12-31"
	existing = frappe.db.sql(
		"SELECT name FROM `tabLeave Period` "
		"WHERE company = %s AND from_date <= %s AND to_date >= %s LIMIT 1",
		(company, year_end, year_start),
	)
	if existing:
		name = existing[0][0]
		frappe.db.set_value("Leave Period", name, "is_active", 1, update_modified=False)
		return name
	period = frappe.new_doc("Leave Period")
	period.leave_period_name = f"Regression Period {year}"
	period.from_date = year_start
	period.to_date = year_end
	period.company = company
	period.is_active = 1
	period.insert(ignore_permissions=True)
	return period.name


def ensure_allocation(employee: str, leave_type: str, leave_period: str, days: int = 25) -> str:
	existing = frappe.db.get_value(
		"Leave Allocation",
		{"employee": employee, "leave_type": leave_type, "leave_period": leave_period, "docstatus": 1},
		"name",
	)
	if existing:
		return existing
	period = frappe.db.get_value("Leave Period", leave_period, ["from_date", "to_date"], as_dict=True)
	alloc = frappe.new_doc("Leave Allocation")
	alloc.employee = employee
	alloc.leave_type = leave_type
	alloc.leave_period = leave_period
	alloc.from_date = period.from_date
	alloc.to_date = period.to_date
	alloc.new_leaves_allocated = days
	alloc.insert(ignore_permissions=True)
	alloc.submit()
	return alloc.name


def create_open_cycle(company: str, leave_period: str, label_suffix: str = "") -> str:
	period = frappe.db.get_value("Leave Period", leave_period, ["from_date", "to_date"], as_dict=True)
	cycle = frappe.new_doc("Leave Planning Cycle")
	cycle.cycle_name = f"Regression Cycle {label_suffix or frappe.utils.now_datetime().strftime('%H%M%S%f')}"
	cycle.company = company
	cycle.leave_period = leave_period
	cycle.open_date = period.from_date
	cycle.submission_deadline = period.from_date
	cycle.scope_type = "All Employees"
	cycle.reminder_offsets_employee = "30,14,7,3,1"
	cycle.reminder_offsets_manager = "7,1"
	cycle.status = "Draft"
	cycle.insert(ignore_permissions=True)
	frappe.db.set_value("Leave Planning Cycle", cycle.name, "status", "Open", update_modified=False)
	return cycle.name


def add_cycle_member(cycle: str, employee: str) -> str:
	existing = frappe.db.get_value(
		"Leave Planning Cycle Member",
		{"cycle": cycle, "employee": employee},
		"name",
	)
	if existing:
		return existing
	member = frappe.new_doc("Leave Planning Cycle Member")
	member.cycle = cycle
	member.employee = employee
	member.plan_status = "Not Started"
	member.insert(ignore_permissions=True)
	return member.name


def create_leave_plan(cycle: str, employee: str, slots: list[dict]):
	plan = frappe.new_doc("Leave Plan")
	plan.planning_cycle = cycle
	plan.employee = employee
	for slot in slots:
		plan.append("leave_plan_slots", slot)
	plan.insert(ignore_permissions=True)
	return plan


def file_leave_application(employee: str, leave_type: str, from_date, to_date):
	la = frappe.new_doc("Leave Application")
	la.employee = employee
	la.leave_type = leave_type
	la.from_date = from_date
	la.to_date = to_date
	la.description = "regression test LA"
	la.status = "Approved"
	la.leave_approver = _approver_email(employee)
	la.insert(ignore_permissions=True)
	return la


def next_business_day(d):
	d = getdate(d)
	while d.weekday() >= 5:
		d += timedelta(days=1)
	return d


def _approver_email(employee: str) -> str:
	approver = frappe.db.get_value("Employee", employee, "leave_approver")
	if approver:
		return approver
	hr_users = frappe.get_all(
		"Has Role",
		filters={"role": "HR Manager", "parenttype": "User"},
		pluck="parent",
	)
	return hr_users[0] if hr_users else "Administrator"


def cleanup_plan(plan_name: str) -> None:
	if not frappe.db.exists("Leave Plan", plan_name):
		return
	doc = frappe.get_doc("Leave Plan", plan_name)
	if doc.docstatus == 1:
		try:
			doc.cancel()
		except Exception:
			pass
	frappe.delete_doc("Leave Plan", plan_name, force=1, ignore_permissions=True)


def cleanup_la(la_name: str) -> None:
	if not frappe.db.exists("Leave Application", la_name):
		# Even if the LA is gone, an orphan booking row may persist and corrupt
		# subsequent tests via the idempotency check in create_booking_for_la.
		_purge_bookings_for_la(la_name)
		return
	doc = frappe.get_doc("Leave Application", la_name)
	if doc.docstatus == 1:
		try:
			doc.cancel()
		except Exception:
			pass
	frappe.delete_doc("Leave Application", la_name, force=1, ignore_permissions=True)
	_purge_bookings_for_la(la_name)


def _purge_bookings_for_la(la_name: str) -> None:
	for booking in frappe.get_all(
		"Leave Plan Slot Booking",
		filters={"leave_application": la_name},
		pluck="name",
	):
		frappe.delete_doc("Leave Plan Slot Booking", booking, force=1, ignore_permissions=True)


def cleanup_booking(booking_name: str) -> None:
	if booking_name and frappe.db.exists("Leave Plan Slot Booking", booking_name):
		frappe.delete_doc("Leave Plan Slot Booking", booking_name, force=1, ignore_permissions=True)


def cleanup_cycle_and_member(cycle: str, member: str) -> None:
	if member and frappe.db.exists("Leave Planning Cycle Member", member):
		frappe.delete_doc("Leave Planning Cycle Member", member, force=1, ignore_permissions=True)
	if cycle and frappe.db.exists("Leave Planning Cycle", cycle):
		frappe.delete_doc("Leave Planning Cycle", cycle, force=1, ignore_permissions=True)


def wipe_employee_planning_state(employee: str, leave_type: str | None = None) -> None:
	"""Defensive cleanup: drop any submitted plans + active bookings for an employee.

	Use in setUp() of tests that depend on `find_matching_slot` finding a freshly-created
	plan as the unique match. Stale plans from previously-failed test runs survive
	tearDown failures and bias matching toward older rows.
	"""
	plan_filters = {"employee": employee}
	if leave_type:
		plan_names = [
			row.parent for row in frappe.db.sql(
				"""
				SELECT DISTINCT parent FROM `tabLeave Plan Slot`
				WHERE leave_type = %s AND parent IN (
					SELECT name FROM `tabLeave Plan` WHERE employee = %s
				)
				""",
				(leave_type, employee),
				as_dict=True,
			)
		]
	else:
		plan_names = frappe.get_all("Leave Plan", filters=plan_filters, pluck="name")

	for plan in plan_names:
		bookings = frappe.get_all(
			"Leave Plan Slot Booking",
			filters={"leave_plan": plan},
			pluck="name",
		)
		for booking in bookings:
			frappe.delete_doc("Leave Plan Slot Booking", booking, force=1, ignore_permissions=True)

		doc = frappe.get_doc("Leave Plan", plan)
		if doc.docstatus == 1:
			try:
				doc.flags.ignore_validate = True
				doc.cancel()
			except Exception:
				pass
		frappe.delete_doc("Leave Plan", plan, force=1, ignore_permissions=True)
