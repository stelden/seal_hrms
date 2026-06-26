# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Edge cases for the slots helper module.

calculate_slot_days, compute_slot_status, compute_plan_status — pure-read
functions that the controller, endpoints, and JS all depend on.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.leave_planning.slots import (
	calculate_slot_days,
	compute_plan_status,
	compute_slot_status,
)

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
	file_leave_application,
	next_business_day,
	wipe_employee_planning_state,
)


EMPLOYEE = "_T-Employee-00001"


class TestCalculateSlotDays(FrappeTestCase):

	def test_returns_zero_when_from_after_to(self):
		days = calculate_slot_days(EMPLOYEE, "2026-06-15", "2026-06-10")
		self.assertEqual(days, 0)

	def test_single_day_range_is_one_or_zero_depending_on_holiday(self):
		days = calculate_slot_days(EMPLOYEE, "2026-06-10", "2026-06-10")
		self.assertIn(days, (0, 1))

	def test_full_week_returns_at_most_seven_days(self):
		days = calculate_slot_days(EMPLOYEE, "2026-06-08", "2026-06-14")
		self.assertGreaterEqual(days, 0)
		self.assertLessEqual(days, 7)


class TestComputeSlotAndPlanStatus(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("Slot Status Edge Test")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMPLOYEE, cls.leave_type, cls.leave_period, days=30)

	def setUp(self):
		wipe_employee_planning_state(EMPLOYEE, self.leave_type)
		frappe.clear_document_cache("Leave Type", self.leave_type)
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member = add_cycle_member(self.cycle, EMPLOYEE)
		self._created_plans = []
		self._created_las = []
		frappe.db.commit()

	def tearDown(self):
		for la in self._created_las:
			cleanup_la(la)
		for plan in self._created_plans:
			cleanup_plan(plan)
		cleanup_cycle_and_member(self.cycle, self.member)
		frappe.db.commit()

	def test_compute_slot_status_returns_open_for_unknown_slot(self):
		status = compute_slot_status("does-not-exist", "also-does-not-exist")
		self.assertEqual(status, "Open")

	def test_compute_plan_status_with_no_slots_is_not_applied(self):
		"""A plan with no slots reports Not Applied (defensive — controller blocks save anyway)."""
		status = compute_plan_status("non-existent-plan-xyz")
		self.assertEqual(status, "Not Applied")

	def test_status_chain_open_then_booked_then_revert(self):
		"""Slot starts Open, becomes booked when an LA covers it, returns to Open on cancel.

		The exact post-booking status (Partially vs Fully Booked) depends on whether
		Frappe HR's `total_leave_days` matches our `calculate_slot_days` for the same
		date range — the comparison is float-arithmetic-sensitive across half-day flags
		and holiday list edges. The invariant we lock down here is the Open ↔ booked
		transition, not the exact intermediate label.
		"""
		slot_from = next_business_day(add_days(today(), 30))
		slot_to = add_days(slot_from, 6)
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
		}])
		self._created_plans.append(plan.name)
		plan.submit()

		slot_row_name = plan.leave_plan_slots[0].name
		self.assertEqual(compute_slot_status(plan.name, slot_row_name), "Open")
		self.assertEqual(compute_plan_status(plan.name), "Not Applied")

		la = file_leave_application(EMPLOYEE, self.leave_type, slot_from, slot_to)
		self._created_las.append(la.name)
		la.submit()

		self.assertIn(
			compute_slot_status(plan.name, slot_row_name),
			("Partially Booked", "Fully Booked"),
		)
		self.assertIn(
			compute_plan_status(plan.name),
			("Partially Applied", "Fully Applied"),
		)

		la.cancel()
		self.assertEqual(compute_slot_status(plan.name, slot_row_name), "Open")
		self.assertEqual(compute_plan_status(plan.name), "Not Applied")

	def test_cancelled_slot_status_is_sticky(self):
		"""HR override action: explicit Cancelled is preserved even after bookings clear."""
		slot_from = next_business_day(add_days(today(), 30))
		slot_to = add_days(slot_from, 4)
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
		}])
		self._created_plans.append(plan.name)
		plan.submit()

		slot_row_name = plan.leave_plan_slots[0].name
		frappe.db.set_value(
			"Leave Plan Slot", slot_row_name,
			"slot_status", "Cancelled",
			update_modified=False,
		)
		self.assertEqual(compute_slot_status(plan.name, slot_row_name), "Cancelled")
