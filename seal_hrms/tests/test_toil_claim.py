# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Time Off in Lieu Claim: the rules, the approval path, and the time reaching the leave balance.

Otieno claims, Achieng (his leave approver) decides, Njeri is a colleague.
Each test runs inside a savepoint and is rolled back; a commit fails the test.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from seal_hrms.seal_hrms.toil import approval
from seal_hrms.seal_hrms.toil.days import PUBLIC, REST, WORKING
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf

SAVEPOINT = "toil_claim"


def _refuse_commit():
	raise AssertionError("A commit inside these tests would make their records permanent")


class ToilTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", tf.COMPANY):
			raise cls.skipTest(cls, f"{tf.COMPANY} is not on this site")
		frappe.set_user("Administrator")
		cls.otieno = tf.set_up_otieno()
		cls.otieno_user = fx.email("otieno")
		cls.achieng_user = fx.approver()
		cls.njeri = fx.ensure_employee("njeri")
		cls.njeri_user = fx.email("njeri")
		tf.policy()

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.savepoint(SAVEPOINT)
		frappe.db.before_commit.add(_refuse_commit)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.before_commit.reset()
		frappe.db.rollback(save_point=SAVEPOINT)
		# Roles are cached outside the database: a role added in a test must not outlive it.
		frappe.clear_cache(user=self.otieno_user)

	def _sent(self, lines):
		doc = tf.claim(self.otieno, lines, as_user=self.otieno_user)
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		return doc

	def _approved(self, lines):
		doc = self._sent(lines)
		fx.as_user(self.achieng_user, approval.approve, doc.name)
		doc.reload()
		return doc

	def _balance(self):
		return flt(
			get_leave_balance_on(
				self.otieno, tf.LEAVE_TYPE, today(), consider_all_leaves_in_the_allocation_period=True
			)
		)


class TestCountingTheClaim(ToilTestCase):
	def test_each_kind_of_day_is_read_from_the_calendar_and_counted(self):
		tf.policy(after_hours_rate=1, rest_day_rate=1.5, public_holiday_rate=2)
		doc = tf.claim(
			self.otieno,
			[(tf.working_day(), 3), (tf.rest_day(), 4), (tf.public_holiday(), 4)],
			as_user=self.otieno_user,
		)
		kinds = {str(line.work_date): (line.day_kind, line.credited_hours) for line in doc.lines}
		self.assertEqual(kinds[tf.working_day()], (WORKING, 3))
		self.assertEqual(kinds[tf.rest_day()], (REST, 6))
		self.assertEqual(kinds[tf.public_holiday()], (PUBLIC, 8))
		self.assertEqual(doc.total_hours, 11)
		self.assertEqual(doc.credited_hours, 17)
		self.assertEqual(doc.days, 2.13)
		self.assertEqual(doc.approver, self.achieng_user, "the leave approver, set by the server")


class TestClaimRules(ToilTestCase):
	def assertRefused(self, lines, words, as_user=None):
		with self.assertRaises(frappe.ValidationError) as caught:
			tf.claim(self.otieno, lines, as_user=as_user or self.otieno_user)
		self.assertIn(words, str(caught.exception))

	def test_a_date_twice_on_one_claim(self):
		self.assertRefused([(tf.rest_day(), 3), (tf.rest_day(), 2)], "on this claim twice")

	def test_a_future_date(self):
		self.assertRefused([(add_days(today(), 2), 3)], "has not happened yet")

	def test_under_the_minimum(self):
		tf.policy(minimum_hours=2)
		self.assertRefused([(tf.rest_day(), 1.5)], "does not count")

	def test_a_date_already_claimed(self):
		tf.claim(self.otieno, [(tf.rest_day(), 3)], as_user=self.otieno_user)
		self.assertRefused([(tf.rest_day(), 2)], "already claimed")

	def test_a_day_of_approved_leave(self):
		day = tf.working_day(at_least_days_ago=9)
		leave = frappe.new_doc("Leave Application")
		leave.employee = self.otieno
		leave.leave_type = fx.ensure_leave_type()
		leave.from_date = leave.to_date = day
		leave.leave_approver = self.achieng_user
		leave.status = "Approved"
		leave.description = "Burial in Siaya"
		leave.insert(ignore_permissions=True)
		leave.submit()
		self.assertRefused([(day, 3)], "approved leave")

	def test_a_grade_that_is_paid_for_extra_hours(self):
		frappe.db.set_value("Employee", self.otieno, "grade", tf.ensure_grade(tf.OTHER_GRADE))
		self.assertRefused([(tf.rest_day(), 3)], "paid for extra hours")

	def test_a_company_that_does_not_bank_hours(self):
		tf.policy(toil_enabled=0)
		self.assertRefused([(tf.rest_day(), 3)], "does not bank extra hours")

	def test_staff_claim_only_for_themselves(self):
		with self.assertRaises(frappe.PermissionError):
			tf.claim(self.otieno, [(tf.rest_day(), 3)], as_user=self.njeri_user)

	def test_the_claim_window(self):
		tf.policy(claim_within_days=5)
		doc = tf.claim(self.otieno, [(tf.working_day(at_least_days_ago=10), 3)], as_user=self.otieno_user)
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		self.assertIn("within 5 days", str(caught.exception))


class TestStatusMovesOnlyByDecision(ToilTestCase):
	def test_a_plain_save_cannot_change_the_status(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 3)], as_user=self.otieno_user)
		doc.status = "Approved"
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, doc.save)

	def test_a_plain_submit_is_refused(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 3)], as_user=self.otieno_user)
		with self.assertRaises(frappe.PermissionError):
			doc.submit()

	def test_a_claim_waiting_for_approval_cannot_be_edited(self):
		doc = self._sent([(tf.rest_day(), 3)])
		doc.lines[0].hours = 6
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, doc.save)
		self.assertIn("return it", str(caught.exception))


class TestDeciding(ToilTestCase):
	def test_sending_reaches_the_approver(self):
		doc = self._sent([(tf.rest_day(), 3)])
		self.assertEqual(doc.status, "Waiting for Approval")
		self.assertTrue(doc.sent_on)
		visible = fx.as_user(self.achieng_user, frappe.get_list, tf.CLAIM, pluck="name")
		self.assertIn(doc.name, visible)

	def test_a_colleague_cannot_see_it(self):
		doc = self._sent([(tf.rest_day(), 3)])
		visible = fx.as_user(self.njeri_user, frappe.get_list, tf.CLAIM, pluck="name")
		self.assertNotIn(doc.name, visible)
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, approval.approve, doc.name)

	def test_nobody_decides_their_own_claim_not_even_hr(self):
		doc = self._sent([(tf.rest_day(), 3)])
		frappe.get_doc("User", self.otieno_user).add_roles("HR Manager")
		with self.assertRaises(frappe.PermissionError) as caught:
			fx.as_user(self.otieno_user, approval.approve, doc.name)
		self.assertIn("your own claim", str(caught.exception))

	def test_returned_with_a_reason_then_corrected_and_resent(self):
		doc = self._sent([(tf.rest_day(), 3)])
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approval.return_claim, doc.name, "")
		fx.as_user(
			self.achieng_user, approval.return_claim, doc.name, "The drive ended at 13:00: claim two hours"
		)
		doc.reload()
		self.assertEqual(doc.status, "Returned")
		doc.lines[0].hours = 2
		fx.as_user(self.otieno_user, doc.save)
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		self.assertEqual(doc.status, "Waiting for Approval")
		self.assertFalse(doc.decision_note)

	def test_rejected_adds_nothing(self):
		doc = self._sent([(tf.rest_day(), 4)])
		fx.as_user(self.achieng_user, approval.reject, doc.name, "This was a voluntary event, not work")
		doc.reload()
		self.assertEqual((doc.docstatus, doc.status), (1, "Rejected"))
		self.assertEqual(self._balance(), 0)


class TestTimeReachesTheBalance(ToilTestCase):
	def test_approval_adds_the_days_to_the_leave_balance(self):
		doc = self._approved([(tf.rest_day(), 8), (tf.public_holiday(), 4)])
		self.assertEqual((doc.docstatus, doc.status), (1, "Approved"))
		self.assertEqual(doc.days_credited, 1.5)
		self.assertEqual(self._balance(), 1.5)
		self.assertTrue(doc.leave_allocation)
		self.assertEqual(str(doc.lapses_on), str(add_days(doc.earned_on, 90)))
		rows = frappe.get_all(
			"Leave Ledger Entry", filters={"custom_toil_claim": doc.name, "docstatus": 1}, pluck="leaves"
		)
		self.assertEqual(rows, [1.5], "one tagged row per claim")

	def test_a_second_claim_tops_up_the_same_allocation(self):
		first = self._approved([(tf.rest_day(), 8)])
		second = self._approved([(tf.public_holiday(), 4)])
		self.assertEqual(first.leave_allocation, second.leave_allocation)
		self.assertEqual(self._balance(), 1.5)
		allocation = frappe.get_doc("Leave Allocation", first.leave_allocation)
		self.assertEqual((allocation.new_leaves_allocated, allocation.total_leaves_allocated), (1.5, 1.5))

	def test_over_the_cap_adds_what_fits(self):
		tf.policy(balance_cap=1)
		self._approved([(tf.rest_day(), 6)])
		doc = self._approved([(tf.public_holiday(), 4)])
		self.assertEqual((doc.days_credited, doc.days_not_credited), (0.25, 0.25))
		self.assertEqual(self._balance(), 1)

	def test_the_time_cannot_be_allocated_by_hand(self):
		allocation = frappe.new_doc("Leave Allocation")
		allocation.employee = self.otieno
		allocation.leave_type = tf.LEAVE_TYPE
		allocation.from_date = add_days(today(), -10)
		allocation.to_date = add_days(today(), 10)
		allocation.new_leaves_allocated = 3
		with self.assertRaises(frappe.ValidationError) as caught:
			allocation.insert(ignore_permissions=True)
		self.assertIn("added by approving", str(caught.exception))

	def test_compensatory_leave_request_is_refused_on_this_type(self):
		request = frappe.new_doc("Compensatory Leave Request")
		request.employee = self.otieno
		request.leave_type = tf.LEAVE_TYPE
		request.work_from_date = request.work_end_date = tf.rest_day()
		request.reason = "Weekend drive"
		with self.assertRaises(frappe.ValidationError) as caught:
			request.insert(ignore_permissions=True)
		self.assertIn("Time Off in Lieu Claim", str(caught.exception))


class TestCancelling(ToilTestCase):
	def test_cancelling_takes_the_time_back_and_keeps_both_rows(self):
		doc = self._approved([(tf.rest_day(), 8)])
		doc.cancel()
		doc.reload()
		self.assertEqual((doc.docstatus, doc.status), (2, "Cancelled"))
		self.assertEqual(self._balance(), 0)
		rows = frappe.get_all(
			"Leave Ledger Entry", filters={"custom_toil_claim": doc.name, "docstatus": 1}, pluck="leaves"
		)
		self.assertEqual(sorted(rows), [-1, 1])

	def test_time_already_used_cannot_be_taken_back(self):
		doc = self._approved([(tf.rest_day(), 8)])
		leave = frappe.new_doc("Leave Application")
		leave.employee = self.otieno
		leave.leave_type = tf.LEAVE_TYPE
		leave.from_date = leave.to_date = add_days(today(), 7)
		leave.leave_approver = self.achieng_user
		leave.status = "Approved"
		leave.description = "Taking back the Kibera Sunday"
		leave.insert(ignore_permissions=True)
		leave.submit()
		with self.assertRaises(frappe.ValidationError) as caught:
			doc.cancel()
		self.assertIn("Cancel that leave first", str(caught.exception))


class TestHealthChecks(ToilTestCase):
	"""What App Health and the Working Time Policy banner say when time off cannot work."""

	def setUp(self):
		super().setUp()
		if "seal_common" not in frappe.get_installed_apps():
			self.skipTest("seal_common is not installed")

	def test_a_working_setup_reports_nothing(self):
		from seal_hrms.health import working_time as wt

		self.assertEqual(wt.time_off_leave_type_fits(), [])
		self.assertEqual(wt.time_off_has_grades(), [])

	def test_a_leave_type_that_pays_out_is_reported(self):
		from seal_hrms.health import working_time as wt

		frappe.db.set_value("Leave Type", tf.LEAVE_TYPE, "allow_encashment", 1)
		finding = wt.time_off_leave_type_fits()
		self.assertIn("can be paid out", finding.detail)

	def test_no_grade_allowed_is_reported(self):
		from seal_hrms.health import working_time as wt

		frappe.db.delete("Working Time Policy Grade", {"parent": tf.COMPANY})
		self.assertIn(tf.COMPANY, wt.time_off_has_grades().detail)

	def test_they_show_on_the_policy_form(self):
		from seal_hrms.health import working_time as wt

		for check in (wt.time_off_has_a_leave_type, wt.time_off_has_a_leave_period, wt.time_off_has_grades):
			self.assertIn("Working Time Policy", check.health_forms)
