# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Scheduler integration tests — reminder dispatch + cycle close.

Tests dispatch behaviour with manipulated cycle deadlines and asserts the
first-detection guard (§3.7) prevents duplicate nudges in one day.
"""

from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from seal_hrms.seal_hrms.leave_planning.scheduler import (
	close_due_cycles,
	send_planning_reminders,
	_business_day_aware_offsets,
	_parse_offsets,
)

from seal_hrms.seal_hrms.tests.integration._fixtures import (
	COMPANY,
	add_cycle_member,
	cleanup_cycle_and_member,
	create_open_cycle,
	ensure_leave_period,
)


EMPLOYEE = "_T-Employee-00001"


class TestPureSchedulerHelpers(FrappeTestCase):
	def test_parse_offsets_handles_blanks_and_negatives(self):
		self.assertEqual(_parse_offsets("30,14,7,3,1"), {30, 14, 7, 3, 1})
		self.assertEqual(_parse_offsets(""), set())
		self.assertEqual(_parse_offsets(None), set())
		self.assertEqual(_parse_offsets("3, , 5,-1"), {3, 5})
		self.assertEqual(_parse_offsets("not_a_number,7"), {7})

	def test_business_day_aware_offsets_includes_calendar_and_next_business_day(self):
		from datetime import date
		friday = date(2026, 5, 8)
		monday_deadline = date(2026, 5, 18)
		offsets = _business_day_aware_offsets(friday, monday_deadline)
		self.assertIn(10, offsets)
		self.assertIn(7, offsets)


class TestSchedulerDispatch(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_period = ensure_leave_period(COMPANY)

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member = add_cycle_member(self.cycle, EMPLOYEE)
		frappe.db.set_value(
			"Leave Planning Cycle Member", self.member,
			{"plan_status": "Not Started", "exempt": 0, "nudges_sent": 0, "last_nudge_at": None},
			update_modified=False,
		)
		frappe.db.commit()

	def tearDown(self):
		cleanup_cycle_and_member(self.cycle, self.member)
		frappe.db.commit()

	def test_close_due_cycles_flips_overdue_open_cycles_to_closed(self):
		frappe.db.set_value(
			"Leave Planning Cycle", self.cycle,
			{"submission_deadline": add_days(today(), -1)},
			update_modified=False,
		)
		close_due_cycles()
		status = frappe.db.get_value("Leave Planning Cycle", self.cycle, "status")
		self.assertEqual(status, "Closed")

	def test_close_due_cycles_leaves_future_deadline_alone(self):
		frappe.db.set_value(
			"Leave Planning Cycle", self.cycle,
			{"submission_deadline": add_days(today(), 30)},
			update_modified=False,
		)
		close_due_cycles()
		status = frappe.db.get_value("Leave Planning Cycle", self.cycle, "status")
		self.assertEqual(status, "Open")

	def test_send_planning_reminders_first_detection_guard_throttles_same_day(self):
		"""Per §3.7: if member.last_nudge_at is today, a second run does not nudge again."""
		frappe.db.set_value(
			"Leave Planning Cycle", self.cycle,
			{"submission_deadline": add_days(today(), 7)},
			update_modified=False,
		)
		send_planning_reminders()
		first = frappe.db.get_value(
			"Leave Planning Cycle Member", self.member,
			["nudges_sent", "last_nudge_at"], as_dict=True,
		)
		send_planning_reminders()
		second = frappe.db.get_value(
			"Leave Planning Cycle Member", self.member,
			["nudges_sent", "last_nudge_at"], as_dict=True,
		)
		self.assertEqual(
			first.nudges_sent, second.nudges_sent,
			"second run on same day must not increment nudges_sent",
		)

	def test_exempt_members_are_not_nudged(self):
		frappe.db.set_value(
			"Leave Planning Cycle", self.cycle,
			{"submission_deadline": add_days(today(), 7)},
			update_modified=False,
		)
		frappe.db.set_value(
			"Leave Planning Cycle Member", self.member,
			{"exempt": 1, "exempt_reason": "probationer"},
			update_modified=False,
		)
		send_planning_reminders()
		nudges = frappe.db.get_value("Leave Planning Cycle Member", self.member, "nudges_sent")
		self.assertEqual(int(nudges or 0), 0)
