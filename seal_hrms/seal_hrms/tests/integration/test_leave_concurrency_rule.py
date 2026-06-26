# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Integration tests for the Leave Concurrency Rule evaluator.

Per SPEC §4.6 — rules cap concurrent planned absences in a scope. These
tests exercise the algorithm end-to-end: a real rule, real plans, real
overlap evaluation.
"""

from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from seal_hrms.seal_hrms.leave_planning.concurrency import evaluate_slot

from seal_hrms.seal_hrms.tests.integration._fixtures import (
	COMPANY,
	add_cycle_member,
	cleanup_cycle_and_member,
	cleanup_la,
	cleanup_plan,
	create_leave_plan,
	create_open_cycle,
	ensure_allocation,
	ensure_leave_period,
	ensure_plannable_leave_type,
	next_business_day,
)


EMP_DEPT1_A = "_T-Employee-00002"
EMP_DEPT1_B = "_T-Employee-00003"
EMP_DEPT2 = "_T-Employee-00001"


class TestLeaveConcurrencyRule(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("Concurrency Test Annual")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMP_DEPT1_A, cls.leave_type, cls.leave_period, days=30)
		ensure_allocation(EMP_DEPT1_B, cls.leave_type, cls.leave_period, days=30)
		ensure_allocation(EMP_DEPT2, cls.leave_type, cls.leave_period, days=30)

		cls.dept_a = frappe.db.get_value("Employee", EMP_DEPT1_A, "department")
		cls.dept_other = frappe.db.get_value("Employee", EMP_DEPT2, "department")
		cls.created_rules: list[str] = []

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member_a = add_cycle_member(self.cycle, EMP_DEPT1_A)
		self.member_b = add_cycle_member(self.cycle, EMP_DEPT1_B)
		self.member_c = add_cycle_member(self.cycle, EMP_DEPT2)
		self._created_plans: list[str] = []
		self._created_las: list[str] = []
		frappe.db.commit()

	def tearDown(self):
		for la in self._created_las:
			cleanup_la(la)
		for plan in self._created_plans:
			cleanup_plan(plan)
		for member in (self.member_a, self.member_b, self.member_c):
			if member and frappe.db.exists("Leave Planning Cycle Member", member):
				frappe.delete_doc("Leave Planning Cycle Member", member, force=1, ignore_permissions=True)
		if self.cycle and frappe.db.exists("Leave Planning Cycle", self.cycle):
			frappe.delete_doc("Leave Planning Cycle", self.cycle, force=1, ignore_permissions=True)
		for rule in self.created_rules:
			if frappe.db.exists("Leave Concurrency Rule", rule):
				frappe.delete_doc("Leave Concurrency Rule", rule, force=1, ignore_permissions=True)
		self.created_rules.clear()
		frappe.db.commit()

	def test_department_scope_absolute_cap_blocks_second_overlap(self):
		self._create_dept_rule(self.dept_a, max_absolute=1)

		plan_a = self._submit_plan(EMP_DEPT1_A, days_offset=30, length=5)
		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			self._submit_plan(EMP_DEPT1_B, days_offset=31, length=3)
		self.assertIn("concurrency cap", str(ctx.exception).lower())

	def test_department_scope_allows_non_overlapping_slots(self):
		self._create_dept_rule(self.dept_a, max_absolute=1)
		self._submit_plan(EMP_DEPT1_A, days_offset=30, length=5)
		self._submit_plan(EMP_DEPT1_B, days_offset=60, length=5)

	def test_different_department_bypasses_dept_scoped_rule(self):
		self._create_dept_rule(self.dept_a, max_absolute=1)
		self._submit_plan(EMP_DEPT1_A, days_offset=30, length=5)
		self._submit_plan(EMP_DEPT2, days_offset=30, length=5)

	def test_disabled_rule_does_not_apply(self):
		rule_name = self._create_dept_rule(self.dept_a, max_absolute=1)
		frappe.db.set_value("Leave Concurrency Rule", rule_name, "enabled", 0)
		self._submit_plan(EMP_DEPT1_A, days_offset=30, length=5)
		self._submit_plan(EMP_DEPT1_B, days_offset=30, length=5)

	def test_rule_outside_effective_window_does_not_apply(self):
		past_from = add_days(today(), -365)
		past_to = add_days(today(), -1)
		self._create_dept_rule(
			self.dept_a, max_absolute=1,
			effective_from=past_from, effective_to=past_to,
		)
		self._submit_plan(EMP_DEPT1_A, days_offset=30, length=5)
		self._submit_plan(EMP_DEPT1_B, days_offset=30, length=5)

	def test_evaluate_slot_returns_violation_dict_with_expected_keys(self):
		rule_name = self._create_dept_rule(self.dept_a, max_absolute=1)
		plan_a = self._submit_plan(EMP_DEPT1_A, days_offset=30, length=5)

		from_d = next_business_day(add_days(today(), 31))
		to_d = add_days(from_d, 2)
		fake_slot = frappe._dict(
			leave_type=self.leave_type, from_date=from_d, to_date=to_d, days=3, name="ephemeral",
		)
		fake_plan = frappe._dict(
			company=COMPANY, employee=EMP_DEPT1_B, name="ephemeral-plan",
		)
		violations = evaluate_slot(fake_slot, fake_plan)
		self.assertEqual(len(violations), 1)
		v = violations[0]
		for key in ("rule", "rule_name", "scope_label", "current", "proposed", "max", "message"):
			self.assertIn(key, v)
		self.assertEqual(v["rule"], rule_name)
		self.assertEqual(v["max"], 1)

	def _create_dept_rule(
		self, department: str, max_absolute: int = 1, max_percent: float = 0,
		effective_from=None, effective_to=None,
	) -> str:
		import time
		rule_name = f"Test Rule {department[:20]} {self._testMethodName[:30]} {int(time.time() * 1000) % 1000000}"
		rule = frappe.new_doc("Leave Concurrency Rule")
		rule.rule_name = rule_name
		rule.company = COMPANY
		rule.enabled = 1
		rule.priority = 100
		rule.scope_type = "Department"
		rule.department = department
		rule.max_concurrent_absolute = max_absolute
		rule.max_concurrent_percent = max_percent
		rule.aggregation = "Any Day"
		rule.effective_from = effective_from or self._period_start()
		rule.effective_to = effective_to
		rule.insert(ignore_permissions=True)
		self.created_rules.append(rule.name)
		return rule.name

	def _period_start(self):
		return frappe.db.get_value("Leave Period", self.leave_period, "from_date")

	def _submit_plan(self, employee: str, days_offset: int, length: int):
		slot_from = next_business_day(add_days(today(), days_offset))
		slot_to = add_days(slot_from, length - 1)
		plan = create_leave_plan(self.cycle, employee, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
			"description": "concurrency test",
		}])
		self._created_plans.append(plan.name)
		plan.submit()
		return plan
