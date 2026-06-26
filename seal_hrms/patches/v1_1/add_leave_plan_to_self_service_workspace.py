# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Add the Leave Plan link to the existing Self Service workspace.

	Frappe syncs Workspace JSONs only on first install, not on subsequent
	`bench migrate` runs. Editing `workspace/self_service/self_service.json`
	covers fresh installs; this patch covers existing installs.

	Idempotent: skips cleanly if the link is already present or the
	workspace doesn't exist.

	The link is positioned immediately after "Leave Application" within the
	"Leave & Attendance" card.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3 (Phase 1)
	"""
	workspace_name = "Self Service"
	if not frappe.db.exists("Workspace", workspace_name):
		frappe.logger().info(f"[seal_hrms.v1_1] {workspace_name} workspace not present — skipping")
		return

	already_present = frappe.db.exists(
		"Workspace Link",
		{"parent": workspace_name, "link_to": "Leave Plan", "type": "Link"},
	)
	if already_present:
		return

	leave_app_idx = frappe.db.get_value(
		"Workspace Link",
		{"parent": workspace_name, "link_to": "Leave Application", "type": "Link"},
		"idx",
	)
	if not leave_app_idx:
		frappe.logger().warning(
			f"[seal_hrms.v1_1] Leave Application link missing from {workspace_name}; "
			f"cannot position Leave Plan — skipping"
		)
		return

	target_idx = leave_app_idx + 1

	frappe.db.sql(
		"UPDATE `tabWorkspace Link` SET idx = idx + 1 WHERE parent = %s AND idx >= %s",
		(workspace_name, target_idx),
	)

	new_link = frappe.get_doc({
		"doctype": "Workspace Link",
		"parent": workspace_name,
		"parenttype": "Workspace",
		"parentfield": "links",
		"label": "Leave Plan",
		"link_to": "Leave Plan",
		"link_type": "DocType",
		"type": "Link",
		"hidden": 0,
		"is_query_report": 0,
		"onboard": 0,
		"idx": target_idx,
	})
	new_link.insert(ignore_permissions=True)

	frappe.clear_cache(doctype="Workspace")
	frappe.logger().info(
		f"[seal_hrms.v1_1] inserted Leave Plan link at idx {target_idx} "
		f"in {workspace_name} workspace"
	)
