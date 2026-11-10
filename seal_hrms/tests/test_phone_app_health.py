# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Staff get the My Desk phone app only where My Desk (seal_desk) is installed (Keith, 2026-11-11).

A deployment rule, not a dependency: seal_hrms never requires seal_desk (SEAL_DEV_RULES §3.15),
so App Health says when a site has seal_hrms without it.
"""

import ast
import pathlib
import unittest
from unittest.mock import patch

import frappe

from seal_hrms.health import my_desk

CHECK = "seal_hrms.health.my_desk.phone_app_needs_my_desk"


class TestPhoneAppNeedsMyDesk(unittest.TestCase):
	def _apps(self, *apps):
		return patch.object(my_desk.frappe, "get_installed_apps", return_value=["frappe", "erpnext", "hrms", "seal_hrms", *apps])

	def test_silent_where_my_desk_is_installed(self):
		with self._apps("seal_desk"):
			self.assertEqual(my_desk.phone_app_needs_my_desk(), [])

	def test_says_so_where_it_is_not(self):
		with self._apps():
			finding = my_desk.phone_app_needs_my_desk()
		self.assertEqual(str(finding.title), "Staff cannot get the phone app: install My Desk")
		self.assertEqual(str(finding.severity), "advisory")

	def test_it_is_on_app_health(self):
		self.assertIn(CHECK, frappe.get_hooks("app_health_checks", app_name="seal_hrms"))

	def test_the_check_does_not_import_my_desk(self):
		source = pathlib.Path(my_desk.__file__).read_text()
		names = [
			n.module if isinstance(n, ast.ImportFrom) else a.name
			for n in ast.walk(ast.parse(source))
			if isinstance(n, (ast.Import, ast.ImportFrom))
			for a in (n.names if isinstance(n, ast.Import) else [None])
		]
		self.assertFalse([n for n in names if n and n.split(".")[0] == "seal_desk"])
