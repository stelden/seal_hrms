# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Rolling lapse of time off in lieu (toil/lapse.py), against Frappe HR's real leave ledger.

Time is moved by setting a claim's "usable until" date, as the passing days
would. The daily job is run for the test's own allocation only (tests never run
site-wide jobs).
"""

import frappe
from frappe.utils import add_days, flt, today
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry, expire_allocation

from seal_hrms.seal_hrms.toil import lapse
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_toil_claim import ToilTestCase


class LapseTestCase(ToilTestCase):
	def _approved_days(self, days: float, lapses_on=None):
		"""An approved claim worth `days` (8 hours a day, from rest days), usable until `lapses_on`."""
		day = tf.rest_day()
		existing = frappe.db.sql(
			"""SELECT line.work_date FROM `tabTime Off in Lieu Claim Line` line
			   JOIN `tabTime Off in Lieu Claim` c ON c.name = line.parent
			   WHERE c.employee = %s AND c.docstatus < 2""",
			self.otieno,
			pluck=True,
		)
		while day in {str(d) for d in existing}:
			day = str(add_days(day, -7))
		claim = self._approved([(day, days * 8)])
		if lapses_on is not None:
			claim.db_set("lapses_on", lapses_on)
			lapse.reconcile(claim.leave_allocation)
			claim.reload()
		return claim

	def _leave(self, on_offset: int, days: int = 1, submit: bool = True):
		doc = frappe.new_doc("Leave Application")
		doc.employee = self.otieno
		doc.leave_type = tf.LEAVE_TYPE
		doc.from_date = add_days(today(), on_offset)
		doc.to_date = add_days(today(), on_offset + days - 1)
		doc.leave_approver = self.achieng_user
		doc.status = "Approved"
		doc.description = "Taking back the Kibera weekends"
		doc.insert(ignore_permissions=True)
		if submit:
			doc.submit()
		return doc

	def _lapse_rows(self, claim, docstatus=1):
		return frappe.get_all(
			"Leave Ledger Entry",
			filters={"custom_toil_claim": claim.name, "is_expired": 1, "docstatus": docstatus},
			fields=["name", "leaves", "to_date"],
		)

	def _balance_on(self, day):
		return flt(get_leave_balance_on(self.otieno, tf.LEAVE_TYPE, day))


class TestTimeLapses(LapseTestCase):
	def test_unused_time_lapses_the_day_after_its_last_usable_day(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), -1))
		rows = self._lapse_rows(claim)
		self.assertEqual([(r.leaves, str(r.to_date)) for r in rows], [(-1, str(add_days(today(), -1)))])
		self.assertEqual((claim.days_lapsed, claim.days_left), (1, 0))
		self.assertEqual(self._balance_on(today()), 0)

	def test_time_still_usable_does_not_lapse(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), 5))
		self.assertEqual(self._lapse_rows(claim), [])
		self.assertEqual(claim.days_left, 1)

	def test_running_it_again_changes_nothing(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), -1))
		lapse.reconcile(claim.leave_allocation)
		lapse.reconcile(claim.leave_allocation)
		self.assertEqual(len(self._lapse_rows(claim)), 1)
		self.assertEqual(self._lapse_rows(claim, docstatus=2), [], "nothing rewritten")

	def test_a_new_date_replaces_the_old_lapse(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), -1))
		claim.db_set("lapses_on", add_days(today(), 10))
		lapse.reconcile(claim.leave_allocation)
		self.assertEqual(self._lapse_rows(claim), [])
		self.assertEqual(self._balance_on(today()), 1)

	def test_the_daily_run_takes_one_allocation(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), 5))
		claim.db_set("lapses_on", add_days(today(), -1))
		self.assertEqual(lapse.daily(allocations=[claim.leave_allocation], commit=False), [])
		self.assertEqual(len(self._lapse_rows(claim)), 1)


class TestLeaveUsesTheRightTime(LapseTestCase):
	def test_leave_uses_the_time_that_lapses_first(self):
		soon = self._approved_days(1, lapses_on=add_days(today(), 20))
		later = self._approved_days(1, lapses_on=add_days(today(), 60))
		self._leave(3)
		soon.reload()
		later.reload()
		self.assertEqual((soon.days_used, soon.days_left), (1, 0))
		self.assertEqual((later.days_used, later.days_left), (0, 1))

	def test_leave_after_the_time_lapses_is_refused(self):
		self._approved_days(1, lapses_on=add_days(today(), 3))
		with self.assertRaises(frappe.ValidationError) as caught:
			self._leave(10, submit=False)
		self.assertIn("lapses before then", str(caught.exception))

	def test_cancelled_leave_puts_back_a_lapse_frappe_deleted(self):
		lapsed = self._approved_days(1, lapses_on=add_days(today(), -1))
		self._approved_days(1, lapses_on=add_days(today(), 60))
		leave = self._leave(3)
		self.assertEqual(len(self._lapse_rows(lapsed)), 1)
		leave.cancel()  # Frappe HR deletes a lapse row of this leave type with it (F3)
		self.assertEqual([r.leaves for r in self._lapse_rows(lapsed)], [-1], "written again")
		self.assertEqual(self._balance_on(today()), 1)


class TestCancellingAClaim(LapseTestCase):
	def test_a_claim_leave_relies_on_cannot_be_cancelled(self):
		used = self._approved_days(1, lapses_on=add_days(today(), 20))
		leave = self._leave(3)
		with self.assertRaises(frappe.ValidationError) as caught:
			used.cancel()
		self.assertIn(leave.name, str(caught.exception))

	def test_leave_moves_to_other_time_when_a_claim_is_cancelled(self):
		first = self._approved_days(1, lapses_on=add_days(today(), 20))
		other = self._approved_days(1, lapses_on=add_days(today(), 60))
		self._leave(3)
		first.cancel()
		other.reload()
		self.assertEqual((other.days_used, other.days_left), (1, 0))

	def test_a_claim_nothing_relies_on_can_be_cancelled(self):
		self._approved_days(1, lapses_on=add_days(today(), 20))
		spare = self._approved_days(1, lapses_on=add_days(today(), 60))
		self._leave(3)
		spare.cancel()
		self.assertEqual(self._balance_on(add_days(today(), 4)), 0)

	def test_cancelling_a_lapsed_claim_removes_its_lapse(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), -1))
		claim.cancel()
		self.assertEqual(self._lapse_rows(claim), [])
		self.assertEqual(self._balance_on(today()), 0)


class TestOnlyClaimsAndLeaveMoveIt(LapseTestCase):
	def test_frappe_expire_allocation_is_undone(self):
		claim = self._approved_days(1, lapses_on=add_days(today(), 30))
		allocation = frappe.get_doc("Leave Allocation", claim.leave_allocation)
		untagged = {
			"transaction_name": allocation.name,
			"is_expired": 1,
			"custom_toil_claim": ["is", "not set"],
		}
		expire_allocation(allocation)
		self.assertEqual(
			frappe.db.count("Leave Ledger Entry", {**untagged, "docstatus": 1}), 1, "the button lapsed it all"
		)
		lapse.reconcile(allocation.name)
		self.assertEqual(frappe.db.count("Leave Ledger Entry", {**untagged, "docstatus": 1}), 0)
		self.assertEqual(self._balance_on(allocation.to_date), 1)

	def test_time_cannot_be_added_to_the_ledger_by_hand(self):
		claim = self._approved_days(1)
		with self.assertRaises(frappe.ValidationError) as caught:
			create_leave_ledger_entry(
				frappe.get_doc("Leave Allocation", claim.leave_allocation),
				dict(leaves=3, from_date=today(), to_date=add_days(today(), 30), is_carry_forward=0),
			)
		self.assertIn("added by approved claims", str(caught.exception))


class TestReport(LapseTestCase):
	def test_the_report_shows_earned_used_lapsed_and_left(self):
		from seal_hrms.seal_hrms.report.time_off_in_lieu.time_off_in_lieu import execute

		self._approved_days(1, lapses_on=add_days(today(), -1))
		self._approved_days(2, lapses_on=add_days(today(), 20))
		self._leave(3)
		_columns, rows = execute({"employee": self.otieno})
		row = rows[0]
		self.assertEqual((row.earned, row.used, row.lapsed, row.left, row.lapsing_soon), (3, 1, 1, 1, 1))
		self.assertEqual(str(row.next_lapse), str(add_days(today(), 20)))
