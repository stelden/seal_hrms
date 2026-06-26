# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Edge cases for the Leave Application override (SPEC §8.2-§8.4)."""

from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.leave_planning.endpoints.booking import (
	cancel_booking_for_la,
	create_booking_for_la,
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
)


EMPLOYEE = "_T-Employee-00001"


class TestLeaveApplicationHookEdgeCases(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.plannable = ensure_plannable_leave_type(
			"LA Hook Test Plannable", min_application_advance_days=3,
		)
		cls.non_plannable = _ensure_non_plannable("LA Hook Test Non-Plannable")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMPLOYEE, cls.plannable, cls.leave_period, days=30)
		ensure_allocation(EMPLOYEE, cls.non_plannable, cls.leave_period, days=10)

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member = add_cycle_member(self.cycle, EMPLOYEE)
		self._created_plans: list[str] = []
		self._created_las: list[str] = []
		frappe.db.commit()

	def tearDown(self):
		for la in self._created_las:
			cleanup_la(la)
		for plan in self._created_plans:
			cleanup_plan(plan)
		cleanup_cycle_and_member(self.cycle, self.member)
		frappe.db.commit()

	def test_non_plannable_la_bypasses_plan_gate_entirely(self):
		"""LA for a non-plannable type should not require a plan slot."""
		from_d = next_business_day(add_days(today(), 7))
		to_d = add_days(from_d, 1)
		la = file_leave_application(EMPLOYEE, self.non_plannable, from_d, to_d)
		self._created_las.append(la.name)
		la.submit()
		self.assertEqual(la.docstatus, 1)
		bookings = frappe.get_all("Leave Plan Slot Booking", filters={"leave_application": la.name})
		self.assertEqual(len(bookings), 0, "non-plannable LA should NOT create a booking")

	def test_min_advance_days_blocks_late_filing(self):
		"""custom_min_application_advance_days = 3 means filing tomorrow throws."""
		from_d = next_business_day(add_days(today(), 1))
		to_d = add_days(from_d, 1)
		la = frappe.new_doc("Leave Application")
		la.employee = EMPLOYEE
		la.leave_type = self.plannable
		la.from_date = from_d
		la.to_date = to_d
		la.status = "Approved"
		la.leave_approver = "Administrator"
		with self.assertRaises(frappe.exceptions.ValidationError) as ctx:
			la.insert(ignore_permissions=True)
		self.assertIn("less than", str(ctx.exception).lower())

	def test_cancel_booking_idempotent_when_la_unknown(self):
		"""cancel_booking_for_la must not raise on a missing LA."""
		result = cancel_booking_for_la("nonexistent-la-xyz")
		self.assertFalse(result)

	def test_create_booking_idempotent_skips_when_already_present(self):
		"""create_booking_for_la called twice for the same LA → no duplicate booking."""
		plan = self._create_submitted_plan()
		la = self._submit_la_in_slot(plan)

		bookings = frappe.get_all(
			"Leave Plan Slot Booking",
			filters={"leave_application": la.name},
		)
		self.assertEqual(len(bookings), 1)

		result = create_booking_for_la(la.name)
		self.assertEqual(result, bookings[0].name, "should return existing booking, not create new")

		bookings_after = frappe.get_all(
			"Leave Plan Slot Booking",
			filters={"leave_application": la.name},
		)
		self.assertEqual(len(bookings_after), 1, "duplicate prevented")

	def _create_submitted_plan(self):
		slot_from = next_business_day(add_days(today(), 30))
		slot_to = add_days(slot_from, 4)
		plan = create_leave_plan(self.cycle, EMPLOYEE, [{
			"leave_type": self.plannable,
			"from_date": slot_from,
			"to_date": slot_to,
		}])
		self._created_plans.append(plan.name)
		plan.submit()
		return plan

	def _submit_la_in_slot(self, plan):
		slot = plan.leave_plan_slots[0]
		la = file_leave_application(EMPLOYEE, self.plannable, slot.from_date, slot.to_date)
		self._created_las.append(la.name)
		la.submit()
		return la


def _ensure_non_plannable(name: str) -> str:
	if frappe.db.exists("Leave Type", name):
		lt = frappe.get_doc("Leave Type", name)
	else:
		lt = frappe.new_doc("Leave Type")
		lt.leave_type_name = name
	lt.custom_is_plannable = 0
	lt.is_lwp = 0
	lt.is_compensatory = 0
	lt.is_encashable = 0
	lt.include_holiday = 1
	lt.max_leaves_allowed = 30
	lt.save(ignore_permissions=True) if lt.name else lt.insert(ignore_permissions=True)
	return lt.name
