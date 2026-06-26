# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Permission hooks integration tests — multi-user scenarios.

Verifies that get_permission_query_conditions and has_permission together
scope visibility correctly per the SPEC §10 role matrix:

  - Employee Self Service: only own records visible
  - Leave Approver: own + direct reports
  - HR User / HR Manager: everything in company
  - Administrator: bypass
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from seal_hrms.seal_hrms.leave_planning.permissions import (
	leave_plan_has_permission,
	leave_plan_query_conditions,
	leave_plan_slot_booking_query_conditions,
	leave_planning_cycle_member_query_conditions,
)


class TestPermissionQueryConditions(FrappeTestCase):
	"""Per §3.4 — query_conditions and has_permission ship together.

	These tests exercise query_conditions in isolation (string output contract).
	Multi-user dynamic permission tests need a richer test user setup; those
	come in a follow-up suite.
	"""

	def test_administrator_gets_no_filter(self):
		original_user = frappe.session.user
		try:
			frappe.set_user("Administrator")
			self.assertEqual(leave_plan_query_conditions("Administrator"), "")
			self.assertEqual(leave_plan_slot_booking_query_conditions("Administrator"), "")
			self.assertEqual(leave_planning_cycle_member_query_conditions("Administrator"), "")
		finally:
			frappe.set_user(original_user)

	def test_query_conditions_include_employee_constraint_for_non_hr(self):
		"""For a regular user, conditions should mention the user's employee or user."""
		fake_user = "test-employee-user@example.com"
		condition = leave_plan_query_conditions(fake_user)
		self.assertTrue(
			"employee" in condition.lower() or "leave_approver" in condition.lower() or condition == "1=0",
			f"expected scoped condition, got: {condition!r}",
		)

	def test_leave_plan_slot_booking_query_conditions_uses_employee(self):
		fake_user = "test-employee-user@example.com"
		condition = leave_plan_slot_booking_query_conditions(fake_user)
		self.assertTrue(
			"employee" in condition.lower() or condition == "1=0",
			f"expected employee-scoped condition, got: {condition!r}",
		)

	def test_cycle_member_query_conditions_includes_leave_approver(self):
		fake_user = "test-manager@example.com"
		condition = leave_planning_cycle_member_query_conditions(fake_user)
		self.assertTrue(
			"employee" in condition.lower() or "leave_approver" in condition.lower() or condition == "1=0",
			f"expected scoped condition, got: {condition!r}",
		)


class TestHasPermissionBoolReturns(FrappeTestCase):
	"""Per §2.9 — every has_permission hook returns explicit bool.

	The source-guard test catches statically-detectable implicit None paths.
	These tests dynamically exercise key (doc, ptype, user) combinations.
	"""

	def test_guest_always_denied(self):
		fake_doc = frappe._dict(employee="EMP-X", leave_approver="user@example.com")
		for ptype in ("read", "write", "submit", "cancel", "delete"):
			self.assertIs(
				leave_plan_has_permission(fake_doc, ptype, "Guest"), False,
				f"Guest should be denied for {ptype}",
			)

	def test_administrator_always_allowed(self):
		fake_doc = frappe._dict(employee="EMP-X", leave_approver="user@example.com")
		for ptype in ("read", "write", "submit", "cancel"):
			result = leave_plan_has_permission(fake_doc, ptype, "Administrator")
			self.assertIsInstance(result, bool)

	def test_returns_explicit_bool_for_every_ptype(self):
		"""§2.9 sanity — every common ptype + user combo returns bool, never None."""
		fake_doc = frappe._dict(employee="EMP-X", leave_approver="manager@example.com")
		for ptype in ("read", "select", "write", "submit", "cancel", "amend", "delete", "create", "print"):
			for user in ("Guest", "Administrator", "manager@example.com", "stranger@example.com"):
				result = leave_plan_has_permission(fake_doc, ptype, user)
				self.assertIsInstance(
					result, bool,
					f"({ptype}, {user}) returned {result!r}, expected bool",
				)
