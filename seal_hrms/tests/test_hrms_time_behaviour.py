# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What Frappe HR and ERPNext do today that time off in lieu and weekly timesheets rely on.

These tests pin upstream behaviour, not ours. The design in
``dev_notes/seal_hrms/WORKING_TIME_DESIGN.md`` is built on each of them; if one
fails after an upgrade, re-read that design before changing anything else.

- S1: Frappe HR's year-end job lapses an allocation only while it has a single
  ledger row. A topped-up allocation (every Compensatory Leave Request top-up)
  is never lapsed, so time off in lieu must write every lapse itself.
- S2: Cancelling a leave application deletes a lapse row of the same person
  and leave type that it has nothing to do with. Lapses must be recomputed,
  never applied once and trusted.
- S3: The leave balance is credits, less leave, less lapses; a lapse dated D
  counts from D+1, and a compensatory allocation may start at zero.
- S4: Timesheet rows placed back to back pass ERPNext's overlap checks, and a
  row ending at midnight moves the timesheet's end date into the next day.

Everything is created through the ORM (SEAL_DEV_RULES §1.9) and undone at the
end of each test. The year-end job is run with its writer replaced by a
recorder, so it reads the site and changes nothing (tests never run site-wide
jobs).
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, getdate, today
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_ledger_entry import leave_ledger_entry
from hrms.hr.utils import create_additional_leave_ledger_entry

from seal_hrms.seal_hrms.toil import guards as toil_guards
from seal_hrms.seal_hrms.toil import lapse as toil_lapse
from seal_hrms.tests import _handover_fixtures as fx

COMPANY = fx.COMPANY
LEAVE_TYPE = "Kilimani Time Off in Lieu"
ACTIVITY_TYPE = "Community Outreach"
SAVEPOINT = "hrms_time_behaviour"

CAST = {
	"chebet": ("Chebet", "Kiprop", "Female", "254722630418"),
	"mutua": ("Mutua", "Musyoka", "Male", "254733187205"),
}

# This site's Leave Type asks for notice by default; time off in lieu is often taken at short notice.
NOTICE_FIELDS = (
	"custom_minimum_leave_application_days",
	"custom_min_application_advance_days",
	"custom_min_leave_days",
	"custom_is_plannable",
)


def _refuse_commit():
	raise AssertionError("A commit inside these tests would make their records permanent")


def _employee(key: str) -> str:
	"""A member of staff with no login: none of these behaviours depends on one."""
	first, last, gender, phone = CAST[key]
	existing = frappe.db.get_value(
		"Employee", {"first_name": first, "last_name": last, "company": COMPANY}, "name"
	)
	if existing:
		return existing
	doc = frappe.new_doc("Employee")
	doc.first_name = first
	doc.last_name = last
	doc.gender = gender
	doc.date_of_birth = "1991-08-23"
	doc.date_of_joining = "2023-03-01"
	doc.status = "Active"
	doc.company = COMPANY
	doc.cell_number = phone
	doc.insert(ignore_permissions=True)
	return doc.name


def _leave_type() -> str:
	if not frappe.db.exists("Leave Type", LEAVE_TYPE):
		doc = frappe.new_doc("Leave Type")
		doc.leave_type_name = LEAVE_TYPE
		doc.is_compensatory = 1
		doc.include_holiday = 1
		doc.insert(ignore_permissions=True)
	doc = frappe.get_doc("Leave Type", LEAVE_TYPE)
	for field in NOTICE_FIELDS:
		if doc.meta.has_field(field) and doc.get(field):
			doc.set(field, 0)
	doc.save(ignore_permissions=True)
	return LEAVE_TYPE


def _activity_type() -> str:
	if not frappe.db.exists("Activity Type", ACTIVITY_TYPE):
		doc = frappe.new_doc("Activity Type")
		doc.activity_type = ACTIVITY_TYPE
		doc.insert(ignore_permissions=True)
	return ACTIVITY_TYPE


class HrmsTimeTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", COMPANY):
			raise cls.skipTest(cls, f"{COMPANY} is not on this site")
		frappe.set_user("Administrator")
		cls.chebet = _employee("chebet")
		cls.mutua = _employee("mutua")
		cls.leave_type = _leave_type()
		cls.approver = fx.approver()

	def setUp(self):
		frappe.set_user("Administrator")
		# These tests pin Frappe HR alone, so this app's time off guards stand aside even when
		# the site has a company banking time off into this leave type (another test's or a
		# browser walk's Working Time Policy for the same company).
		for module in (toil_guards, toil_lapse):
			stand_aside = patch.object(module, "toil_leave_types", return_value=set())
			stand_aside.start()
			self.addCleanup(stand_aside.stop)
		frappe.db.savepoint(SAVEPOINT)
		frappe.db.before_commit.add(_refuse_commit)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.before_commit.reset()
		frappe.db.rollback(save_point=SAVEPOINT)

	def _allocation(self, employee: str, from_date, to_date, days: float):
		doc = frappe.new_doc("Leave Allocation")
		doc.employee = employee
		doc.leave_type = self.leave_type
		doc.from_date = from_date
		doc.to_date = to_date
		doc.new_leaves_allocated = days
		doc.description = "Weekend community health drive in Kibera"
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc

	def _credit(self, allocation, days: float, from_date) -> None:
		"""Top up an allocation the way Compensatory Leave Request does."""
		create_additional_leave_ledger_entry(
			frappe.get_doc("Leave Allocation", allocation.name), days, from_date
		)

	def _lapse(self, allocation, days: float, on_date) -> str:
		"""A partial lapse row, shaped like Frappe's own "Expire Allocation" row."""
		leave_ledger_entry.create_leave_ledger_entry(
			allocation,
			dict(leaves=-days, from_date=on_date, to_date=on_date, is_expired=1, is_carry_forward=0),
		)
		return frappe.db.get_value(
			"Leave Ledger Entry",
			{"transaction_name": allocation.name, "is_expired": 1, "docstatus": 1, "to_date": on_date},
			"name",
		)

	def _approved_leave(self, employee: str, on_date):
		doc = frappe.new_doc("Leave Application")
		doc.employee = employee
		doc.leave_type = self.leave_type
		doc.from_date = on_date
		doc.to_date = on_date
		doc.leave_approver = self.approver
		doc.description = "Taking back the Saturday spent at the Kibera health drive"
		doc.status = "Approved"
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc


class TestYearEndLapse(HrmsTimeTestCase):
	"""S1: Frappe HR's year-end job and topped-up allocations."""

	def _picked_by_year_end_job(self) -> set[str]:
		picked = []
		with patch.object(leave_ledger_entry, "create_expiry_ledger_entry", side_effect=picked.extend):
			leave_ledger_entry.process_expired_allocation()
		return {row.name for row in picked}

	def test_a_topped_up_allocation_is_never_lapsed_at_year_end(self):
		single = self._allocation(self.chebet, add_days(today(), -120), add_days(today(), -91), 2)
		topped_up = self._allocation(self.chebet, add_days(today(), -90), add_days(today(), -31), 1)
		self._credit(topped_up, 1, add_days(today(), -60))

		picked = self._picked_by_year_end_job()

		self.assertIn(single.name, picked, "an allocation with one ledger row is lapsed")
		self.assertNotIn(topped_up.name, picked, "a second row hides the allocation from the job")


class TestLeaveCancellationDeletesLapses(HrmsTimeTestCase):
	"""S2: cancelling leave takes an unrelated lapse row with it."""

	def test_cancelling_leave_deletes_a_lapse_of_the_same_person_and_leave_type(self):
		mutua_allocation = self._allocation(self.mutua, add_days(today(), -30), add_days(today(), 60), 3)
		mutua_lapse = self._lapse(mutua_allocation, 1, add_days(today(), 40))
		chebet_allocation = self._allocation(self.chebet, add_days(today(), -30), add_days(today(), 60), 3)
		chebet_lapse = self._lapse(chebet_allocation, 1, add_days(today(), 40))
		leave = self._approved_leave(self.mutua, add_days(today(), 10))
		self.assertTrue(
			mutua_lapse and frappe.db.exists("Leave Ledger Entry", mutua_lapse), "the lapse is there first"
		)

		leave.cancel()

		self.assertFalse(
			frappe.db.exists("Leave Ledger Entry", mutua_lapse),
			"the lapse has nothing to do with this leave, and is deleted with it",
		)
		self.assertTrue(frappe.db.exists("Leave Ledger Entry", chebet_lapse), "another person's lapse stays")


class TestBalanceArithmetic(HrmsTimeTestCase):
	"""S3: what the leave balance counts."""

	def test_balance_is_credits_less_leave_less_lapses_from_the_day_after(self):
		allocation = self._allocation(self.chebet, add_days(today(), -7), add_days(today(), 90), 0)
		self._credit(allocation, 2, add_days(today(), -5))
		self._credit(allocation, 1.5, add_days(today(), -2))
		self._approved_leave(self.chebet, add_days(today(), 14))
		lapse_on = add_days(today(), 30)
		self._lapse(allocation, 1, lapse_on)

		self.assertEqual(get_leave_balance_on(self.chebet, self.leave_type, lapse_on), 2.5)
		self.assertEqual(get_leave_balance_on(self.chebet, self.leave_type, add_days(lapse_on, 1)), 1.5)


class TestTimesheetRows(HrmsTimeTestCase):
	"""S4: rows generated back to back, as a week grid would write them."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.activity_type = _activity_type()
		cls.monday = add_days(today(), -getdate(today()).weekday() - 14)

	def _timesheet(self, rows: list[tuple[str, str, float]]):
		"""`rows` are (from datetime, to datetime, hours)."""
		doc = frappe.new_doc("Timesheet")
		doc.company = COMPANY
		doc.employee = self.chebet
		for from_time, to_time, hours in rows:
			doc.append(
				"time_logs",
				{
					"activity_type": self.activity_type,
					"from_time": from_time,
					"to_time": to_time,
					"hours": hours,
					"description": "Household visits in Mathare North",
				},
			)
		doc.insert(ignore_permissions=True)
		return doc

	def test_back_to_back_rows_pass_the_overlap_checks(self):
		tuesday = add_days(self.monday, 1)
		doc = self._timesheet(
			[
				(f"{self.monday} 08:00:00", f"{self.monday} 12:00:00", 4),
				(f"{self.monday} 12:00:00", f"{self.monday} 16:00:00", 4),
				# The longest day a grid can write without crossing midnight.
				(f"{tuesday} 00:00:00", f"{tuesday} 12:00:00", 12),
				(f"{tuesday} 12:00:00", f"{tuesday} 23:59:00", 11 + 59 / 60),
			]
		)

		doc.submit()

		self.assertEqual(getdate(doc.start_date), getdate(self.monday))
		self.assertEqual(getdate(doc.end_date), getdate(tuesday))

	def test_a_row_ending_at_midnight_moves_the_end_date_into_the_next_day(self):
		sunday = add_days(self.monday, 6)
		doc = self._timesheet([(f"{sunday} 23:00:00", get_datetime(f"{add_days(sunday, 1)} 00:00:00"), 1)])

		self.assertEqual(getdate(doc.end_date), getdate(add_days(sunday, 1)), "Monday: outside the week")
