# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate


def execute():
	"""Backfill `planning_cycle` on existing Leave Plans created before Phase 2.

	Strategy: group existing plans by (company, leave_period), create one
	"Migrated" Leave Planning Cycle per group with status=Closed, then link
	each plan to its cycle. Roster materialisation is skipped (these plans
	are pre-existing — their owners already filed without going through a cycle).

	No-op fast path when no plans need backfilling.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.5
	"""
	if not frappe.db.has_column("Leave Plan", "planning_cycle"):
		return

	plans = frappe.db.sql(
		"""
		SELECT name, company, leave_period
		FROM `tabLeave Plan`
		WHERE docstatus != 2
		  AND (planning_cycle IS NULL OR planning_cycle = '')
		  AND leave_period IS NOT NULL AND leave_period != ''
		""",
		as_dict=True,
	)
	if not plans:
		print("[seal_hrms.v1_2] backfill_planning_cycle: 0 plans need backfilling — no-op")
		return

	cycle_cache: dict[tuple, str] = {}
	for plan in plans:
		key = (plan.company, plan.leave_period)
		if key not in cycle_cache:
			cycle_cache[key] = _ensure_cycle(plan.company, plan.leave_period)
		frappe.db.set_value(
			"Leave Plan", plan.name,
			"planning_cycle", cycle_cache[key],
			update_modified=False,
		)
		frappe.logger().info(
			f"[seal_hrms.v1_2] linked plan {plan.name} -> cycle {cycle_cache[key]}"
		)

	print(f"[seal_hrms.v1_2] backfill_planning_cycle: linked {len(plans)} plans to "
	      f"{len(cycle_cache)} migrated cycles")


def _ensure_cycle(company: str, leave_period: str) -> str:
	existing = frappe.db.exists(
		"Leave Planning Cycle",
		{"company": company, "leave_period": leave_period},
	)
	if existing:
		return existing

	period = frappe.db.get_value(
		"Leave Period", leave_period,
		["from_date", "to_date"], as_dict=True,
	)
	if not period:
		frappe.throw(f"[seal_hrms.v1_2] Leave Period {leave_period} missing")

	cycle = frappe.new_doc("Leave Planning Cycle")
	cycle.cycle_name = f"Migrated — {leave_period}"
	cycle.company = company
	cycle.leave_period = leave_period
	cycle.scope_type = "All Employees"
	cycle.open_date = period.from_date
	cycle.submission_deadline = period.from_date
	cycle.close_date = getdate()
	cycle.reminder_offsets_employee = "30,14,7,3,1"
	cycle.reminder_offsets_manager = "7,1"
	cycle.status = "Closed"
	cycle.flags.ignore_validate = True
	cycle.insert(ignore_permissions=True)
	frappe.logger().info(
		f"[seal_hrms.v1_2] created backfill cycle {cycle.name} for ({company}, {leave_period})"
	)
	return cycle.name
