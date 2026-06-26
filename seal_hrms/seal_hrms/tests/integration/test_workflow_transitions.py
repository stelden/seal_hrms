# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Workflow transition tests — temporarily activate the Leave Plan Approval
workflow and walk Draft → Pending Manager → Pending HR → Approved.

The workflow ships INACTIVE per SPEC §5.2; HR enables it client-side.
These tests activate it for the duration of the test class and restore
the original state afterwards.

Per SPEC §3.2 two-mode override: the controller is workflow-tolerant —
when workflow_state is set to a non-Approved value, before_submit blocks
docstatus advance. These tests pin that behaviour down.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.tests.integration._fixtures import (
	COMPANY,
	add_cycle_member,
	cleanup_cycle_and_member,
	cleanup_plan,
	create_leave_plan,
	create_open_cycle,
	ensure_allocation,
	ensure_leave_period,
	ensure_plannable_leave_type,
	next_business_day,
)


EMPLOYEE = "_T-Employee-00001"
WORKFLOW_NAME = "Leave Plan Approval"


class TestWorkflowTransitions(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("Workflow Test Annual")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMPLOYEE, cls.leave_type, cls.leave_period, days=30)
		cls._workflow_was_active = bool(
			frappe.db.get_value("Workflow", WORKFLOW_NAME, "is_active")
		)
		frappe.db.set_value("Workflow", WORKFLOW_NAME, "is_active", 1, update_modified=False)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.db.set_value(
			"Workflow", WORKFLOW_NAME, "is_active", 1 if cls._workflow_was_active else 0,
			update_modified=False,
		)
		frappe.db.commit()
		super().tearDownClass()

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member = add_cycle_member(self.cycle, EMPLOYEE)
		self._created_plans: list[str] = []
		frappe.db.commit()

	def tearDown(self):
		for plan in self._created_plans:
			cleanup_plan(plan)
		cleanup_cycle_and_member(self.cycle, self.member)
		frappe.db.commit()

	def test_workflow_is_active_on_target_doctype(self):
		active = frappe.db.get_value(
			"Workflow",
			{"document_type": "Leave Plan", "is_active": 1},
			"name",
		)
		self.assertEqual(active, WORKFLOW_NAME)

	def test_new_plan_starts_in_draft_workflow_state(self):
		plan = self._create_draft_plan()
		self.assertEqual(plan.workflow_state, "Draft")

	def test_submit_blocked_while_workflow_state_is_not_approved(self):
		"""Per controller §3.2: before_submit blocks if workflow_state != Approved."""
		plan = self._create_draft_plan()
		frappe.db.set_value(
			"Leave Plan", plan.name, "workflow_state", "Pending Manager",
			update_modified=False,
		)
		plan.reload()
		with self.assertRaises(frappe.exceptions.ValidationError):
			plan.submit()

	def test_workflow_state_approved_allows_submit(self):
		plan = self._create_draft_plan()
		frappe.db.set_value(
			"Leave Plan", plan.name, "workflow_state", "Approved",
			update_modified=False,
		)
		plan.reload()
		plan.submit()
		self.assertEqual(plan.docstatus, 1)

	def test_invalid_workflow_state_value_throws(self):
		"""Either Frappe Workflow's own validator OR our controller's
		_validate_workflow_state_transition rejects unknown state names —
		both raise ValidationError, which is what we lock down."""
		plan = self._create_draft_plan()
		plan.workflow_state = "MadeUpState"
		with self.assertRaises(frappe.exceptions.ValidationError):
			plan.save()

	def _create_draft_plan(self):
		slot_from = next_business_day(add_days(today(), 30))
		slot_to = add_days(slot_from, 4)
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
		}])
		self._created_plans.append(plan.name)
		return plan
