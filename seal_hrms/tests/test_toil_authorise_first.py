# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Authorise first, then confirm the hours; the claim's emails, process map and My Desk rows."""

import unittest

import frappe
from frappe.utils import add_days, now_datetime, today

from seal_hrms.seal_hrms.process_maps import toil_claim as process_map
from seal_hrms.seal_hrms.toil import approval, notifications, work
from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST, CLAIM_AFTERWARDS
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_toil_claim import ToilTestCase


def _emails_to(user: str) -> int:
	return frappe.db.count("Email Queue Recipient", {"recipient": user})


class AuthoriseFirstTestCase(ToilTestCase):
	def setUp(self):
		super().setUp()
		tf.policy(prior_authorisation=AUTHORISE_FIRST)

	def _planned(self, lines):
		doc = frappe.new_doc(tf.CLAIM)
		doc.employee = self.otieno
		doc.company = tf.COMPANY
		for day, hours in lines:
			doc.append(
				"lines",
				{"work_date": day, "planned_hours": hours, "work_done": "Weekend immunisation outreach"},
			)
		fx.as_user(self.otieno_user, doc.insert)
		return doc

	def _authorised(self, lines):
		doc = self._planned(lines)
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		fx.as_user(self.achieng_user, approval.authorise, doc.name)
		doc.reload()
		return doc

	def _confirm(self, doc, hours):
		for line in doc.lines:
			line.hours = hours
		fx.as_user(self.otieno_user, doc.save)
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		return doc


class TestAuthoriseFirst(AuthoriseFirstTestCase):
	def test_the_mode_is_stamped_when_the_claim_is_made(self):
		doc = self._planned([(tf.rest_day(), 6)])
		tf.policy(prior_authorisation=CLAIM_AFTERWARDS)
		doc.reload()
		self.assertEqual(doc.mode, AUTHORISE_FIRST, "a later change of policy does not move it")

	def test_planned_days_may_be_in_the_future(self):
		doc = self._planned([(add_days(today(), 6), 4)])
		self.assertEqual(doc.total_hours, 4)

	def test_it_cannot_go_straight_to_approval(self):
		doc = self._planned([(tf.rest_day(), 6)])
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		self.assertIn("authorised first", str(caught.exception))

	def test_the_whole_path(self):
		doc = self._authorised([(tf.rest_day(), 6)])
		self.assertEqual(doc.status, approval.AUTHORISED)
		self.assertTrue(doc.lines[0].authorised)
		self.assertEqual(doc.authorised_by, self.achieng_user)
		doc = self._confirm(doc, 8)
		self.assertEqual(doc.status, approval.WAITING)
		fx.as_user(self.achieng_user, approval.approve, doc.name)
		doc.reload()
		self.assertEqual((doc.status, doc.days_credited), (approval.APPROVED, 1))

	def test_waiting_for_authorisation_cannot_be_edited(self):
		doc = self._planned([(tf.rest_day(), 6)])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		doc.reload()
		doc.lines[0].planned_hours = 10
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, doc.save)

	def test_hours_worked_are_needed_to_send_it(self):
		doc = self._authorised([(tf.rest_day(), 6)])
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		self.assertIn("extra hours worked", str(caught.exception))

	def test_a_day_not_authorised_cannot_be_added_afterwards(self):
		doc = self._authorised([(tf.rest_day(), 6)])
		doc.lines[0].hours = 6
		doc.append("lines", {"work_date": tf.public_holiday(), "hours": 5, "work_done": "Clinic open day"})
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, doc.save)
		self.assertIn("was not authorised", str(caught.exception))

	def test_returned_before_authorising_goes_back_to_the_person(self):
		doc = self._planned([(tf.rest_day(), 6)])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		fx.as_user(self.achieng_user, approval.return_claim, doc.name, "Plan four hours, not six")
		doc.reload()
		self.assertEqual(doc.status, approval.RETURNED)

	def test_returned_after_authorising_keeps_the_authorisation(self):
		doc = self._confirm(self._authorised([(tf.rest_day(), 6)]), 9)
		fx.as_user(self.achieng_user, approval.return_claim, doc.name, "The drive ended at 15:00")
		doc.reload()
		self.assertEqual(doc.status, approval.AUTHORISED)
		self.assertTrue(doc.lines[0].authorised)

	def test_rejected_at_authorisation(self):
		doc = self._planned([(tf.rest_day(), 6)])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		fx.as_user(self.achieng_user, approval.reject, doc.name, "Not needed this month")
		doc.reload()
		self.assertEqual((doc.docstatus, doc.status), (1, approval.REJECTED))


class TestEmails(AuthoriseFirstTestCase):
	def test_each_move_reaches_the_person_who_acts_next(self):
		doc = self._planned([(tf.rest_day(), 6)])
		before = _emails_to(self.achieng_user)
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		self.assertEqual(_emails_to(self.achieng_user), before + 1, "the approver is asked")
		before = _emails_to(self.otieno_user)
		fx.as_user(self.achieng_user, approval.authorise, doc.name)
		self.assertEqual(_emails_to(self.otieno_user), before + 1, "the person is told")

	def test_templates_are_made_once_and_never_overwritten(self):
		frappe.db.delete("Email Template", {"name": ["like", notifications.PREFIX + "%"]})
		notifications.ensure_templates()
		self.assertEqual(
			frappe.db.count("Email Template", {"name": ["like", notifications.PREFIX + "%"]}),
			len(notifications.TEMPLATES),
		)
		frappe.db.set_value(
			"Email Template", notifications.APPROVED, "subject", "Karibu: your time off is in"
		)
		notifications.ensure_templates()
		self.assertEqual(
			frappe.db.get_value("Email Template", notifications.APPROVED, "subject"),
			"Karibu: your time off is in",
		)


class TestProcessMap(unittest.TestCase):
	def _check(self, definition):
		if "seal_common" not in frappe.get_installed_apps():
			self.skipTest("seal_common is not installed")
		from seal_common.process_map import check_definition

		self.assertEqual(check_definition(definition), [])

	def _statuses(self, **facts):
		definition = process_map.build(process_map.ClaimFacts(**facts))
		self._check(definition)
		return {step["id"]: step["status"] for step in definition["steps"]}

	def test_claim_afterwards(self):
		self.assertEqual(
			self._statuses(authorise_first=False, status="Draft", docstatus=0),
			{"claim": "current", "approve": "pending", "added": "pending", "rejected": "skipped"},
		)
		self.assertEqual(
			self._statuses(authorise_first=False, status="Approved", docstatus=1, validity_days=90),
			{"claim": "past", "approve": "past", "added": "end", "rejected": "skipped"},
		)
		self.assertEqual(
			self._statuses(authorise_first=False, status="Rejected", docstatus=1),
			{"claim": "past", "approve": "past", "added": "skipped", "rejected": "interrupted"},
		)

	def test_authorise_first(self):
		self.assertEqual(
			self._statuses(authorise_first=True, status="Authorised", docstatus=0, authorised=True),
			{
				"plan": "past",
				"authorise": "past",
				"confirm": "current",
				"approve": "pending",
				"added": "pending",
				"rejected": "skipped",
			},
		)
		statuses = self._statuses(authorise_first=True, status="Rejected", docstatus=1, authorised=False)
		self.assertEqual(
			(statuses["authorise"], statuses["confirm"], statuses["rejected"]),
			("past", "skipped", "interrupted"),
		)

	def test_cancelled_after_approval(self):
		statuses = self._statuses(authorise_first=False, status="Cancelled", docstatus=2)
		self.assertEqual(statuses["added"], "interrupted")

	def test_pills_come_from_the_policy(self):
		definition = process_map.build(
			process_map.ClaimFacts(
				authorise_first=False, status="Draft", docstatus=0, claim_within_days=30, validity_days=0
			)
		)
		pills = {step["id"]: [p["label"] for p in step["pills"]] for step in definition["steps"]}
		self.assertEqual(pills["claim"], ["Send within 30 days"])
		self.assertEqual(pills["added"], [], "no limit set, no pill")


class TestWaitingForYou(AuthoriseFirstTestCase):
	def test_the_approver_sees_what_to_decide_and_the_person_what_to_do(self):
		doc = self._planned([(tf.rest_day(), 6)])
		self.assertEqual([w.kind for w in work.work_for(self.otieno_user)], ["draft"])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		decide = work.work_for(self.achieng_user)
		self.assertEqual([(w.kind, w.name) for w in decide], [("approval", doc.name)])
		fx.as_user(self.achieng_user, approval.authorise, doc.name)
		self.assertEqual([w.title for w in work.work_for(self.otieno_user)], ["Confirm the hours you worked"])

	def test_time_lapsing_soon_is_flagged(self):
		tf.policy(prior_authorisation=CLAIM_AFTERWARDS)
		doc = self._approved([(tf.rest_day(), 8)])
		doc.db_set("lapses_on", add_days(today(), 5))
		doc.db_set("days_left", 1)
		self.assertIn("notification", [w.kind for w in work.work_for(self.otieno_user)])

	def test_nobody_is_asked_to_decide_their_own(self):
		tf.policy(prior_authorisation=CLAIM_AFTERWARDS)
		doc = self._sent([(tf.rest_day(), 8)])
		frappe.db.set_value(tf.CLAIM, doc.name, "approver", self.otieno_user)
		self.assertEqual([w for w in work.work_for(self.otieno_user) if w.kind == "approval"], [])


class TestClaimsWaitingTooLong(AuthoriseFirstTestCase):
	def setUp(self):
		super().setUp()
		if "seal_common" not in frappe.get_installed_apps():
			self.skipTest("seal_common is not installed")

	def test_a_claim_waiting_past_the_limit_is_reported(self):
		from seal_hrms.health.working_time import time_off_claims_waiting

		doc = self._planned([(tf.rest_day(), 6)])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		self.assertEqual(time_off_claims_waiting(), [])
		frappe.db.set_value(tf.CLAIM, doc.name, "sent_on", add_days(now_datetime(), -10))
		self.assertEqual(time_off_claims_waiting().count, 1)


class TestSelfService(AuthoriseFirstTestCase):
	def test_claims_in_flight_are_counted(self):
		from seal_hrms.seal_hrms.self_service_status import self_service

		doc = self._planned([(tf.rest_day(), 6)])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		figures = {f.key: f.count for f in fx.as_user(self.otieno_user, self_service, self.otieno_user)}
		self.assertEqual(figures.get("toil_in_approval"), 1)


class TestMyDeskRows(AuthoriseFirstTestCase):
	def test_the_desk_adapter_returns_list_rows(self):
		if "seal_desk" not in frappe.get_installed_apps():
			self.skipTest("seal_desk is not installed")
		from seal_desk.role_center.schema import ListRow

		from seal_hrms.desk.providers import time_rows

		doc = self._planned([(tf.rest_day(), 6)])
		fx.as_user(self.otieno_user, approval.send_for_authorisation, doc.name)
		rows = time_rows(frappe._dict(user=self.achieng_user))
		self.assertEqual(len(rows), 1)
		self.assertIsInstance(rows[0], ListRow)
		self.assertIn("Otieno", rows[0].title)
