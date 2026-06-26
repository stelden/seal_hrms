# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Helpers that compute slot day counts and slot/plan booking status.

These are pure read functions — no side effects, no database writes — and may
be called from validate(), from endpoints, and from JS via @whitelist.
"""

from datetime import timedelta

import frappe
from frappe.utils import getdate


@frappe.whitelist()
def calculate_slot_days(employee: str, from_date, to_date) -> int:
	"""Working days between from_date and to_date inclusive, excluding the
	employee's holidays. Used by Leave Plan JS as the user enters dates.
	"""
	from hrms.hr.utils import get_holidays_for_employee

	from_d, to_d = getdate(from_date), getdate(to_date)
	if from_d > to_d:
		return 0

	total_days = (to_d - from_d).days + 1
	holidays = get_holidays_for_employee(employee, from_d, to_d) or []
	holiday_dates = {getdate(h["holiday_date"]) for h in holidays}

	return sum(
		1 for i in range(total_days)
		if (from_d + timedelta(days=i)) not in holiday_dates
	)


def compute_slot_status(plan_name: str, slot_row_name: str) -> str:
	"""Derive a slot's status from its bookings.

	Returns: Open / Partially Booked / Fully Booked / Cancelled.
	The Cancelled state is sticky (HR override action) — once stamped,
	this function preserves it regardless of booking activity.
	"""
	row = frappe.db.get_value(
		"Leave Plan Slot",
		slot_row_name,
		["days", "slot_status"],
		as_dict=True,
	)
	if not row:
		return "Open"
	if row.slot_status == "Cancelled":
		return "Cancelled"

	slot_days = float(row.days or 0)
	if slot_days <= 0:
		return "Open"

	booked = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(days), 0) FROM `tabLeave Plan Slot Booking`
		WHERE leave_plan = %(plan)s AND slot = %(slot)s AND status = 'Active'
		""",
		{"plan": plan_name, "slot": slot_row_name},
	)[0][0]
	booked_days = float(booked or 0)

	if booked_days <= 0:
		return "Open"
	if booked_days + 1e-6 >= slot_days:
		return "Fully Booked"
	return "Partially Booked"


def compute_plan_status(plan_name: str) -> str:
	"""Derive a Leave Plan's overall status from its slots.

	Not Applied: every active slot is Open.
	Partially Applied: at least one slot has bookings, not all are Fully Booked.
	Fully Applied: every active slot is Fully Booked.
	Cancelled slots are excluded from the active-slot accounting; if every
	slot is Cancelled the plan reports Not Applied.
	"""
	rows = frappe.db.sql(
		"""
		SELECT name, days, slot_status FROM `tabLeave Plan Slot`
		WHERE parent = %s
		""",
		(plan_name,),
		as_dict=True,
	)
	if not rows:
		return "Not Applied"

	statuses = [compute_slot_status(plan_name, r.name) for r in rows]
	active = [s for s in statuses if s != "Cancelled"]
	if not active:
		return "Not Applied"

	if all(s == "Open" for s in active):
		return "Not Applied"
	if all(s == "Fully Booked" for s in active):
		return "Fully Applied"
	return "Partially Applied"
