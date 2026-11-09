# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Claiming time off in lieu from a timesheet (timesheets/claim.py)."""

import frappe

from seal_hrms.seal_hrms.timesheets import approval, stage
from seal_hrms.seal_hrms.timesheets import claim as from_timesheet
from seal_hrms.seal_hrms.toil import approval as toil_approval
from seal_hrms.seal_hrms.toil.evidence import TIMESHEET
from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_timesheet_approval import ACTIVITY_TYPE, TimesheetTestCase


class ClaimFromTimesheetTestCase(TimesheetTestCase):
	def _approved_timesheet(self, days_hours):
		"""A timesheet with (day, hours) lines, sent and approved."""
		doc = frappe.new_doc("Timesheet")
		doc.company = tf.COMPANY
		doc.employee = self.otieno
		for day, hours in days_hours:
			doc.append(
				"time_logs",
				{
					"activity_type": ACTIVITY_TYPE,
					"from_time": f"{day} 07:00:00",
					"to_time": f"{day} {7 + hours:02d}:00:00",
					"hours": hours,
					"description": "Kibera health drive",
				},
			)
		fx.as_user(self.otieno_user, doc.insert)
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		fx.as_user(self.achieng_user, approval.approve, doc.name)
		doc.reload()
		return doc

	def _claim_from(self, timesheet, as_user=None):
		data = fx.as_user(as_user or self.otieno_user, from_timesheet.make_toil_claim, timesheet.name)
		return frappe.get_doc(data)


class TestWhatCanBeClaimed(ClaimFromTimesheetTestCase):
	def test_rest_days_and_long_days_are_offered(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6), (tf.working_day(), 10), (tf.working_day(9), 8)])
		found = {c["work_date"]: c["hours"] for c in from_timesheet.candidates(doc)}
		self.assertEqual(found, {tf.rest_day(): 6, tf.working_day(): 2})

	def test_days_already_claimed_are_left_out(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		tf.claim(self.otieno, [(tf.rest_day(), 6)], as_user=self.otieno_user)
		self.assertEqual(from_timesheet.candidates(doc), [])

	def test_a_grade_that_is_paid_gets_nothing(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		frappe.db.set_value("Employee", self.otieno, "grade", tf.ensure_grade(tf.OTHER_GRADE))
		self.assertEqual(from_timesheet.candidates(doc), [])
		with self.assertRaises(frappe.ValidationError):
			self._claim_from(doc)

	def test_a_draft_timesheet_is_not_claimed_from(self):
		doc = self._timesheet(as_user=self.otieno_user, day=tf.rest_day())
		with self.assertRaises(frappe.ValidationError):
			self._claim_from(doc)

	def test_a_colleague_cannot_claim_from_it(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		with self.assertRaises(frappe.PermissionError):
			self._claim_from(doc, as_user=self.njeri_user)


class TestTheClaimItMakes(ClaimFromTimesheetTestCase):
	def test_an_unsaved_claim_linked_to_the_timesheet(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		claim = self._claim_from(doc)
		self.assertTrue(claim.is_new())
		self.assertEqual(
			[(str(l.work_date), l.hours, l.timesheet, l.work_done) for l in claim.lines],
			[(tf.rest_day(), 6, doc.name, "Kibera health drive")],
		)
		self.assertEqual(frappe.db.count(tf.CLAIM, {"employee": self.otieno}), 0, "nothing written")

	def test_it_saves_and_the_timesheet_bears_it_out(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		claim = self._claim_from(doc)
		fx.as_user(self.otieno_user, claim.insert)
		self.assertEqual(claim.lines[0].supported_by, TIMESHEET)

	def test_the_timesheet_cannot_be_cancelled_under_an_approved_claim(self):
		doc = self._approved_timesheet([(tf.rest_day(), 8)])
		claim = self._claim_from(doc)
		fx.as_user(self.otieno_user, claim.insert)
		fx.as_user(self.otieno_user, toil_approval.send_for_approval, claim.name)
		fx.as_user(self.achieng_user, toil_approval.approve, claim.name)
		doc.reload()
		with self.assertRaises(frappe.LinkExistsError):
			doc.cancel()

	def test_authorise_first_companies_get_planned_hours_too(self):
		tf.policy(timesheet_approval=1, prior_authorisation=AUTHORISE_FIRST)
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		claim = self._claim_from(doc)
		self.assertEqual((claim.lines[0].planned_hours, claim.mode), (6, AUTHORISE_FIRST))
		fx.as_user(self.otieno_user, claim.insert)


class TestTheTimesheetSaysSo(ClaimFromTimesheetTestCase):
	def test_the_banner_names_the_button(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		rows = {i["label"]: i["text"] for i in stage.where_it_is(doc, self.otieno_user)["items"]}
		self.assertIn("Claim as Time Off in Lieu", rows["Do"])

	def test_the_form_learns_how_many_days(self):
		doc = self._approved_timesheet([(tf.rest_day(), 6)])
		frappe.set_user(self.otieno_user)
		try:
			from_timesheet.onload(doc)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(doc.get_onload().get("toil_candidates"), 1)
