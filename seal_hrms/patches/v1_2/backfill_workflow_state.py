# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Stamp workflow_state on existing Leave Plans based on docstatus.

	Maps:
	  docstatus 0 (Draft)     -> workflow_state Draft
	  docstatus 1 (Submitted) -> workflow_state Approved
	  docstatus 2 (Cancelled) -> workflow_state Cancelled

	Idempotent: only sets workflow_state where it is currently NULL or empty.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.6
	"""
	if not frappe.db.has_column("Leave Plan", "workflow_state"):
		return

	mapping = {0: "Draft", 1: "Approved", 2: "Cancelled"}
	total = 0
	for ds, state in mapping.items():
		count = frappe.db.sql(
			"""
			UPDATE `tabLeave Plan`
			SET workflow_state = %s
			WHERE docstatus = %s
			  AND (workflow_state IS NULL OR workflow_state = '')
			""",
			(state, ds),
		)
		n = frappe.db.sql(
			"SELECT COUNT(*) FROM `tabLeave Plan` WHERE docstatus = %s AND workflow_state = %s",
			(ds, state),
		)[0][0]
		total += n
		frappe.logger().info(
			f"[seal_hrms.v1_2] backfill_workflow_state: docstatus={ds} -> '{state}' "
			f"({n} rows now in this state)"
		)
	print(f"[seal_hrms.v1_2] backfill_workflow_state: {total} plans normalised")
