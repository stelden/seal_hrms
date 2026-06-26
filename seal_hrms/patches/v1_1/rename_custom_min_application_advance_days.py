# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Migrate data from the old Leave Type field name to the new one.

	Old: `custom_min_leave_application_days_in_advance` (sat at top of form,
	     among native Frappe HR fields)
	New: `custom_min_application_advance_days` (lives in the new
	     "Application Timing" section per the Phase 1 layout)

	Runs in post_model_sync so the new Custom Field row + DB column have
	already been created by customizations sync. We then:

	  1. Copy data from the old column to the new column (where present).
	  2. Delete the orphan old Custom Field row.
	  3. Drop the orphan old DB column.

	Idempotent: skips cleanly on fresh installs (no old column) and on
	re-runs (already cleaned).

	Note: an earlier version of this patch tried to use
	frappe.model.utils.rename_field in pre_model_sync. That helper requires
	the new field to already exist in meta — which it doesn't until
	customizations sync runs — so it silently no-op'd. This patch supersedes
	that approach.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.3
	"""
	old = "custom_min_leave_application_days_in_advance"
	new = "custom_min_application_advance_days"
	dt = "Leave Type"

	has_old_col = frappe.db.has_column(dt, old)
	has_new_col = frappe.db.has_column(dt, new)
	old_cf_name = f"{dt}-{old}"
	old_cf_exists = frappe.db.exists("Custom Field", old_cf_name)

	if not has_old_col and not old_cf_exists:
		frappe.logger().info(f"[seal_hrms.v1_1] {old} already cleaned up — no-op")
		return

	if has_old_col and has_new_col:
		frappe.db.sql(
			f"UPDATE `tab{dt}` SET `{new}` = `{old}` "
			f"WHERE `{old}` IS NOT NULL AND `{old}` > 0 AND (`{new}` IS NULL OR `{new}` = 0)"
		)
		frappe.logger().info(f"[seal_hrms.v1_1] copied data {old} -> {new}")

	if old_cf_exists:
		frappe.delete_doc("Custom Field", old_cf_name, force=1, ignore_permissions=True)
		frappe.logger().info(f"[seal_hrms.v1_1] deleted Custom Field {old_cf_name}")

	if has_old_col:
		frappe.db.sql_ddl(f"ALTER TABLE `tab{dt}` DROP COLUMN `{old}`")
		frappe.logger().info(f"[seal_hrms.v1_1] dropped column {old} from tab{dt}")
