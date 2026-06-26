# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Tests for the Leave Planning report endpoints (SPEC §1, §3 of REPORTS.md)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.leave_planning.reports import (
	compliance_roster,
	departmental_coverage,
)

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


class TestDepartmentalCoverage(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("Reports Test Annual")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMPLOYEE, cls.leave_type, cls.leave_period, days=30)

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

	def test_returns_expected_top_level_keys(self):
		result = departmental_coverage(company=COMPANY)
		for key in ("weeks", "headcount", "cells"):
			self.assertIn(key, result)
		self.assertIsInstance(result["weeks"], list)
		self.assertIsInstance(result["headcount"], dict)
		self.assertIsInstance(result["cells"], list)

	def test_weeks_format_is_iso(self):
		result = departmental_coverage(company=COMPANY, leave_period=self.leave_period)
		for week in result["weeks"]:
			self.assertRegex(week, r"^\d{4}-W\d{2}$")

	def test_no_plans_yields_empty_cells_but_populated_headcount(self):
		result = departmental_coverage(company=COMPANY, leave_period=self.leave_period)
		self.assertEqual(result["cells"], [])
		self.assertGreater(sum(result["headcount"].values()), 0)

	def test_cell_appears_when_a_plan_is_submitted(self):
		slot_from = next_business_day(add_days(today(), 30))
		slot_to = add_days(slot_from, 4)
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
		}])
		self._created_plans.append(plan.name)
		plan.submit()

		result = departmental_coverage(company=COMPANY, leave_period=self.leave_period)
		emp_dept = frappe.db.get_value("Employee", EMPLOYEE, "department")
		matching = [c for c in result["cells"] if c["department"] == emp_dept and c["absent_employees"] > 0]
		self.assertGreater(len(matching), 0, "expected at least one populated cell after plan submit")
		for cell in matching:
			self.assertGreaterEqual(cell["headcount"], cell["absent_employees"])
			self.assertGreaterEqual(cell["percent_absent"], 0)
			self.assertLessEqual(cell["percent_absent"], 100)


class TestComplianceRoster(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_period = ensure_leave_period(COMPANY)

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member = add_cycle_member(self.cycle, EMPLOYEE)
		frappe.db.commit()

	def tearDown(self):
		cleanup_cycle_and_member(self.cycle, self.member)
		frappe.db.commit()

	def test_returns_expected_shape(self):
		result = compliance_roster(cycle=self.cycle)
		self.assertIn("cycle", result)
		self.assertIn("summary", result)
		self.assertIn("members", result)
		self.assertEqual(result["cycle"]["name"], self.cycle)

	def test_summary_buckets_sum_to_total(self):
		result = compliance_roster(cycle=self.cycle)
		s = result["summary"]
		bucket_sum = (
			(s.get("approved") or 0) + (s.get("pending") or 0) + (s.get("draft") or 0)
			+ (s.get("not_started") or 0) + (s.get("exempt") or 0) + (s.get("cancelled") or 0)
		)
		self.assertEqual(bucket_sum, s["total"])

	def test_status_filter_narrows_members(self):
		all_members = compliance_roster(cycle=self.cycle)["members"]
		not_started_only = compliance_roster(cycle=self.cycle, status_filter=["Not Started"])["members"]
		self.assertLessEqual(len(not_started_only), len(all_members))
		for m in not_started_only:
			self.assertEqual(m["plan_status"], "Not Started")

	def test_unknown_cycle_throws(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			compliance_roster(cycle="does-not-exist")
