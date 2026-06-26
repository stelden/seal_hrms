# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Year-boundary edge cases for Leave Plan slot validation.

The year-end reject (Fork C / C3) throws when a slot crosses out of the
cycle's leave period. These tests pin down the exact boundary semantics:

  - Slot ending exactly on period.to_date is OK
  - Slot starting exactly on period.from_date is OK
  - Slot starting one day before period.from_date throws
  - Slot ending one day after period.to_date throws
"""

from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

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
)


EMPLOYEE = "_T-Employee-00001"


class TestYearBoundaryEdges(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("Year Boundary Edge Test")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMPLOYEE, cls.leave_type, cls.leave_period, days=30)
		period = frappe.db.get_value(
			"Leave Period", cls.leave_period,
			["from_date", "to_date"], as_dict=True,
		)
		cls.period_from = getdate(period.from_date)
		cls.period_to = getdate(period.to_date)

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

	def test_slot_starting_exactly_on_period_from_is_accepted(self):
		from_d = self.period_from
		to_d = from_d + timedelta(days=4)
		plan = self._try_plan(from_d, to_d)
		self.assertIsNotNone(plan)

	def test_slot_ending_exactly_on_period_to_is_accepted(self):
		to_d = self.period_to
		from_d = to_d - timedelta(days=4)
		plan = self._try_plan(from_d, to_d)
		self.assertIsNotNone(plan)

	def test_slot_starting_one_day_before_period_from_throws(self):
		from_d = self.period_from - timedelta(days=1)
		to_d = from_d + timedelta(days=4)
		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			self._try_plan(from_d, to_d)
		self.assertIn("crosses out of leave period", str(ctx.exception).lower())

	def test_slot_ending_one_day_after_period_to_throws(self):
		to_d = self.period_to + timedelta(days=1)
		from_d = to_d - timedelta(days=4)
		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			self._try_plan(from_d, to_d)
		self.assertIn("crosses out of leave period", str(ctx.exception).lower())

	def _try_plan(self, from_date, to_date):
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.leave_type,
			"from_date": from_date,
			"to_date": to_date,
		}])
		self._created_plans.append(plan.name)
		return plan
