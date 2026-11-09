# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Timesheet approval (timesheets/approval.py): send, approve, return; who may; and stock where it is off.

Otieno records his week, Achieng approves it, Njeri is a colleague. Each test is
rolled back to a savepoint.
"""

import frappe
from frappe.utils import add_days, now_datetime

from seal_hrms.seal_hrms.timesheets import approval, stage, work
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_toil_claim import ToilTestCase

ACTIVITY_TYPE = "Community Outreach"


def _emails_to(user: str) -> int:
	return frappe.db.count("Email Queue Recipient", {"recipient": user})


class TimesheetTestCase(ToilTestCase):
	def setUp(self):
		super().setUp()
		tf.policy(timesheet_approval=1)
		if not frappe.db.exists("Activity Type", ACTIVITY_TYPE):
			activity = frappe.new_doc("Activity Type")
			activity.activity_type = ACTIVITY_TYPE
			activity.insert(ignore_permissions=True)

	def _timesheet(self, as_user=None, day=None):
		day = day or tf.working_day()
		doc = frappe.new_doc("Timesheet")
		doc.company = tf.COMPANY
		doc.employee = self.otieno
		doc.append(
			"time_logs",
			{
				"activity_type": ACTIVITY_TYPE,
				"from_time": f"{day} 08:00:00",
				"to_time": f"{day} 16:00:00",
				"hours": 8,
				"description": "Household visits in Mathare North",
			},
		)
		if as_user:
			fx.as_user(as_user, doc.insert)
		else:
			doc.insert(ignore_permissions=True)
		return doc

	def _sent(self, day=None):
		doc = self._timesheet(as_user=self.otieno_user, day=day)
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		return doc


class TestStockWhereItIsOff(TimesheetTestCase):
	def test_a_company_without_approval_submits_as_stock(self):
		tf.policy(timesheet_approval=0)
		doc = self._timesheet()
		doc.submit()
		self.assertEqual(doc.docstatus, 1)
		self.assertFalse(doc.get("custom_approval_state"))


class TestApproval(TimesheetTestCase):
	def test_a_plain_submit_is_refused(self):
		doc = self._timesheet()
		with self.assertRaises(frappe.ValidationError) as caught:
			doc.submit()
		self.assertIn("Send this timesheet for approval", str(caught.exception))

	def test_saving_sets_the_approver_and_not_sent(self):
		doc = self._timesheet(as_user=self.otieno_user)
		self.assertEqual((doc.custom_approval_state, doc.custom_approver), ("Not Sent", self.achieng_user))

	def test_send_then_approve(self):
		before = _emails_to(self.achieng_user)
		doc = self._sent()
		self.assertEqual(doc.custom_approval_state, "Waiting for Approval")
		self.assertEqual(_emails_to(self.achieng_user), before + 1)
		before = _emails_to(self.otieno_user)
		fx.as_user(self.achieng_user, approval.approve, doc.name)
		doc.reload()
		self.assertEqual(
			(doc.docstatus, doc.custom_approval_state, doc.custom_approved_by),
			(1, "Approved", self.achieng_user),
		)
		self.assertEqual(_emails_to(self.otieno_user), before + 1)

	def test_the_status_cannot_be_set_by_a_plain_save(self):
		doc = self._timesheet(as_user=self.otieno_user)
		doc.custom_approval_state = "Approved"
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, doc.save)

	def test_waiting_cannot_be_edited(self):
		doc = self._sent()
		doc.time_logs[0].description = "Changed after sending"
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, doc.save)
		self.assertIn("return it", str(caught.exception))

	def test_returned_with_a_reason_then_resent(self):
		doc = self._sent()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approval.return_timesheet, doc.name, " ")
		fx.as_user(
			self.achieng_user, approval.return_timesheet, doc.name, "Split Wednesday between the two projects"
		)
		doc.reload()
		self.assertEqual(
			(doc.custom_approval_state, doc.custom_return_reason),
			("Returned", "Split Wednesday between the two projects"),
		)
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		self.assertEqual(
			(doc.custom_approval_state, doc.custom_return_reason), ("Waiting for Approval", None)
		)


class TestWhoMay(TimesheetTestCase):
	def test_nobody_approves_their_own_not_even_hr(self):
		doc = self._sent()
		frappe.get_doc("User", self.otieno_user).add_roles("HR Manager")
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, approval.approve, doc.name)

	def test_a_colleague_cannot_approve(self):
		doc = self._sent()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, approval.approve, doc.name)

	def test_staff_cannot_cancel_an_approved_timesheet(self):
		doc = self._sent()
		fx.as_user(self.achieng_user, approval.approve, doc.name)
		doc.reload()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, doc.cancel)
		doc.reload()
		doc.cancel()  # HR (Administrator here) can
		self.assertEqual(doc.docstatus, 2)

	def test_the_line_manager_approves_where_the_company_says_so(self):
		tf.policy(timesheet_approval=1, timesheet_approver="Line manager")
		manager = fx.ensure_employee("njeri")
		frappe.db.set_value("Employee", self.otieno, "reports_to", manager)
		self.assertEqual(approval.approver_for(self.otieno, tf.COMPANY), self.njeri_user)

	def test_a_line_manager_without_a_login_falls_back_to_the_leave_approver(self):
		tf.policy(timesheet_approval=1, timesheet_approver="Line manager")
		manager = fx.ensure_employee("njeri")
		frappe.db.set_value("Employee", manager, "user_id", None)
		frappe.db.set_value("Employee", self.otieno, "reports_to", manager)
		self.assertEqual(approval.approver_for(self.otieno, tf.COMPANY), self.achieng_user)


class TestWhereItIsAndWhatIsWaiting(TimesheetTestCase):
	def test_the_banner_names_the_button_for_each_person(self):
		doc = self._timesheet(as_user=self.otieno_user)
		rows = {i["label"]: i["text"] for i in stage.where_it_is(doc, self.otieno_user)["items"]}
		self.assertIn("Send for Approval", rows["Do"])
		doc = self._sent(day=tf.working_day(at_least_days_ago=9))
		rows = {i["label"]: i["text"] for i in stage.where_it_is(doc, self.achieng_user)["items"]}
		self.assertIn("Approve", rows["Do"])

	def test_my_desk_shows_the_approver_what_to_approve_and_the_person_what_came_back(self):
		doc = self._sent()
		self.assertEqual(
			[(w.kind, w.name) for w in work.work_for(self.achieng_user)], [("approval", doc.name)]
		)
		fx.as_user(self.achieng_user, approval.return_timesheet, doc.name, "Add Friday afternoon")
		self.assertEqual([w.kind for w in work.work_for(self.otieno_user)], ["task"])


class TestHealth(TimesheetTestCase):
	def setUp(self):
		super().setUp()
		if "seal_common" not in frappe.get_installed_apps():
			self.skipTest("seal_common is not installed")

	def test_staff_with_nobody_to_approve_are_counted(self):
		from seal_hrms.health.working_time import timesheets_have_approvers

		before = timesheets_have_approvers()
		before = before.count if before else 0
		frappe.db.set_value("Employee", self.otieno, "leave_approver", None)
		self.assertEqual(timesheets_have_approvers().count, before + 1)

	def test_a_timesheet_waiting_too_long_is_reported(self):
		from seal_hrms.health.working_time import timesheets_waiting

		doc = self._sent()
		self.assertEqual(timesheets_waiting(), [])
		frappe.db.set_value("Timesheet", doc.name, "custom_sent_on", add_days(now_datetime(), -9))
		self.assertEqual(timesheets_waiting().count, 1)

	def test_a_deadline_with_approval_is_reported(self):
		from seal_hrms.health.working_time import timesheet_cutoff_with_approval

		self.assertEqual(timesheet_cutoff_with_approval(), [])
		rule = frappe.new_doc("Document Submission Cutoff")
		rule.document_type = "Timesheet"
		rule.company = tf.COMPANY
		rule.enabled = 1
		rule.cutoff_cycle = "Weekly"
		rule.cutoff_day = "Friday"
		rule.cutoff_time = "17:00:00"
		rule.deadline_falls_in = "Same Period"
		rule.insert(ignore_permissions=True)
		self.assertIn(tf.COMPANY, timesheet_cutoff_with_approval().detail)


class TestOwnEmployeeLookup(TimesheetTestCase):
	"""ERPNext's new Timesheet looks the person up by login, which staff may not filter on."""

	def test_staff_get_their_own_record_and_nothing_else(self):
		from seal_hrms.seal_hrms.task_assignment_access import my_employee_fields

		mine = fx.as_user(self.otieno_user, my_employee_fields, ["name", "company"])
		self.assertEqual((mine.name, mine.company), (self.otieno, tf.COMPANY))
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, my_employee_fields, ["bank_ac_no"])
		self.assertEqual(fx.as_user("Administrator", my_employee_fields, ["name"]), {})
