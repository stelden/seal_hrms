# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What the records say about extra hours (toil/evidence.py), and the claim form's Now / Next / Do.

Otieno's attendance, clock-ins and timesheets are made through the ORM; the
supervisor's word is always enough, so a line with no record is allowed and
marked "Approver only".
"""

import unittest

import frappe
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.toil import approval, evidence, stage
from seal_hrms.seal_hrms.toil.days import PUBLIC, REST, WORKING
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_toil_claim import ToilTestCase

ACTIVITY_TYPE = "Community Outreach"


class TestCounting(unittest.TestCase):
	def test_extra_hours_by_kind_of_day(self):
		self.assertEqual(evidence.extra(WORKING, 11, 8), 3)
		self.assertEqual(evidence.extra(WORKING, 7, 8), 0)
		self.assertEqual(evidence.extra(REST, 5, 8), 5)
		self.assertEqual(evidence.extra(PUBLIC, 0, 8), 0)

	def test_the_first_record_that_bears_it_out_wins(self):
		found = {evidence.ATTENDANCE: 2, evidence.CLOCK_INS: 3, evidence.TIMESHEET: 4}
		self.assertEqual(evidence.supported_by(3, found), evidence.CLOCK_INS)
		self.assertEqual(
			evidence.supported_by(2.2, found), evidence.ATTENDANCE, "within a quarter of an hour"
		)
		self.assertEqual(evidence.supported_by(5, found), evidence.APPROVER_ONLY)
		self.assertEqual(evidence.supported_by(1, {}), evidence.APPROVER_ONLY)


class EvidenceTestCase(ToilTestCase):
	def _attendance(self, day, hours):
		doc = frappe.new_doc("Attendance")
		doc.employee = self.otieno
		doc.attendance_date = day
		doc.status = "Present"
		doc.working_hours = hours
		doc.company = tf.COMPANY
		doc.insert(ignore_permissions=True)
		doc.submit()

	def _clock_ins(self, day, start, end):
		for time, log in ((start, "IN"), (end, "OUT")):
			doc = frappe.new_doc("Employee Checkin")
			doc.employee = self.otieno
			doc.time = f"{day} {time}"
			doc.log_type = log
			doc.skip_auto_attendance = 1
			doc.insert(ignore_permissions=True)

	def _timesheet(self, day, hours):
		if not frappe.db.exists("Activity Type", ACTIVITY_TYPE):
			activity = frappe.new_doc("Activity Type")
			activity.activity_type = ACTIVITY_TYPE
			activity.insert(ignore_permissions=True)
		doc = frappe.new_doc("Timesheet")
		doc.company = tf.COMPANY
		doc.employee = self.otieno
		doc.append(
			"time_logs",
			{
				"activity_type": ACTIVITY_TYPE,
				"from_time": f"{day} 08:00:00",
				"to_time": f"{day} {8 + int(hours):02d}:00:00",
				"hours": int(hours),
				"description": "Household visits in Mathare North",
			},
		)
		doc.insert(ignore_permissions=True)
		doc.submit()


class TestWhatTheRecordsShow(EvidenceTestCase):
	def test_a_late_evening_in_attendance_bears_out_the_claim(self):
		day = tf.working_day()
		self._attendance(day, 11)
		doc = tf.claim(self.otieno, [(day, 3)], as_user=self.otieno_user)
		line = doc.lines[0]
		self.assertEqual(
			(line.normal_hours, line.attendance_hours, line.supported_by), (8, 3, evidence.ATTENDANCE)
		)

	def test_clock_ins_on_a_rest_day(self):
		day = tf.rest_day()
		self._clock_ins(day, "07:30:00", "13:30:00")
		doc = tf.claim(self.otieno, [(day, 6)], as_user=self.otieno_user)
		self.assertEqual((doc.lines[0].clocked_hours, doc.lines[0].supported_by), (6, evidence.CLOCK_INS))

	def test_timesheets_on_a_rest_day(self):
		day = tf.rest_day()
		self._timesheet(day, 5)
		doc = tf.claim(self.otieno, [(day, 5)], as_user=self.otieno_user)
		self.assertEqual((doc.lines[0].timesheet_hours, doc.lines[0].supported_by), (5, evidence.TIMESHEET))

	def test_no_record_means_the_approver_confirms_it(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 4)], as_user=self.otieno_user)
		self.assertEqual(doc.lines[0].supported_by, evidence.APPROVER_ONLY)

	def test_a_company_can_leave_timesheets_out(self):
		tf.policy(evidence_timesheets=0)
		day = tf.rest_day()
		self._timesheet(day, 5)
		doc = tf.claim(self.otieno, [(day, 5)], as_user=self.otieno_user)
		self.assertFalse(doc.lines[0].timesheet_hours)
		self.assertEqual(doc.lines[0].supported_by, evidence.APPROVER_ONLY)


class TestFillingFromRecords(EvidenceTestCase):
	def _fetch(self, source, as_user=None, days=30):
		return fx.as_user(
			as_user or self.otieno_user,
			evidence.get_extra_time,
			self.otieno,
			str(add_days(today(), -days)),
			today(),
			source,
		)

	def test_attendance_offers_days_with_extra_hours_only(self):
		late, normal = tf.working_day(), tf.working_day(at_least_days_ago=9)
		self._attendance(late, 10.5)
		self._attendance(normal, 8)
		rows = self._fetch(evidence.ATTENDANCE)
		self.assertEqual([(r["work_date"], r["hours"]) for r in rows], [(late, 2.5)])

	def test_clock_ins_count_where_attendance_was_not_made(self):
		day = tf.rest_day()
		self._clock_ins(day, "09:00:00", "12:00:00")
		self.assertEqual([r["hours"] for r in self._fetch(evidence.ATTENDANCE)], [3])

	def test_timesheets_offer_rest_day_hours(self):
		day = tf.rest_day()
		self._timesheet(day, 6)
		self.assertEqual(
			[(r["work_date"], r["day_kind"]) for r in self._fetch(evidence.TIMESHEET)], [(day, REST)]
		)

	def test_days_already_claimed_are_left_out(self):
		day = tf.rest_day()
		self._timesheet(day, 6)
		tf.claim(self.otieno, [(day, 6)], as_user=self.otieno_user)
		self.assertEqual(self._fetch(evidence.TIMESHEET), [])

	def test_under_the_minimum_is_left_out(self):
		tf.policy(minimum_hours=4)
		day = tf.rest_day()
		self._timesheet(day, 3)
		self.assertEqual(self._fetch(evidence.TIMESHEET), [])

	def test_the_approver_may_look_a_colleague_may_not(self):
		self._timesheet(tf.rest_day(), 6)
		self.assertEqual(len(self._fetch(evidence.TIMESHEET, as_user=self.achieng_user)), 1)
		with self.assertRaises(frappe.PermissionError):
			self._fetch(evidence.TIMESHEET, as_user=self.njeri_user)

	def test_a_long_range_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self._fetch(evidence.TIMESHEET, days=90)


class TestNowNextDo(EvidenceTestCase):
	def _rows(self, doc, user):
		banner = stage.where_it_is(doc, user)
		return (
			[item["label"] for item in banner["items"]],
			{i["label"]: i["text"] for i in banner["items"]},
			banner,
		)

	def test_every_state_answers_now_next_do_in_that_order(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 8)], as_user=self.otieno_user)
		for user in (self.otieno_user, self.achieng_user, self.njeri_user, "Administrator"):
			labels, _rows, _banner = self._rows(doc, user)
			self.assertEqual(labels, ["Now", "Next", "Do"])

	def test_a_draft_tells_the_person_to_send_it(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 8)], as_user=self.otieno_user)
		_labels, rows, _banner = self._rows(doc, self.otieno_user)
		self.assertIn("Send for Approval", rows["Do"])

	def test_waiting_tells_the_approver_which_buttons_and_flags_unrecorded_days(self):
		doc = self._sent([(tf.rest_day(), 8)])
		_labels, rows, banner = self._rows(doc, self.achieng_user)
		self.assertIn("Approve", rows["Do"])
		self.assertIn("1 of these days have no record", rows["Do"])
		self.assertEqual(banner["type"], "warning")
		_labels, rows, _banner = self._rows(doc, self.otieno_user)
		self.assertIn("returns it", rows["Do"])

	def test_approved_points_the_person_at_taking_it(self):
		doc = self._approved([(tf.rest_day(), 8)])
		_labels, rows, banner = self._rows(doc, self.otieno_user)
		self.assertIn("Apply for Leave", rows["Do"])
		self.assertEqual(banner["type"], "success")

	def test_names_are_escaped(self):
		doc = self._sent([(tf.rest_day(), 8)])
		fx.as_user(
			self.achieng_user, approval.return_claim, doc.name, "<script>alert(1)</script> two hours only"
		)
		doc.reload()
		_labels, rows, _banner = self._rows(doc, self.otieno_user)
		self.assertNotIn("<script>", rows["Now"])


class TestDayCounts(unittest.TestCase):
	def test_days_read_as_a_person_writes_them(self):
		self.assertEqual(stage.days(1), "1 day")
		self.assertEqual(stage.days(1.0), "1 day")
		self.assertEqual(stage.days(1.5), "1.5 days")
		self.assertEqual(stage.days(0.25), "0.25 days")
