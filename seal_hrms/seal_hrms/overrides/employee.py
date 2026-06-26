# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Employee on_update — refresh denormalised fields on dependent Leave Planning records.

Per SPEC §8.5: when an employee's department / branch / designation /
leave_approver changes, propagate to:

- Leave Planning Cycle Member rows where the cycle is still Open
- Non-cancelled Leave Plan rows for this employee

Writes use update_modified=False per §2.10 — these are mechanical syncs,
not user edits, so they shouldn't bump the modified timestamp.
"""

import frappe


_TRACKED_FIELDS = ("department", "branch", "designation", "leave_approver")


def on_update(doc, method=None):
	if not any(doc.has_value_changed(f) for f in _TRACKED_FIELDS):
		return

	updates = {f: doc.get(f) for f in _TRACKED_FIELDS if doc.has_value_changed(f)}

	_propagate_to_open_cycle_members(doc.name, updates)
	_propagate_to_active_leave_plans(doc.name, updates)


def _propagate_to_open_cycle_members(employee: str, updates: dict) -> None:
	members = frappe.db.sql(
		"""
		SELECT m.name FROM `tabLeave Planning Cycle Member` m
		JOIN `tabLeave Planning Cycle` c ON c.name = m.cycle
		WHERE m.employee = %s AND c.status = 'Open'
		""",
		(employee,),
	)
	for (member_name,) in members:
		frappe.db.set_value(
			"Leave Planning Cycle Member", member_name,
			updates, update_modified=False,
		)


def _propagate_to_active_leave_plans(employee: str, updates: dict) -> None:
	plans = frappe.get_all(
		"Leave Plan",
		filters={"employee": employee, "docstatus": ["!=", 2]},
		pluck="name",
	)
	for plan_name in plans:
		frappe.db.set_value(
			"Leave Plan", plan_name,
			updates, update_modified=False,
		)
