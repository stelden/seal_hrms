# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""`/hrms` opens My Desk (PWA-4; seal_hrms/my_desk/links.py, hooks.website_redirects).

The mapping is checked against what Frappe HR actually produces: the links its push messages
carry (`pwa_notification.py`) and the routes of its app (`frontend/src/router/*.js`), read
from the hrms checkout, so an upstream route nobody mapped shows here. The redirect rule is
matched the way Frappe matches it, without touching the site's redirect cache.
"""

import pathlib
import re
import unittest

import frappe

from seal_hrms.my_desk.links import COLLECTIONS, SCREENS, SELF_SERVICE, target


def _rule():
	rules = [r for r in frappe.get_hooks("website_redirects", app_name="seal_hrms") if "hrms" in r["source"]]
	assert len(rules) == 1, rules
	return rules[0]


def _redirect(path: str) -> str | None:
	"""Frappe's own matching (frappe/website/path_resolver.resolve_redirect), on a path without its slash."""
	rule = _rule()
	pattern = rule["source"].strip("/ ") + "$"
	if not re.match(pattern, path):
		return None
	return re.sub(pattern, rule["target"], path)


class TestTheRedirectRule(unittest.TestCase):
	def test_every_hrms_address_lands_on_the_mapping_page(self):
		self.assertEqual(_redirect("hrms"), "/my-hr-go?to=")
		self.assertEqual(_redirect("hrms/leave-applications/HR-LAP-2026-00042"), "/my-hr-go?to=/leave-applications/HR-LAP-2026-00042")

	def test_nothing_else_is_caught(self):
		for path in ("hrmsx", "assets/hrms/frontend/index.js", "app/hrms", "desk/self-service"):
			with self.subTest(path=path):
				self.assertIsNone(_redirect(path))

	def test_temporary_so_browsers_do_not_keep_it(self):
		self.assertEqual(_rule()["redirect_http_status"], 302)


class TestTheMapping(unittest.TestCase):
	def test_records_open_in_my_desk(self):
		self.assertEqual(target("/leave-applications/HR-LAP-2026-00042", True), "/my-desk/r/Leave%20Application/HR-LAP-2026-00042")
		self.assertEqual(target("/expense-claims/HR-EXP-2026-00007", True), "/my-desk/r/Expense%20Claim/HR-EXP-2026-00007")
		self.assertEqual(
			target("/salary-slips/Sal Slip/HR-EMP-00012/00003", True), "/my-desk/r/Salary%20Slip/Sal%20Slip%2FHR-EMP-00012%2F00003"
		)

	def test_lists_new_forms_and_screens(self):
		self.assertEqual(target("/leave-applications", True), "/my-desk/l/Leave%20Application")
		self.assertEqual(target("/leave-applications/new", True), "/my-desk/apps/my-hr/leave/new")
		self.assertEqual(target("/shift-assignments/new", True), "/my-desk/l/Shift%20Assignment")
		self.assertEqual(target("/compensatory-leave-requests/new", True), "/my-desk/l/Compensatory%20Leave%20Request")
		self.assertEqual(target("/employee-checkins", True), "/my-desk/apps/my-hr/check-in")
		self.assertEqual(target("/notifications", True), "/my-desk/notifications")
		self.assertEqual(target("", True), "/my-desk/apps/my-hr")
		self.assertEqual(target("/something-new", True), "/my-desk/apps/my-hr")

	def test_without_my_desk_the_desk(self):
		self.assertEqual(target("/leave-applications/HR-LAP-2026-00042", False), "/desk/leave-application/HR-LAP-2026-00042")
		self.assertEqual(target("/leave-applications", False), SELF_SERVICE)
		self.assertEqual(target("/home", False), SELF_SERVICE)

	def test_a_name_is_escaped_not_followed(self):
		self.assertEqual(target("/expense-claims/../../desk", True), "/my-desk/r/Expense%20Claim/..%2F..%2Fdesk")
		self.assertTrue(target("//evil.example.com", True).startswith("/my-desk"))


class TestAgainstFrappeHR(unittest.TestCase):
	"""Every link Frappe HR builds and every route of its app has an answer here."""

	HRMS = pathlib.Path(frappe.get_app_path("hrms")).parent

	def test_the_push_links(self):
		source = (self.HRMS / "hrms" / "hr" / "doctype" / "pwa_notification" / "pwa_notification.py").read_text()
		heads = set(re.findall(r'f"\{base_url\}/([a-z-]+)/', source))
		self.assertTrue(heads, "Frappe HR builds no record links any more: re-read pwa_notification.py")
		self.assertLessEqual(heads, set(COLLECTIONS), heads - set(COLLECTIONS))

	def test_the_app_routes(self):
		routes = set()
		for path in (self.HRMS / "frontend" / "src" / "router").glob("*.js"):
			routes |= set(re.findall(r'path:\s*"/([^"]*)"', path.read_text()))
		self.assertTrue(routes, "no routes found in Frappe HR's router")
		unmapped = sorted(
			r
			for r in routes
			if r.split("/")[0] not in COLLECTIONS and r not in SCREENS and r.split("/:")[0] not in SCREENS
		)
		self.assertEqual(unmapped, [], "Frappe HR routes with no My Desk screen")
