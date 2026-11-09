# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Does a week account for the person's time (timesheets/effort.py), and the report that lists what does not."""

import json
import unittest
from datetime import date

import frappe
from frappe.utils import add_days

from seal_hrms.seal_hrms.timesheets import approval, effort, week
from seal_hrms.seal_hrms.toil.days import PUBLIC, REST, WORKING
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_timesheet_approval import ACTIVITY_TYPE
from seal_hrms.tests.test_timesheet_week import WeekTestCase, entry

D = date(2026, 11, 2)


def day(kind=WORKING, logged=0, leave=0.0, kept=False, present=False):
	return effort.Day(
		date=D, kind=kind, logged=logged, leave_fraction=leave, attendance_kept=kept, present=present
	)


class TestTheRules(unittest.TestCase):
	def flags(self, d, hours_per_day=8):
		return effort.check_days([d], hours_per_day).days[0].flags

	def test_a_full_working_day_is_accounted_for(self):
		self.assertEqual(self.flags(day(logged=8)), [])

	def test_a_short_working_day(self):
		self.assertEqual(self.flags(day(logged=5)), [effort.SHORT])

	def test_leave_counts_towards_the_day(self):
		self.assertEqual(self.flags(day(logged=4, leave=0.5)), [])
		self.assertEqual(self.flags(day(logged=0, leave=1)), [])

	def test_hours_on_a_day_of_leave(self):
		self.assertEqual(self.flags(day(logged=3, leave=1)), [effort.ON_LEAVE])
		self.assertIn(effort.ON_LEAVE, self.flags(day(logged=6, leave=0.5)))

	def test_hours_without_attendance_only_where_attendance_is_kept(self):
		self.assertIn(effort.NO_ATTENDANCE, self.flags(day(logged=8, kept=True, present=False)))
		self.assertNotIn(effort.NO_ATTENDANCE, self.flags(day(logged=8, kept=False)))
		self.assertNotIn(effort.NO_ATTENDANCE, self.flags(day(logged=8, kept=True, present=True)))

	def test_rest_days_and_holidays_expect_nothing_and_flag_extra(self):
		self.assertEqual(self.flags(day(kind=REST)), [])
		self.assertEqual(self.flags(day(kind=PUBLIC, logged=4)), [effort.EXTRA])
		self.assertEqual(self.flags(day(logged=10)), [effort.EXTRA])

	def test_the_week_adds_up(self):
		days = [day(logged=8), day(logged=4, leave=0.5), day(kind=REST)]
		result = effort.check_days(days, 8)
		self.assertEqual((result.expected, result.accounted, result.short), (16, 16, False))
		self.assertTrue(effort.check_days([day(logged=6)], 8).short)


class EffortTestCase(WeekTestCase):
	def _full_week(self, hours=8):
		return self._week([entry(1, [hours, hours, hours, hours, hours, 0, 0], ACTIVITY_TYPE)])

	def _leave_on(self, day):
		leave = frappe.new_doc("Leave Application")
		leave.employee = self.otieno
		leave.leave_type = fx.ensure_leave_type()
		leave.from_date = leave.to_date = day
		leave.leave_approver = self.achieng_user
		leave.status = "Approved"
		leave.description = "Clinic appointment at Kenyatta"
		leave.insert(ignore_permissions=True)
		leave.submit()


class TestAWeek(EffortTestCase):
	def test_a_full_week_has_nothing_to_look_at(self):
		doc = self._full_week()
		self.assertEqual(effort.describe(effort.week_of(doc)), [])

	def test_a_short_day_is_pointed_out(self):
		doc = self._week([entry(1, [8, 8, 5, 8, 8, 0, 0], ACTIVITY_TYPE)])
		lines = effort.describe(effort.week_of(doc))
		self.assertEqual(len(lines), 1)
		self.assertIn("5 of 8 hours", lines[0])

	def test_hours_on_approved_leave_are_pointed_out(self):
		self._leave_on(add_days(self.monday, 1))
		doc = self._full_week()
		self.assertIn("approved leave", " ".join(effort.describe(effort.week_of(doc))))

	def test_the_form_gets_the_points_for_a_saved_week(self):
		doc = self._week([entry(1, [8, 8, 5, 8, 8, 0, 0], ACTIVITY_TYPE)])
		context = fx.as_user(self.otieno_user, week.week_context, self.otieno, self.monday, doc.name)
		self.assertEqual(len(context["checks"]), 1)


class TestSendingAShortWeek(EffortTestCase):
	def test_where_gaps_are_only_pointed_out_it_can_be_sent(self):
		doc = self._week([entry(1, [8, 8, 5, 8, 8, 0, 0], ACTIVITY_TYPE)])
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		self.assertEqual(doc.custom_approval_state, "Waiting for Approval")

	def test_where_the_company_refuses_it_cannot(self):
		tf.policy(
			weekly_timesheets=1,
			timesheet_approval=1,
			default_activity_type=ACTIVITY_TYPE,
			effort_rule=effort.REFUSE,
		)
		doc = self._week([entry(1, [8, 8, 5, 8, 8, 0, 0], ACTIVITY_TYPE)])
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		self.assertIn("does not yet account for your time", str(caught.exception))

	def test_a_full_week_sends_even_where_the_company_refuses(self):
		tf.policy(
			weekly_timesheets=1,
			timesheet_approval=1,
			default_activity_type=ACTIVITY_TYPE,
			effort_rule=effort.REFUSE,
		)
		doc = self._full_week()
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		self.assertEqual(doc.custom_approval_state, "Waiting for Approval")

	def test_leave_makes_up_the_week(self):
		tf.policy(
			weekly_timesheets=1,
			timesheet_approval=1,
			default_activity_type=ACTIVITY_TYPE,
			effort_rule=effort.REFUSE,
		)
		self._leave_on(add_days(self.monday, 2))
		doc = self._week([entry(1, [8, 8, 0, 8, 8, 0, 0], ACTIVITY_TYPE)])
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)


class TestTheReport(EffortTestCase):
	def _run(self, **filters):
		from seal_hrms.seal_hrms.report.timesheets_against_attendance_and_leave.timesheets_against_attendance_and_leave import (
			execute,
		)

		base = {
			"company": tf.COMPANY,
			"employee": self.otieno,
			"from_date": self.monday,
			"to_date": str(add_days(self.monday, 6)),
		}
		return execute({**base, **filters})[1]

	def test_only_the_days_to_look_at(self):
		self._week([entry(1, [8, 8, 5, 8, 8, 0, 0], ACTIVITY_TYPE)])
		rows = self._run(only_issues=1)
		self.assertEqual(
			[(str(r.date), r.flags) for r in rows], [(str(add_days(self.monday, 2)), "Not accounted for")]
		)

	def test_every_day_on_request(self):
		self._full_week()
		rows = self._run(only_issues=0)
		self.assertEqual(len(rows), 7)
		self.assertEqual(sum(r.logged for r in rows), 40)

	def test_drafts_count(self):
		doc = self._week([entry(1, [8, 8, 8, 8, 8, 0, 0], ACTIVITY_TYPE)])
		self.assertEqual(doc.docstatus, 0)
		self.assertEqual(self._run(only_issues=1), [])

	def test_a_long_range_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self._run(to_date=str(add_days(self.monday, 90)))


class TestExtraDoesNotMakeUpShort(EffortTestCase):
	def test_a_short_day_is_refused_even_when_the_week_totals_more(self):
		tf.policy(
			weekly_timesheets=1,
			timesheet_approval=1,
			default_activity_type=ACTIVITY_TYPE,
			effort_rule=effort.REFUSE,
		)
		doc = self._week([entry(1, [10, 10, 5, 8, 8, 0, 0], ACTIVITY_TYPE)])
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
