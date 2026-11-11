# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Who can read pay in the Kenya Salary Register (security finding, 2026-11-10; fixed in 1.28.1).

The report listed Employee and Employee Self Service among its roles and read every salary slip
with a raw query, so staff were kept out only by lacking Report on Salary Slip. Pinned here:

- the shipped report names only Frappe HR's Salary Register roles, HR User and HR Manager;
- a member of staff calling the report gets nothing, whatever roles the report lists;
- a payroll officer whom no User Permission limits sees every slip in the period;
- an HR User whom a User Permission limits to her own Employee record sees only what the Salary
  Slip list would show her, not her colleagues' pay.

Cast from `_phone_cast` (Baraka Mutua and Kiprop Chebet, staff; Zawadi Njoroge, Baraka's line
manager). Rows are made through the ORM and rolled back with each test; no commit is allowed.
"""

import json
import os

import frappe
from frappe.desk.query_report import run as run_report

from seal_hrms.seal_hrms.report.kenya_salary_register import kenya_salary_register as register
from seal_hrms.tests._phone_cast import COMPANY, CastTestCase, as_user

REPORT = "Kenya Salary Register"
FROM, TO = "2026-10-01", "2026-10-31"
PAYROLL_OFFICER = "wanjiru.kariuki@mvua-health.co.ke"


def _filters(**extra):
	return {"company": COMPANY, "from_date": FROM, "to_date": TO, "docstatus": "Draft", **extra}


def _slip_names(rows):
	"""The salary slip IDs (first column) of the report's rows."""
	return {row[0] for row in rows}


class TestKenyaSalaryRegisterAccess(CastTestCase):
	def setUp(self):
		super().setUp()
		self.baraka_slip = self._slip(self.baraka, 86_500)
		self.kiprop_slip = self._slip(self.kiprop, 112_000)

	def _slip(self, employee, gross):
		"""A draft October slip. Arranged through the ORM without Frappe HR's payroll validation
		(which needs a salary structure assignment): the slip's figures are not under test."""
		doc = frappe.new_doc("Salary Slip")
		doc.update(
			{
				"employee": employee,
				"employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
				"company": COMPANY,
				"currency": frappe.get_cached_value("Company", COMPANY, "default_currency"),
				"exchange_rate": 1,
				"posting_date": TO,
				"start_date": FROM,
				"end_date": TO,
				"payroll_frequency": "Monthly",
				"total_working_days": 22,
				"payment_days": 22,
				"gross_pay": gross,
				"total_deduction": round(gross * 0.28),
				"net_pay": gross - round(gross * 0.28),
			}
		)
		doc.flags.ignore_validate = True
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_links = True
		doc.insert(ignore_permissions=True)
		return doc.name

	def _payroll_officer(self):
		"""Wanjiru Kariuki, payroll officer: HR User, with no Employee record and so no User
		Permission narrowing what she sees."""
		user = frappe.new_doc("User")
		user.update(
			{
				"email": PAYROLL_OFFICER,
				"first_name": "Wanjiru",
				"last_name": "Kariuki",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("HR User")
		self.addCleanup(frappe.clear_cache, user=PAYROLL_OFFICER)
		return PAYROLL_OFFICER

	def test_shipped_report_names_only_payroll_roles(self):
		path = os.path.join(os.path.dirname(register.__file__), "kenya_salary_register.json")
		with open(path) as f:
			roles = {row["role"] for row in json.load(f)["roles"]}
		self.assertEqual(roles, {"HR User", "HR Manager"})

	def test_staff_cannot_run_the_report(self):
		with self.assertRaises(frappe.PermissionError):
			as_user(self.baraka_user, run_report, REPORT, filters=_filters())

	def test_staff_get_nothing_even_where_the_report_lets_them_in(self):
		# Calling the report's own code stands for a site where a role added to the report lets
		# staff past the report's door: the report must still refuse them.
		with self.assertRaises(frappe.PermissionError):
			as_user(self.baraka_user, register.execute, _filters())

	def test_payroll_officer_sees_every_slip_in_the_period(self):
		officer = self._payroll_officer()
		_columns, rows = as_user(officer, register.execute, _filters())
		self.assertTrue({self.baraka_slip, self.kiprop_slip} <= _slip_names(rows))

	def test_payroll_officer_can_narrow_to_one_employee(self):
		officer = self._payroll_officer()
		_columns, rows = as_user(officer, register.execute, _filters(employee=self.kiprop))
		self.assertEqual(_slip_names(rows), {self.kiprop_slip})

	def test_hr_user_limited_to_her_own_record_does_not_see_colleagues_pay(self):
		self.assertTrue(
			frappe.db.exists("User Permission", {"user": self.zawadi_user, "allow": "Employee"}),
			"the cast's Employee insert should have given Zawadi a User Permission on her own record",
		)
		frappe.get_doc("User", self.zawadi_user).add_roles("HR User")
		result = as_user(self.zawadi_user, register.execute, _filters())
		rows = result[1] if result else []
		self.assertFalse({self.baraka_slip, self.kiprop_slip} & _slip_names(rows))
