# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Self-Service on My Desk (seal_desk P6), and the page seal_hrms ships for it.

The figures are counted for the person's own Employee, through their own permissions.
The first classes need no desk; the last one is skipped where seal_desk is absent.
"""

import json
import pathlib
import unittest
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from seal_hrms.seal_hrms import self_service_status as status
from seal_hrms.tests import _handover_fixtures as fx

HOST = "seal_desk"
APP = "seal_hrms"
DOCTYPES = {"Leave Application", "Expense Claim", "Employee Advance", "Timesheet"}


class TestSelfServiceFigures(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.user = fx.email("wanjiku")

	def counted(self, user, readable=None):
		"""The figures, with the filters each count asked get_list for."""
		asked = {}
		real = frappe.get_list

		def spy(doctype, *args, **kwargs):
			if doctype in DOCTYPES:
				asked.setdefault(doctype, []).append(kwargs.get("filters"))
				return [frappe._dict(n=2)]
			return real(doctype, *args, **kwargs)

		with patch.object(frappe, "get_list", spy):
			figures = status.self_service(user, readable)
		return figures, asked

	def test_every_count_is_for_the_persons_own_employee(self):
		figures, asked = self.counted(self.user)
		self.assertEqual({f.doctype for f in figures}, DOCTYPES)
		for doctype, calls in asked.items():
			for filters in calls:
				self.assertIn(["employee", "=", self.wanjiku], filters, doctype)
		self.assertTrue(all(f.count == 2 for f in figures))

	def test_someone_with_no_employee_gets_no_figures_at_all(self):
		figures, asked = self.counted("Administrator")
		self.assertEqual((figures, asked), ([], {}))

	def test_a_doctype_the_person_cannot_read_is_left_out(self):
		figures, _asked = self.counted(self.user, readable={"Timesheet"})
		self.assertEqual([f.key for f in figures], ["timesheets_draft"])

	def test_each_figure_opens_a_list_with_exactly_its_conditions(self):
		figures, _asked = self.counted(self.user)
		for f in figures:
			with self.subTest(f.key):
				self.assertEqual(len(f.route_options()), len(f.filters))


class TestShippedWithTheApp(unittest.TestCase):
	"""The Employee Self-Service page and its parts ship as files (seal_desk §18.5); Frappe
	imports no desk_page or desk_widget folder itself, so they are inert without the desk."""

	ROOT = pathlib.Path(frappe.get_app_path(APP), "seal_hrms")

	def files(self, folder):
		return sorted((self.ROOT / folder).glob("*/*.json"))

	def test_every_shipped_page_and_part_is_standard_and_ours(self):
		found = self.files("desk_page") + self.files("desk_widget")
		self.assertTrue(found)
		for path in found:
			data = json.loads(path.read_text())
			with self.subTest(path.name):
				self.assertEqual((data["is_standard"], data["module"]), (1, "SEAL HRMS"))

	def test_a_shipped_page_carries_no_site_choices_and_keeps_its_row_names(self):
		for path in self.files("desk_page"):
			data = json.loads(path.read_text())
			with self.subTest(path.name):
				self.assertEqual((data["role_profiles"], data["status"], data.get("published_json")), ([], "Draft", None))
				self.assertTrue(all(row.get("name") for row in data["items"] + data["actions"]))

	def test_every_group_a_shipped_part_names_is_declared(self):
		declared = {g["key"] for g in frappe.get_hooks("seal_desk_cue_groups", app_name=APP) or []}
		for path in self.files("desk_widget"):
			data = json.loads(path.read_text())
			if data["widget_type"] == "Standard Group" and data["standard_group"].startswith(APP + "."):
				self.assertIn(data["standard_group"], declared)


@unittest.skipUnless(HOST in frappe.get_installed_apps(), f"{HOST} is not installed")
class TestSelfServiceOnTheDesk(unittest.TestCase):
	def test_the_desk_runs_the_group_and_accepts_it(self):
		from frappe.utils import getdate
		from seal_desk.role_center import contract, registry
		from seal_desk.role_center.schema import DeskContext

		info = registry.standard_groups()["seal_hrms.self_service"]
		self.assertEqual((info.renders_as, info.app), ("cues", APP))
		found, error = contract.run_group(info, DeskContext(user="Administrator", company=None, today=getdate(), readable=frozenset(DOCTYPES)))
		self.assertIsNone(error)
		self.assertEqual(found, [])  # Administrator has no Employee
