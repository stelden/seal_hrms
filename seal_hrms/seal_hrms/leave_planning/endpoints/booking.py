# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Leave Plan Slot Booking lifecycle.

The booking layer is owned by Leave Application hooks, NOT by users.
Bookings are the single source of truth for "this LA drew N days from this slot."

Per SPEC §7.3, this module exposes three endpoints:
  - find_matching_slot   — read-only, returns the slot an LA would draw from
  - create_booking_for_la — called from LA on_submit, pessimistic lock per §3.3
  - cancel_booking_for_la — called from LA on_cancel, idempotent
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from seal_hrms.seal_hrms.leave_planning.slots import compute_plan_status


def find_matching_slot(employee: str, leave_type: str, from_date, to_date) -> dict:
	"""Find a slot in a submitted plan that can absorb this LA.

	Returns a dict: {plan, slot_row_name, slot_from, slot_to, remaining_days, reason}.
	On failure, plan is None and reason explains why.
	"""
	from_d, to_d = getdate(from_date), getdate(to_date)

	plans = frappe.db.sql(
		"""
		SELECT lp.name AS plan_name, lp.leave_period
		FROM `tabLeave Plan` lp
		JOIN `tabLeave Period` lpd ON lpd.name = lp.leave_period
		WHERE lp.employee = %(employee)s
		  AND lp.docstatus = 1
		  AND lpd.from_date <= %(from_d)s
		  AND lpd.to_date >= %(to_d)s
		ORDER BY lp.modified DESC
		""",
		{"employee": employee, "from_d": from_d, "to_d": to_d},
		as_dict=True,
	)
	if not plans:
		return {
			"plan": None, "slot_row_name": None,
			"reason": _("No submitted Leave Plan covers the dates {0} to {1} for {2}").format(
				from_date, to_date, employee
			),
		}

	candidate_slots = []
	for p in plans:
		slots = frappe.db.sql(
			"""
			SELECT name, leave_type, from_date, to_date, days, slot_status
			FROM `tabLeave Plan Slot`
			WHERE parent = %(parent)s
			  AND leave_type = %(lt)s
			  AND from_date <= %(from_d)s
			  AND to_date >= %(to_d)s
			  AND slot_status != 'Cancelled'
			ORDER BY from_date ASC
			""",
			{"parent": p.plan_name, "lt": leave_type, "from_d": from_d, "to_d": to_d},
			as_dict=True,
		)
		for s in slots:
			candidate_slots.append((p.plan_name, s))

	if not candidate_slots:
		return {
			"plan": None, "slot_row_name": None,
			"reason": _("No slot of type {0} covers {1} to {2} in any submitted Leave Plan").format(
				leave_type, from_date, to_date
			),
		}

	la_days_request = _calculate_la_days(employee, from_d, to_d)

	for plan_name, slot in candidate_slots:
		booked_active = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(days), 0)
			FROM `tabLeave Plan Slot Booking`
			WHERE leave_plan = %(plan)s AND slot = %(slot)s AND status = 'Active'
			""",
			{"plan": plan_name, "slot": slot.name},
		)[0][0]
		remaining = flt(slot.days or 0) - flt(booked_active or 0)
		if remaining + 1e-6 < la_days_request:
			continue

		conflict = frappe.db.sql(
			"""
			SELECT name FROM `tabLeave Plan Slot Booking`
			WHERE leave_plan = %(plan)s AND slot = %(slot)s AND status = 'Active'
			  AND from_date <= %(to_d)s AND to_date >= %(from_d)s
			LIMIT 1
			""",
			{"plan": plan_name, "slot": slot.name, "from_d": from_d, "to_d": to_d},
		)
		if conflict:
			continue

		return {
			"plan": plan_name,
			"slot_row_name": slot.name,
			"slot_from": slot.from_date,
			"slot_to": slot.to_date,
			"remaining_days": remaining,
			"reason": "",
		}

	return {
		"plan": None, "slot_row_name": None,
		"reason": _(
			"Slots of type {0} exist for {1}-{2} but all are at capacity or "
			"conflict with another booking. Cancel a conflicting Leave Application "
			"or reduce the requested range."
		).format(leave_type, from_date, to_date),
	}


def create_booking_for_la(la_name: str) -> str | None:
	"""Create a Leave Plan Slot Booking for the given Leave Application.

	Called from LA on_submit. Idempotent: if a booking already exists for this
	LA, no-op. Acquires a pessimistic lock on the plan row before re-running
	find_matching_slot to defeat races (per §3.3).

	Returns the booking name, or None if no slot matched (caller should already
	have validated this in LA validate; we re-check here defensively).
	"""
	existing = frappe.db.get_value("Leave Plan Slot Booking", {"leave_application": la_name}, "name")
	if existing:
		frappe.logger().info(f"[seal_hrms] booking {existing} already exists for LA {la_name}; skipping")
		return existing

	la = frappe.db.get_value(
		"Leave Application", la_name,
		["employee", "leave_type", "from_date", "to_date", "total_leave_days"],
		as_dict=True,
	)
	if not la:
		frappe.log_error(
			title="[seal_hrms] booking attempted for missing LA",
			message=f"Leave Application {la_name} not found",
		)
		return None

	match = find_matching_slot(la.employee, la.leave_type, la.from_date, la.to_date)
	if not match["plan"]:
		frappe.log_error(
			title="[seal_hrms] booking failed: no matching slot",
			message=f"Leave Application {la_name}: {match['reason']}",
		)
		return None

	frappe.db.get_value("Leave Plan", match["plan"], "name", for_update=True)

	match_locked = find_matching_slot(la.employee, la.leave_type, la.from_date, la.to_date)
	if not match_locked["plan"] or match_locked["slot_row_name"] != match["slot_row_name"]:
		frappe.log_error(
			title="[seal_hrms] booking race lost",
			message=f"LA {la_name}: candidate slot changed under lock — {match_locked['reason']}",
		)
		return None

	booking = frappe.get_doc({
		"doctype": "Leave Plan Slot Booking",
		"leave_plan": match_locked["plan"],
		"slot": match_locked["slot_row_name"],
		"leave_application": la_name,
		"employee": la.employee,
		"from_date": la.from_date,
		"to_date": la.to_date,
		"days": flt(la.total_leave_days or 0),
		"status": "Active",
	})
	booking.insert(ignore_permissions=True)

	_propagate_status(match_locked["plan"], match_locked["slot_row_name"])

	return booking.name


def cancel_booking_for_la(la_name: str) -> bool:
	"""Cancel the booking attached to this LA.

	Called from LA on_cancel. Idempotent — safe to call when no booking
	exists (LA was for a non-plannable type, or already cancelled).
	"""
	booking_name = frappe.db.get_value(
		"Leave Plan Slot Booking",
		{"leave_application": la_name, "status": "Active"},
		"name",
	)
	if not booking_name:
		return False

	booking = frappe.db.get_value(
		"Leave Plan Slot Booking", booking_name,
		["leave_plan", "slot"], as_dict=True,
	)

	frappe.db.get_value("Leave Plan", booking.leave_plan, "name", for_update=True)

	frappe.db.set_value(
		"Leave Plan Slot Booking", booking_name,
		{"status": "Cancelled", "cancelled_at": now_datetime()},
		update_modified=False,
	)

	_propagate_status(booking.leave_plan, booking.slot)
	return True


def _calculate_la_days(employee: str, from_date, to_date) -> float:
	"""Working days for a candidate LA, mirroring HRMS' own day calculation."""
	from seal_hrms.seal_hrms.leave_planning.slots import calculate_slot_days
	return float(calculate_slot_days(employee, from_date, to_date))


def _propagate_status(plan_name: str, slot_row_name: str) -> None:
	"""Refresh the slot's stored slot_status and the plan's stored status from bookings.

	Both writes use update_modified=False per §2.10 so the plan/slot's modified
	timestamp isn't bumped by mechanical recomputation.
	"""
	from seal_hrms.seal_hrms.leave_planning.slots import compute_slot_status

	new_slot_status = compute_slot_status(plan_name, slot_row_name)
	frappe.db.set_value(
		"Leave Plan Slot", slot_row_name,
		"slot_status", new_slot_status,
		update_modified=False,
	)

	new_plan_status = compute_plan_status(plan_name)
	frappe.db.set_value(
		"Leave Plan", plan_name,
		"status", new_plan_status,
		update_modified=False,
	)
