# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Drop the deprecated Leave Type custom field deferred from Phase 1.

	`custom_require_one_slot_min_days` was the old "at least one slot of leave
	type X must be ≥ N days" rule. Phase 2 replaces this semantically with
	per-slot `custom_min_days_per_slot` and `custom_max_days_per_slot` checks
	in the new Leave Plan controller.

	Phase 1 kept the field because the old `leave_plan.py` controller still
	read it. Phase 2 has rewritten the controller; the field is now safe to drop.

	Idempotent.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.4
	"""
	dt = "Leave Type"
	fieldname = "custom_require_one_slot_min_days"
	cf_name = f"{dt}-{fieldname}"

	if frappe.db.exists("Custom Field", cf_name):
		frappe.delete_doc("Custom Field", cf_name, force=1, ignore_permissions=True)
		frappe.logger().info(f"[seal_hrms.v1_2] deleted Custom Field {cf_name}")

	if frappe.db.has_column(dt, fieldname):
		frappe.db.sql_ddl(f"ALTER TABLE `tab{dt}` DROP COLUMN `{fieldname}`")
		frappe.logger().info(f"[seal_hrms.v1_2] dropped column {fieldname} from tab{dt}")
