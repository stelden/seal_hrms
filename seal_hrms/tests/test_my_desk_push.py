# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""HR notices on staff phones (seal_hrms/my_desk/push.py; My Desk phone app phase P6).

Otieno applies and claims; Achieng approves his leave, time off, timesheets and expense
claims; Njeri is a colleague who decides nothing until she stands in for Achieng.

Pinned: the hooks are declared exactly as the P6 contract says (seal_common and seal_desk
read them); a notice waiting for the recipient's decision is not "hr" (it is seal_desk's
"approvals"), the same notice to the person it is about is; a decided record is "hr" for
everyone; records that are not HR's are no kind of ours; the classifier never raises. What
shows on a locked phone: payslips, payout changes and advances subject only, payslips with a
subject that carries no amount, medical leave without its type; everything else is left to
seal_common. Where seal_common's push engine is importable, its own message builder is run
with these answers.

Rows are created and rolled back per test (ToilTestCase); no SMS or email leaves the process.
"""

import ast
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

import frappe

from seal_hrms.my_desk import push
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
# Modules, not classes: a TestCase imported by name would be collected and run again here.
from seal_hrms.tests import test_my_desk_approvals as approval_tests
from seal_hrms.tests import test_timesheet_approval as timesheet_tests

ApprovalsTestCase = approval_tests.ApprovalsTestCase

APP = "seal_hrms"


def _log(for_user, doctype, name, subject="", email_content=""):
	"""A Notification Log as the hooks receive it (unsaved: the classifier reads fields only)."""
	return frappe.get_doc(
		{
			"doctype": "Notification Log",
			"for_user": for_user,
			"type": "Alert",
			"document_type": doctype,
			"document_name": name,
			"subject": subject,
			"email_content": email_content,
		}
	)


class TestTheContract(unittest.TestCase):
	"""What seal_common and seal_desk read, exactly as agreed for P6."""

	def _hooks(self):
		return frappe.get_module(f"{APP}.hooks")

	def test_hooks_are_declared_as_the_contract_says(self):
		hooks = self._hooks()
		self.assertEqual(hooks.push_kind_labels, [{"key": "hr", "label": "HR"}])
		self.assertEqual(hooks.push_kind_providers, ["seal_hrms.my_desk.push.kind_of"])
		self.assertEqual(hooks.push_message_providers, ["seal_hrms.my_desk.push.message_for"])
		self.assertIs(frappe.get_attr(hooks.push_kind_providers[0]), push.kind_of)
		self.assertIs(frappe.get_attr(hooks.push_message_providers[0]), push.message_for)

	def test_the_module_imports_neither_seal_common_nor_seal_desk_on_load(self):
		tree = ast.parse(pathlib.Path(push.__file__).read_text())
		top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
		names = [a.name for n in top if isinstance(n, ast.Import) for a in n.names] + [n.module or "" for n in top if isinstance(n, ast.ImportFrom)]
		self.assertEqual([n for n in names if n.split(".")[0] in ("seal_common", "seal_desk")], [])

	def test_every_kind_doctype_is_one_the_section_claims(self):
		claims = set(frappe.get_module(f"{APP}.hooks").seal_desk_app_sections[0]["claims"])
		self.assertEqual(push.HR_DOCTYPES - claims, set())

	def test_medical_leave_types_are_told_apart(self):
		for name in ("Sick Leave", "Medical Leave", "Maternity Leave", "Paternity Leave", "Hospitalisation Leave", "Convalescence Leave"):
			with self.subTest(name=name):
				self.assertTrue(push.is_medical(name))
		for name in ("Annual Leave", "Compassionate Leave", "Study Leave", "Leave Without Pay", "Time Off in Lieu"):
			with self.subTest(name=name):
				self.assertFalse(push.is_medical(name))


class TestKindOfLeave(ApprovalsTestCase):
	def test_waiting_for_the_approver_is_an_approval_not_hr(self):
		la = fx.leave(self.otieno, 20, 2)
		self.assertIsNone(push.kind_of(_log(self.achieng_user, "Leave Application", la.name)))
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Leave Application", la.name)), push.HR)
		# A colleague told about it (say, as stand-in for the handover) decides nothing.
		self.assertEqual(push.kind_of(_log(self.njeri_user, "Leave Application", la.name)), push.HR)

	def test_a_stand_in_holding_the_approvals_gets_an_approval(self):
		la = fx.leave(self.otieno, 20, 2)
		self.njeri_stands_in_for_achieng("leave_approval", ("Leave Application", la.name))
		self.assertIsNone(push.kind_of(_log(self.njeri_user, "Leave Application", la.name)))

	def test_once_decided_it_is_hr_for_everyone(self):
		from seal_hrms.my_desk import approvals

		la = fx.leave(self.otieno, 20, 2)
		fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Approve")
		self.assertEqual(push.kind_of(_log(self.achieng_user, "Leave Application", la.name)), push.HR)
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Leave Application", la.name)), push.HR)

	def test_the_applicant_is_never_asked_to_decide_their_own(self):
		la = fx.leave(self.otieno, 20, 2)
		la.db_set("leave_approver", self.otieno_user)
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Leave Application", la.name)), push.HR)


class TestKindOfTimeOff(ApprovalsTestCase):
	def test_a_sent_claim_is_an_approval_for_the_approver_only(self):
		doc = self._sent([(tf.working_day(), 3)])
		self.assertIsNone(push.kind_of(_log(self.achieng_user, "Time Off in Lieu Claim", doc.name)))
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Time Off in Lieu Claim", doc.name)), push.HR)
		self.assertEqual(push.kind_of(_log(self.njeri_user, "Time Off in Lieu Claim", doc.name)), push.HR)


class TestKindOfExpense(approval_tests.TestExpenseClaims):
	"""Borrows the expense tests' claim fixture; their own tests run in their module, not again here."""

	def test_a_draft_claim_is_an_approval_for_the_expense_approver(self):
		ec = self._claim()
		self.assertIsNone(push.kind_of(_log(self.achieng_user, "Expense Claim", ec.name)))
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Expense Claim", ec.name)), push.HR)
		ec.db_set("approval_status", "Rejected")
		self.assertEqual(push.kind_of(_log(self.achieng_user, "Expense Claim", ec.name)), push.HR)


for _inherited in [n for n in dir(approval_tests.TestExpenseClaims) if n.startswith("test_")]:
	# Keep this class to the kind of an expense claim: the inherited tests already run in their own module.
	setattr(TestKindOfExpense, _inherited, None)


class TestKindOfTimesheet(timesheet_tests.TimesheetTestCase):
	def test_a_sent_week_is_an_approval_for_the_approver(self):
		ts = self._sent()
		self.assertIsNone(push.kind_of(_log(self.achieng_user, "Timesheet", ts.name)))
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Timesheet", ts.name)), push.HR)


for _inherited in [n for n in dir(timesheet_tests.TimesheetTestCase) if n.startswith("test_")]:
	setattr(TestKindOfTimesheet, _inherited, None)


class TestKindOfAnythingElse(ApprovalsTestCase):
	def test_records_that_are_not_hr_are_no_kind_of_ours(self):
		self.assertIsNone(push.kind_of(_log(self.otieno_user, "ToDo", "anything")))
		self.assertIsNone(push.kind_of(_log(self.otieno_user, None, None)))
		self.assertIsNone(push.kind_of(_log(self.otieno_user, "Leave Application", None)))

	def test_a_record_deleted_since_is_still_hr(self):
		self.assertEqual(push.kind_of(_log(self.otieno_user, "Salary Slip", "Sal Slip/HR-EMP-GONE/00001")), push.HR)

	def test_it_never_raises(self):
		la = fx.leave(self.otieno, 20, 2)
		with patch.object(push, "waiting_for", side_effect=RuntimeError("database went away")), patch("frappe.log_error") as logged:
			self.assertIsNone(push.kind_of(_log(self.achieng_user, "Leave Application", la.name)))
		logged.assert_called_once()


class TestWhatShowsOnALockedPhone(ApprovalsTestCase):
	def test_pay_and_payout_notices_are_subject_only(self):
		for doctype in ("Payout Change Request", "Employee Advance"):
			with self.subTest(doctype=doctype):
				self.assertEqual(push.message_for(_log(self.otieno_user, doctype, "X-0001")), {"private": True})

	def test_a_payslip_subject_names_the_period_never_the_amount(self):
		slip = frappe._dict(employee=self.otieno, employee_name="Otieno Ochieng", start_date="2026-10-01", end_date="2026-10-31")
		real = frappe.db.get_value

		def get_value(doctype, *args, **kwargs):
			return slip if doctype == "Salary Slip" else real(doctype, *args, **kwargs)

		with patch("frappe.db.get_value", side_effect=get_value):
			mine = push.message_for(_log(self.otieno_user, "Salary Slip", "Sal Slip/1", subject="Salary Slip: net pay KES 84,250"))
			hrs = push.message_for(_log(self.achieng_user, "Salary Slip", "Sal Slip/1"))
		self.assertTrue(mine["private"])
		self.assertTrue(mine["subject"].startswith("Your payslip for"))
		self.assertNotIn("84", mine["subject"])
		self.assertTrue(hrs["subject"].startswith("Payslip for Otieno Ochieng"))

	def test_medical_leave_hides_its_type_and_ordinary_leave_is_left_alone(self):
		la = fx.leave(self.otieno, 20, 2)
		self.assertIsNone(push.message_for(_log(self.achieng_user, "Leave Application", la.name)))
		with patch.object(push, "is_medical", return_value=True):
			theirs = push.message_for(_log(self.achieng_user, "Leave Application", la.name, subject="Sick Leave for Otieno"))
			mine = push.message_for(_log(self.otieno_user, "Leave Application", la.name))
		self.assertEqual(theirs["subject"], f"Leave application from {la.employee_name}")
		self.assertTrue(theirs["private"])
		self.assertEqual(mine["subject"], "An update on your leave application")

	def test_other_records_are_left_to_seal_common(self):
		self.assertIsNone(push.message_for(_log(self.otieno_user, "ToDo", "x")))
		self.assertIsNone(push.message_for(_log(self.otieno_user, "Task Assignment", "TA-0001")))


def _engine_here() -> bool:
	"""seal_common's push engine with the message-provider hook (P2c) is importable."""
	try:
		if not importlib.util.find_spec("seal_common.messaging.push"):
			return False
		return hasattr(importlib.import_module("seal_common.messaging.push"), "PROVIDER_HOOK")
	except Exception:
		return False


@unittest.skipUnless(_engine_here(), "seal_common's push engine (P2) is not here")
class TestSealCommonReadsTheAnswer(ApprovalsTestCase):
	"""seal_common's own message builder, with this app's provider declared."""

	def test_a_payout_notice_goes_subject_only(self):
		from seal_common.messaging import push as engine

		log = _log(self.otieno_user, "Payout Change Request", "PCR-2026-00004", subject="Payout change approved", email_content="<p>New account ending 6311 from 1 Dec</p>")
		with patch("frappe.get_hooks", side_effect=lambda hook, *a, **k: [f"{APP}.my_desk.push.message_for"] if hook == engine.PROVIDER_HOOK else []), patch.object(engine, "site_name", return_value="Kilimani"):
			message = engine.message_for_log(log)
		self.assertEqual(message["body"], "Payout change approved")

	def test_an_ordinary_leave_notice_keeps_its_summary(self):
		from seal_common.messaging import push as engine

		la = fx.leave(self.otieno, 20, 2)
		log = _log(self.achieng_user, "Leave Application", la.name, subject="Leave for Otieno Ochieng", email_content="<p>2 days from next month</p>")
		with patch("frappe.get_hooks", side_effect=lambda hook, *a, **k: [f"{APP}.my_desk.push.message_for"] if hook == engine.PROVIDER_HOOK else []), patch.object(engine, "site_name", return_value="Kilimani"):
			message = engine.message_for_log(log)
		self.assertEqual(message["body"], "Leave for Otieno Ochieng\n2 days from next month")
