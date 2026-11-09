# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A timesheet filled in as a week (timesheets/week.py): the generator, and the timesheet it writes."""

import json
import unittest
from datetime import date, datetime

import frappe
from frappe.utils import add_days, getdate

from seal_hrms.seal_hrms.timesheets import week
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_timesheet_approval import ACTIVITY_TYPE, TimesheetTestCase

MONDAY = date(2026, 11, 2)


def entry(row, hours, activity="Training", **more):
	return {"row": row, "activity_type": activity, "hours": hours, **more}


class TestRowsForAWeek(unittest.TestCase):
	def test_lines_run_back_to_back_from_the_day_start(self):
		rows = week.rows_for(MONDAY, [entry(1, [4, 0, 0, 0, 0, 0, 0]), entry(2, [3.5, 0, 0, 0, 0, 0, 0])])
		self.assertEqual(
			[(r["from_time"], r["to_time"], r["custom_grid_row"]) for r in rows],
			[
				(datetime(2026, 11, 2, 8, 0), datetime(2026, 11, 2, 12, 0), 1),
				(datetime(2026, 11, 2, 12, 0), datetime(2026, 11, 2, 15, 30), 2),
			],
		)

	def test_each_day_falls_on_its_own_date(self):
		rows = week.rows_for(MONDAY, [entry(1, [0, 0, 0, 0, 0, 0, 2])])
		self.assertEqual(rows[0]["from_time"].date(), date(2026, 11, 8))

	def test_a_long_day_starts_earlier_and_ends_by_23_59(self):
		rows = week.rows_for(MONDAY, [entry(1, [20, 0, 0, 0, 0, 0, 0])], day_start_minutes=8 * 60)
		self.assertEqual(
			(rows[0]["from_time"].time().isoformat(), rows[0]["to_time"].time().isoformat()),
			("03:59:00", "23:59:00"),
		)

	def test_a_day_longer_than_23_59_is_refused(self):
		with self.assertRaises(week.DayTooLong):
			week.rows_for(MONDAY, [entry(1, [24, 0, 0, 0, 0, 0, 0])])

	def test_hours_become_whole_minutes(self):
		rows = week.rows_for(MONDAY, [entry(1, [1.3333, 0, 0, 0, 0, 0, 0])])
		self.assertEqual(
			rows[0]["to_time"] - rows[0]["from_time"], datetime(2026, 1, 1, 1, 20) - datetime(2026, 1, 1)
		)

	def test_empty_cells_and_lines_write_nothing(self):
		self.assertEqual(week.rows_for(MONDAY, [entry(1, [0] * 7), entry(2, [])]), [])

	def test_monday_of_any_day(self):
		self.assertEqual(week.monday_of("2026-11-08"), MONDAY)
		self.assertEqual(week.monday_of("2026-11-02"), MONDAY)


class WeekTestCase(TimesheetTestCase):
	def setUp(self):
		super().setUp()
		tf.policy(weekly_timesheets=1, timesheet_approval=1, default_activity_type=ACTIVITY_TYPE)
		self.monday = str(week.monday_of(add_days(tf.working_day(), -7)))

	def _week(self, entries, monday=None, insert=True):
		doc = frappe.new_doc("Timesheet")
		doc.company = tf.COMPANY
		doc.employee = self.otieno
		doc.custom_week_start = monday or self.monday
		doc.custom_week_entries = json.dumps(entries)
		if insert:
			fx.as_user(self.otieno_user, doc.insert)
		return doc


class TestAWeeklyTimesheet(WeekTestCase):
	def test_the_week_writes_the_time_lines(self):
		doc = self._week(
			[
				entry(1, [8, 4, 0, 0, 0, 0, 0], ACTIVITY_TYPE, description="Mathare North visits"),
				entry(2, [0, 4, 8, 8, 8, 0, 0], ACTIVITY_TYPE),
			]
		)
		self.assertEqual(len(doc.time_logs), 6)
		self.assertEqual(doc.total_hours, 40)
		self.assertEqual(
			(str(doc.start_date), str(doc.end_date)), (self.monday, str(add_days(self.monday, 4)))
		)
		self.assertEqual(doc.time_logs[0].description, "Mathare North visits")

	def test_saving_again_rewrites_them_from_the_week(self):
		doc = self._week([entry(1, [8, 0, 0, 0, 0, 0, 0], ACTIVITY_TYPE)])
		doc.custom_week_entries = json.dumps([entry(1, [6, 2, 0, 0, 0, 0, 0], ACTIVITY_TYPE)])
		fx.as_user(self.otieno_user, doc.save)
		self.assertEqual([round(t.hours, 2) for t in doc.time_logs], [6, 2])

	def test_a_week_starts_on_a_monday(self):
		with self.assertRaises(frappe.ValidationError) as caught:
			self._week([entry(1, [8, 0, 0, 0, 0, 0, 0], ACTIVITY_TYPE)], monday=str(add_days(self.monday, 2)))
		self.assertIn("starts on a Monday", str(caught.exception))

	def test_one_timesheet_a_week(self):
		self._week([entry(1, [8, 0, 0, 0, 0, 0, 0], ACTIVITY_TYPE)])
		with self.assertRaises(frappe.ValidationError) as caught:
			self._week([entry(1, [0, 0, 0, 0, 0, 3, 0], ACTIVITY_TYPE)])
		self.assertIn("already has a timesheet", str(caught.exception))

	def test_hours_need_a_kind_of_work(self):
		with self.assertRaises(frappe.ValidationError) as caught:
			self._week([entry(1, [8, 0, 0, 0, 0, 0, 0], None)])
		self.assertIn("activity type", str(caught.exception))

	def test_an_empty_week_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self._week([entry(1, [0] * 7, ACTIVITY_TYPE)])

	def test_a_week_sends_and_is_approved_like_any_timesheet(self):
		from seal_hrms.seal_hrms.timesheets import approval

		doc = self._week([entry(1, [8, 8, 8, 8, 8, 0, 0], ACTIVITY_TYPE)])
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		fx.as_user(self.achieng_user, approval.approve, doc.name)
		doc.reload()
		self.assertEqual((doc.docstatus, doc.total_hours), (1, 40))

	def test_a_company_without_weeks_is_untouched(self):
		tf.policy(weekly_timesheets=0, timesheet_approval=1)
		doc = self._timesheet()
		self.assertEqual(len(doc.time_logs), 1)
		self.assertFalse(doc.get("custom_week_start"))


class TestWhatTheWeekShows(WeekTestCase):
	def test_days_carry_their_kind_leave_and_attendance(self):
		monday = str(week.monday_of(tf.rest_day()))
		context = fx.as_user(self.otieno_user, week.week_context, self.otieno, monday)
		kinds = [d["kind"] for d in context["days"]]
		self.assertEqual(len(kinds), 7)
		self.assertEqual(kinds[6], "Rest day")
		self.assertTrue(context["weekly"])
		self.assertEqual(context["default_activity_type"], ACTIVITY_TYPE)

	def test_last_weeks_lines_are_offered_to_copy(self):
		self._week([entry(1, [8, 0, 0, 0, 0, 0, 0], ACTIVITY_TYPE, description="Mathare North visits")])
		next_monday = str(add_days(self.monday, 7))
		context = fx.as_user(self.otieno_user, week.week_context, self.otieno, next_monday)
		self.assertEqual([e["description"] for e in context["previous_entries"]], ["Mathare North visits"])

	def test_a_colleague_cannot_see_someone_elses_week(self):
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, week.week_context, self.otieno, self.monday)

	def test_the_form_learns_whether_to_show_the_week(self):
		self.assertTrue(fx.as_user(self.otieno_user, week.weekly_for, self.otieno)["weekly"])
		self.assertTrue(
			fx.as_user(self.achieng_user, week.weekly_for, self.otieno)["weekly"], "the approver too"
		)
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, week.weekly_for, self.otieno)
