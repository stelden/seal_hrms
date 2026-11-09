# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A day is either paid as overtime or banked as time off, never both.

Both directions: a claim refuses a date on an overtime slip, and an overtime
slip leaves out (when fetched from attendance) or refuses (when typed by hand)
a date on a claim that has been sent.
"""

import frappe
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.toil import approval
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_toil_claim import ToilTestCase

OVERTIME_TYPE = "Kilimani Field Overtime"
COMPONENT = "Kilimani Overtime Pay"


def _overtime_type() -> str:
	if not frappe.db.exists("Salary Component", COMPONENT):
		component = frappe.new_doc("Salary Component")
		component.salary_component = COMPONENT
		component.salary_component_abbr = "KOP"
		component.type = "Earning"
		component.insert(ignore_permissions=True)
	if not frappe.db.exists("Overtime Type", OVERTIME_TYPE):
		doc = frappe.new_doc("Overtime Type")
		doc.name = OVERTIME_TYPE
		doc.overtime_calculation_method = "Fixed Hourly Rate"
		doc.hourly_rate = 450
		doc.overtime_salary_component = COMPONENT
		doc.standard_multiplier = 1.5
		doc.applicable_for_weekend = 0
		doc.applicable_for_public_holiday = 0
		doc.insert(ignore_permissions=True)
	return OVERTIME_TYPE


def _attendance(employee: str, day: str) -> str:
	doc = frappe.new_doc("Attendance")
	doc.employee = employee
	doc.attendance_date = day
	doc.status = "Present"
	doc.company = tf.COMPANY
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _slip(employee: str, rows: list[dict]):
	doc = frappe.new_doc("Overtime Slip")
	doc.employee = employee
	doc.company = tf.COMPANY
	doc.posting_date = today()
	doc.start_date = add_days(today(), -30)
	doc.end_date = today()
	for row in rows:
		doc.append(
			"overtime_details",
			{"overtime_type": _overtime_type(), "overtime_duration": 2, "standard_working_hours": 8, **row},
		)
	doc.insert(ignore_permissions=True)
	return doc


class TestPaidOrBanked(ToilTestCase):
	def test_a_claim_refuses_a_date_on_an_overtime_slip(self):
		day = tf.rest_day()
		slip = _slip(self.otieno, [{"date": day}])
		with self.assertRaises(frappe.ValidationError) as caught:
			tf.claim(self.otieno, [(day, 3)], as_user=self.otieno_user)
		self.assertIn("paid as overtime", str(caught.exception))
		self.assertIn(slip.name, str(caught.exception))

	def test_a_deleted_draft_slip_frees_the_date(self):
		day = tf.rest_day()
		slip = _slip(self.otieno, [{"date": day}])
		slip.delete()
		tf.claim(self.otieno, [(day, 3)], as_user=self.otieno_user)

	def test_a_slip_leaves_out_a_banked_date_fetched_from_attendance(self):
		banked, paid = tf.rest_day(), tf.working_day()
		claim = tf.claim(self.otieno, [(banked, 3)], as_user=self.otieno_user)
		fx.as_user(self.otieno_user, approval.send_for_approval, claim.name)
		slip = _slip(
			self.otieno,
			[
				{"date": banked, "reference_document": _attendance(self.otieno, banked)},
				{"date": paid, "reference_document": _attendance(self.otieno, paid)},
			],
		)
		self.assertEqual([str(r.date) for r in slip.overtime_details], [paid])
		self.assertEqual(slip.total_overtime_duration, 2)
		notes = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Overtime Slip", "reference_name": slip.name},
			pluck="content",
		)
		self.assertTrue(any(claim.name in n for n in notes), "the slip says which date was left out, and why")

	def test_a_slip_refuses_a_banked_date_typed_by_hand(self):
		banked = tf.rest_day()
		claim = tf.claim(self.otieno, [(banked, 3)], as_user=self.otieno_user)
		fx.as_user(self.otieno_user, approval.send_for_approval, claim.name)
		with self.assertRaises(frappe.ValidationError) as caught:
			_slip(self.otieno, [{"date": banked}])
		self.assertIn("given as time off", str(caught.exception))

	def test_a_draft_claim_does_not_hold_the_date_against_pay(self):
		banked = tf.rest_day()
		tf.claim(self.otieno, [(banked, 3)], as_user=self.otieno_user)
		slip = _slip(self.otieno, [{"date": banked}])
		self.assertEqual(len(slip.overtime_details), 1)
