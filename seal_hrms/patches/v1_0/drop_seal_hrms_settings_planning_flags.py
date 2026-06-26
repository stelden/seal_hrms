# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Phase 0 of Leave Planning redesign — drop two SEAL HRMS Settings fields.

	`enable_leave_planning` is replaced by per-Leave-Type `custom_is_plannable`
	(plannable types now require a Leave Plan; non-plannable types do not).

	`planning_submission_max_future_days` is replaced by the per-cycle
	`submission_deadline` introduced in Phase 1's Leave Planning Cycle doctype.

	The other planning-related Settings fields remain temporarily; Phase 1
	moves them to dedicated doctypes (Leave Concurrency Rule, Leave Planning
	Cycle).

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.2
	"""
	prior_values = {}
	for fieldname in ("enable_leave_planning", "planning_submission_max_future_days"):
		row = frappe.db.sql(
			"SELECT value FROM tabSingles WHERE doctype = %s AND field = %s",
			("SEAL HRMS Settings", fieldname),
		)
		prior_values[fieldname] = row[0][0] if row else None

	frappe.logger().info(
		f"[seal_hrms.v1_0] dropping SEAL HRMS Settings planning flags — "
		f"prior values: {prior_values}"
	)

	frappe.db.sql(
		"DELETE FROM tabSingles WHERE doctype = %s AND field IN (%s, %s)",
		("SEAL HRMS Settings", "enable_leave_planning", "planning_submission_max_future_days"),
	)
