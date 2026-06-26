# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Migration patch idempotency tests.

Each Phase 0/1/2 patch must be safely re-runnable: a second invocation
on a clean post-migration site must complete without error and without
changing observable state.

Per SEAL_DEV_RULES §3.11 — END-STATE migration audits are read-mostly and
report rather than auto-correct. These tests verify they don't re-correct.
"""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase


_PATCHES = [
	"seal_hrms.patches.v1_0.drop_seal_hrms_settings_planning_flags",
	"seal_hrms.patches.v1_1.rename_custom_min_application_advance_days",
	"seal_hrms.patches.v1_1.add_leave_plan_to_self_service_workspace",
	"seal_hrms.patches.v1_2.backfill_planning_cycle",
	"seal_hrms.patches.v1_2.backfill_workflow_state",
	"seal_hrms.patches.v1_2.migrate_slot_links_to_bookings",
	"seal_hrms.patches.v1_2.drop_custom_require_one_slot_min_days",
	"seal_hrms.patches.v1_2.audit_orphan_plans_and_log",
	"seal_hrms.patches.v1_3.create_workflow_leave_plan_approval",
]


class TestMigrationPatchesIdempotent(FrappeTestCase):

	def test_every_patch_re_runs_without_error(self):
		"""Every patch's execute() must complete cleanly when called a second time."""
		failures: list[str] = []
		for patch_path in _PATCHES:
			module = importlib.import_module(patch_path)
			try:
				module.execute()
				frappe.db.commit()
			except Exception as exc:
				failures.append(f"{patch_path}: {exc}")
				frappe.db.rollback()
		self.assertEqual(failures, [], f"patches not idempotent: {failures}")

	def test_workflow_patch_does_not_create_duplicate(self):
		"""The workflow patch should detect existing Workflow and skip silently."""
		from seal_hrms.patches.v1_3 import create_workflow_leave_plan_approval as p
		count_before = frappe.db.count("Workflow", {"name": "Leave Plan Approval"})
		self.assertEqual(count_before, 1, "expected one workflow record post-migration")
		p.execute()
		frappe.db.commit()
		count_after = frappe.db.count("Workflow", {"name": "Leave Plan Approval"})
		self.assertEqual(count_after, 1, "patch must not create a second workflow")

	def test_drop_custom_field_patch_is_safe_when_already_dropped(self):
		from seal_hrms.patches.v1_2 import drop_custom_require_one_slot_min_days as p
		exists_before = frappe.db.exists(
			"Custom Field", "Leave Type-custom_require_one_slot_min_days",
		)
		self.assertFalse(bool(exists_before), "field should already be dropped post-migration")
		p.execute()
		frappe.db.commit()
		exists_after = frappe.db.exists(
			"Custom Field", "Leave Type-custom_require_one_slot_min_days",
		)
		self.assertFalse(bool(exists_after))

	def test_workspace_patch_does_not_create_duplicate_link(self):
		from seal_hrms.patches.v1_1 import add_leave_plan_to_self_service_workspace as p
		count_before = frappe.db.count(
			"Workspace Link",
			{"parent": "Self Service", "link_to": "Leave Plan", "type": "Link"},
		)
		self.assertEqual(count_before, 1, "expected one Leave Plan link post-migration")
		p.execute()
		frappe.db.commit()
		count_after = frappe.db.count(
			"Workspace Link",
			{"parent": "Self Service", "link_to": "Leave Plan", "type": "Link"},
		)
		self.assertEqual(count_after, 1, "patch must not duplicate the Leave Plan link")
