# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Leave Plan operations exposed to the form/UI.

Per SPEC §7.2: cancellation gating (B1 rule), explicit cancel, status
recomputation, and HR-override slot cancel.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

from seal_hrms.seal_hrms.leave_planning.slots import compute_plan_status, compute_slot_status


@frappe.whitelist()
def can_cancel_plan(plan: str) -> dict:
	"""Per §1.11 dict-key follows the verb: returns {can_cancel, reason}.

	Cancellation is hard-gated (SPEC §9 / B1): the plan cannot be cancelled
	while any of its slots have Active bookings. The user must first cancel
	each linked Leave Application (which cancels its booking).
	"""
	if not frappe.db.exists("Leave Plan", plan):
		return {"can_cancel": False, "reason": _("Plan {0} not found").format(plan)}

	docstatus = frappe.db.get_value("Leave Plan", plan, "docstatus")
	if docstatus == 2:
		return {"can_cancel": False, "reason": _("Already cancelled")}

	active_bookings = frappe.db.sql(
		"""
		SELECT leave_application
		FROM `tabLeave Plan Slot Booking`
		WHERE leave_plan = %s AND status = 'Active'
		""",
		(plan,),
	)
	if active_bookings:
		la_list = ", ".join(b[0] for b in active_bookings[:5])
		more = f" (+{len(active_bookings) - 5} more)" if len(active_bookings) > 5 else ""
		return {
			"can_cancel": False,
			"reason": _(
				"{0} Leave Application(s) still draw from this plan: {1}{2}. "
				"Cancel those first."
			).format(len(active_bookings), la_list, more),
		}

	return {"can_cancel": True, "reason": ""}


@frappe.whitelist()
def cancel_plan(plan: str) -> str:
	"""Validates B1 (no active bookings), then cancels the Leave Plan.

	Idempotent on already-cancelled plans (returns immediately).
	"""
	gate = can_cancel_plan(plan)
	if not gate["can_cancel"]:
		frappe.throw(gate["reason"], title=_("Cannot Cancel Leave Plan"))

	docstatus = frappe.db.get_value("Leave Plan", plan, "docstatus")
	if docstatus == 2:
		return plan

	doc = frappe.get_doc("Leave Plan", plan)
	doc.cancel()
	return plan


@frappe.whitelist()
def recompute_plan_status(plan: str) -> str:
	"""Recompute the Leave Plan's stored status from current bookings.

	Writes via db.set_value with update_modified=False per §2.10 so the
	plan's modified timestamp isn't bumped by mechanical recomputation.
	Also refreshes each slot's stored slot_status field.
	"""
	if not frappe.db.exists("Leave Plan", plan):
		frappe.throw(_("Plan {0} not found").format(plan))

	slot_rows = frappe.db.sql(
		"SELECT name FROM `tabLeave Plan Slot` WHERE parent = %s",
		(plan,),
	)
	for (slot_name,) in slot_rows:
		new_status = compute_slot_status(plan, slot_name)
		frappe.db.set_value(
			"Leave Plan Slot", slot_name, "slot_status", new_status, update_modified=False,
		)

	new_plan_status = compute_plan_status(plan)
	frappe.db.set_value(
		"Leave Plan", plan, "status", new_plan_status, update_modified=False,
	)
	return new_plan_status


@frappe.whitelist()
def cancel_slot(plan: str, slot_row_name: str) -> str:
	"""HR-override action: mark a single slot Cancelled.

	Cancels any active bookings against it (each booking's LA must already be
	cancelled by the caller — we don't cascade LA cancellation). Then refreshes
	the plan's status.
	"""
	user_roles = set(frappe.get_roles(frappe.session.user))
	if "HR Manager" not in user_roles and "System Manager" not in user_roles:
		frappe.throw(_("Only HR Manager or System Manager can cancel a planned slot."))

	slot = frappe.db.get_value(
		"Leave Plan Slot", slot_row_name,
		["parent", "slot_status"], as_dict=True,
	)
	if not slot or slot.parent != plan:
		frappe.throw(_("Slot {0} not found in plan {1}").format(slot_row_name, plan))
	if slot.slot_status == "Cancelled":
		return slot_row_name

	frappe.db.get_value("Leave Plan", plan, "name", for_update=True)

	active_bookings = frappe.db.sql(
		"""
		SELECT name, leave_application FROM `tabLeave Plan Slot Booking`
		WHERE leave_plan = %s AND slot = %s AND status = 'Active'
		""",
		(plan, slot_row_name),
		as_dict=True,
	)
	for b in active_bookings:
		la_docstatus = frappe.db.get_value("Leave Application", b.leave_application, "docstatus")
		if la_docstatus == 1:
			frappe.throw(_(
				"Cannot cancel slot — Leave Application {0} is still submitted. "
				"Cancel the LA first."
			).format(b.leave_application))
		frappe.db.set_value(
			"Leave Plan Slot Booking", b.name,
			{"status": "Cancelled", "cancelled_at": now_datetime()},
			update_modified=False,
		)

	frappe.db.set_value(
		"Leave Plan Slot", slot_row_name, "slot_status", "Cancelled", update_modified=False,
	)

	new_plan_status = compute_plan_status(plan)
	frappe.db.set_value(
		"Leave Plan", plan, "status", new_plan_status, update_modified=False,
	)
	return slot_row_name
