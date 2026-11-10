# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""HR's emails reach the desk bell and the phone too (seal_hrms/seal_hrms/notify.py, PUSH.md §1).

Otieno sends a time off claim and a timesheet; Achieng, his approver, gets the email
and a Notification Log about the same document. The log never carries the email's
body, sends no second email, and a failure to write it never stops the email.
"""

from unittest.mock import patch

import frappe

from seal_hrms.seal_hrms import notify
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_timesheet_approval import TimesheetTestCase


def _logs(user, name):
	return frappe.get_all(
		"Notification Log", filters={"for_user": user, "document_name": name}, fields=["type", "subject", "email_content"]
	)


class TestNotificationLogs(TimesheetTestCase):
	def setUp(self):
		super().setUp()
		p = patch("frappe.sendmail")
		self.sendmail = p.start()
		self.addCleanup(p.stop)

	def test_a_claim_sent_reaches_the_approvers_bell(self):
		doc = self._sent_claim()
		logs = _logs(self.achieng_user, doc.name)
		self.assertEqual(len(logs), 1)
		self.assertEqual(logs[0].type, "Alert")
		self.assertFalse(logs[0].email_content, "the body stays in the email")
		self.assertTrue(self.sendmail.called)

	def test_a_timesheet_sent_reaches_the_approvers_bell(self):
		ts = self._sent()
		self.assertEqual(len(_logs(self.achieng_user, ts.name)), 1)

	def test_an_unknown_recipient_is_skipped(self):
		notify.log("nobody@kilimani-office.co.ke", "Your timesheet was returned", "Timesheet", "TS-NONE")
		self.assertFalse(frappe.db.exists("Notification Log", {"document_name": "TS-NONE"}))

	def test_a_failure_never_stops_the_email(self):
		with patch("frappe.new_doc", side_effect=RuntimeError("database away")), patch("frappe.log_error") as logged:
			notify.log(self.achieng_user, "Time off claim from Otieno Ochieng", "Time Off in Lieu Claim", "TOIL-NONE")
		self.assertTrue(logged.called)

	def _sent_claim(self):
		from seal_hrms.seal_hrms.toil import approval

		doc = tf.claim(self.otieno, [(tf.working_day(), 3)], as_user=self.otieno_user)
		frappe.set_user(self.otieno_user)
		try:
			approval.send_for_approval(doc.name)
		finally:
			frappe.set_user("Administrator")
		return doc
