# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Regression suite for the Leave Planning workstream.

Each test method names the bug or invariant it locks down. The two BUG_E2E_*
tests exist because the end-to-end smoke test caught real defects that would
have shipped without it; these guarantees stay green going forward.
"""

from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from seal_hrms.seal_hrms.leave_planning.endpoints.plan import can_cancel_plan, cancel_plan

from seal_hrms.seal_hrms.tests.integration._fixtures import (
	COMPANY,
	add_cycle_member,
	cleanup_booking,
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
)


EMPLOYEE = "_T-Employee-00001"


class TestLeavePlanningRegressions(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("Regression Plannable Annual")
		cls.leave_period = ensure_leave_period(COMPANY)
		cls.allocation = ensure_allocation(EMPLOYEE, cls.leave_type, cls.leave_period, days=30)

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member = add_cycle_member(self.cycle, EMPLOYEE)
		self._created_plans: list[str] = []
		self._created_las: list[str] = []
		self._created_bookings: list[str] = []
		frappe.db.commit()

	def tearDown(self):
		for la_name in self._created_las:
			cleanup_la(la_name)
		for plan_name in self._created_plans:
			cleanup_plan(plan_name)
		for booking_name in self._created_bookings:
			cleanup_booking(booking_name)
		cleanup_cycle_and_member(self.cycle, self.member)
		frappe.db.commit()

	def test_BUG_E2E_leave_type_validate_does_not_reference_dropped_field(self):
		"""Regression for Phase 2 oversight: overrides/leave_type.py read
		`custom_require_one_slot_min_days` which was dropped in v1_2.
		Saving any Leave Type used to crash with AttributeError.
		"""
		lt = frappe.get_doc("Leave Type", self.leave_type)
		lt.custom_min_days_per_slot = 2
		lt.custom_max_days_per_slot = 14
		lt.save(ignore_permissions=True)

	def test_leave_type_validate_min_exceeds_max_per_slot_throws(self):
		lt = frappe.get_doc("Leave Type", self.leave_type)
		lt.custom_min_days_per_slot = 20
		lt.custom_max_days_per_slot = 5
		with self.assertRaises(frappe.exceptions.ValidationError):
			lt.save(ignore_permissions=True)
		lt.reload()
		lt.custom_min_days_per_slot = 1
		lt.custom_max_days_per_slot = 0
		lt.save(ignore_permissions=True)

	def test_BUG_E2E_cancel_with_active_booking_blocked_in_before_cancel(self):
		"""Regression for B1 + on_cancel-vs-before_cancel timing bug.

		Originally the gate sat in on_cancel, which runs AFTER docstatus has
		flipped to 2. can_cancel_plan then returned 'Already cancelled' and the
		cancel itself threw. Gate must run in before_cancel while docstatus is
		still 1.
		"""
		plan = self._create_submitted_plan()
		la = self._file_submitted_la(plan)

		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			plan.cancel()
		msg = str(ctx.exception).lower()
		self.assertIn("draw from this plan", msg)
		self.assertIn(la.name.lower(), msg)

	def test_cancel_after_la_cancelled_succeeds(self):
		plan = self._create_submitted_plan()
		la = self._file_submitted_la(plan)

		la.cancel()
		plan.reload()

		gate = can_cancel_plan(plan.name)
		self.assertTrue(gate["can_cancel"], gate.get("reason"))

		cancel_plan(plan.name)
		self.assertEqual(frappe.db.get_value("Leave Plan", plan.name, "docstatus"), 2)

	def test_can_cancel_plan_returns_dict_with_verb_keyed_field(self):
		"""§1.11: can_<action> functions return a dict keyed by the verb."""
		plan = self._create_submitted_plan()
		la = self._file_submitted_la(plan)

		result = can_cancel_plan(plan.name)
		self.assertIn("can_cancel", result)
		self.assertIn("reason", result)
		self.assertIsInstance(result["can_cancel"], bool)
		self.assertFalse(result["can_cancel"])
		self.assertTrue(result["reason"])

	def test_la_for_plannable_type_without_covering_plan_throws(self):
		from_d = next_business_day(add_days(today(), 30))
		to_d = add_days(from_d, 4)

		la = frappe.new_doc("Leave Application")
		la.employee = EMPLOYEE
		la.leave_type = self.leave_type
		la.from_date = from_d
		la.to_date = to_d
		la.description = "should be rejected"
		la.status = "Approved"
		la.leave_approver = "Administrator"

		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			la.insert(ignore_permissions=True)
		msg = str(ctx.exception).lower()
		self.assertTrue(
			"submitted leave plan" in msg or "slot" in msg,
			f"Expected plan/slot rejection message, got: {ctx.exception}",
		)

	def test_year_end_reject_when_slot_crosses_period_boundary(self):
		period = frappe.db.get_value(
			"Leave Period", self.leave_period,
			["from_date", "to_date"], as_dict=True,
		)
		bad_from = period.to_date - timedelta(days=2)
		bad_to = period.to_date + timedelta(days=5)

		plan = frappe.new_doc("Leave Plan")
		plan.planning_cycle = self.cycle
		plan.employee = EMPLOYEE
		plan.append("leave_plan_slots", {
			"leave_type": self.leave_type,
			"from_date": bad_from,
			"to_date": bad_to,
		})

		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			plan.insert(ignore_permissions=True)
		self.assertIn("crosses out of leave period", str(ctx.exception).lower())

	def test_full_happy_path_booking_then_cancel(self):
		plan = self._create_submitted_plan()
		la = self._file_submitted_la(plan)

		bookings = frappe.get_all(
			"Leave Plan Slot Booking",
			filters={"leave_application": la.name},
			fields=["name", "slot", "days", "status"],
		)
		self.assertEqual(len(bookings), 1, f"expected 1 booking, got {bookings}")
		self._created_bookings.append(bookings[0].name)
		self.assertEqual(bookings[0].status, "Active")

		slot_status = frappe.db.get_value("Leave Plan Slot", bookings[0].slot, "slot_status")
		plan_status = frappe.db.get_value("Leave Plan", plan.name, "status")
		self.assertEqual(slot_status, "Fully Booked")
		self.assertEqual(plan_status, "Fully Applied")

		la.cancel()
		slot_status_after = frappe.db.get_value("Leave Plan Slot", bookings[0].slot, "slot_status")
		plan_status_after = frappe.db.get_value("Leave Plan", plan.name, "status")
		booking_after = frappe.db.get_value("Leave Plan Slot Booking", bookings[0].name, "status")
		self.assertEqual(slot_status_after, "Open")
		self.assertEqual(plan_status_after, "Not Applied")
		self.assertEqual(booking_after, "Cancelled")

	def test_la_idempotent_on_cancel_when_no_booking_exists(self):
		"""Cancelling an LA for a non-plannable type (or one that never produced
		a booking) must not raise — the on_cancel hook is idempotent.
		"""
		from seal_hrms.seal_hrms.leave_planning.endpoints.booking import cancel_booking_for_la
		result = cancel_booking_for_la("non-existent-la-12345")
		self.assertFalse(result)

	def test_uniqueness_one_active_plan_per_employee_per_cycle(self):
		plan_a = self._create_submitted_plan()

		plan_b = frappe.new_doc("Leave Plan")
		plan_b.planning_cycle = self.cycle
		plan_b.employee = EMPLOYEE
		plan_b.append("leave_plan_slots", {
			"leave_type": self.leave_type,
			"from_date": next_business_day(add_days(today(), 90)),
			"to_date": next_business_day(add_days(today(), 92)),
		})
		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			plan_b.insert(ignore_permissions=True)
		self.assertIn("already has a leave plan", str(ctx.exception).lower())

	def _create_submitted_plan(self):
		slot_from = next_business_day(add_days(today(), 30))
		slot_to = add_days(slot_from, 4)
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
			"description": "regression-test slot",
		}])
		self._created_plans.append(plan.name)
		plan.submit()
		return plan

	def _file_submitted_la(self, plan):
		slot = plan.leave_plan_slots[0]
		la = file_leave_application(EMPLOYEE, self.leave_type, slot.from_date, slot.to_date)
		self._created_las.append(la.name)
		la.submit()
		booking_name = frappe.db.get_value(
			"Leave Plan Slot Booking", {"leave_application": la.name}, "name",
		)
		if booking_name:
			self._created_bookings.append(booking_name)
		return la
