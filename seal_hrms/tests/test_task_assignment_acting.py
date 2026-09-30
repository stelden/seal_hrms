# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Approving in an absent approver's place (seal_hrms.acting).

Achieng approves leave for the office. She goes on leave and Otieno approves in
her place. Each thing that must hold is pinned: he agrees to it separately from
covering her work; he can approve while she is away and not after; what he is
given is taken back, and nothing he already had; and he cannot approve his own
leave by being his own approver's stand-in.
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from seal_hrms.seal_hrms import acting, handover, task_assignment_actions as actions
from seal_hrms.seal_hrms.handover import Status
from seal_hrms.tests import _handover_fixtures as fx

_real_get_attr = frappe.get_attr


class ActingTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		cls.achieng_user = fx.approver()
		cls.achieng = fx.ensure_employee("achieng")
		cls.otieno = fx.ensure_employee("otieno")
		cls.njeri = fx.ensure_employee("njeri")
		cls.otieno_user, cls.njeri_user = fx.email("otieno"), fx.email("njeri")
		# Achieng approves Njeri's leave.
		njeri = frappe.get_doc("Employee", cls.njeri)
		if njeri.leave_approver != cls.achieng_user:
			njeri.leave_approver = cls.achieng_user
			njeri.save(ignore_permissions=True)

	def setUp(self):
		frappe.set_user("Administrator")
		self._clean()
		self._strip(self.otieno_user, "Leave Approver")

	def tearDown(self):
		frappe.set_user("Administrator")
		self._clean()

	def _clean(self):
		fx.cleanup([self.achieng, self.otieno, self.njeri])

	def _strip(self, user, role):
		frappe.db.delete("Has Role", {"parent": user, "parenttype": "User", "role": role})
		frappe.clear_cache(user=user)

	def _handover(self, start_offset=0, days=4):
		"""Achieng's leave, with Otieno covering her work and her leave approvals."""
		la = fx.leave(self.achieng, start_offset, days)
		frappe.db.set_value("Leave Application", la.name, "leave_approver", "Administrator", update_modified=False)
		la.reload()
		ta = frappe.new_doc("Task Assignment")
		ta.employee = self.achieng
		ta.leave_application = la.name
		ta.task_assignee = self.otieno
		ta.task_description = "<p>Approve the team's leave and keep the rota straight.</p>"
		ta.append("authorities", {"authority": "leave_approval"})
		ta.insert(ignore_permissions=True)
		ta.submit()
		return la, ta

	def _in_effect(self):
		la, ta = self._handover()
		fx.approve(la)
		fx.agree(ta, "otieno")
		fx.as_user(self.otieno_user, actions.respond_authority, ta.name, ta.authorities[0].name, "Accepted")
		ta.reload()
		self.assertEqual(ta.status, Status.ACTIVE)
		return la, ta


class TestAgreeingToApprove(ActingTestCase):
	def test_achieng_is_found_to_approve_leave(self):
		kinds = [a["authority"] for a in acting.suggest_authorities(self.achieng)]
		self.assertIn("leave_approval", kinds)

	def test_covering_the_work_is_not_agreeing_to_approve(self):
		la, ta = self._handover(start_offset=3)
		fx.agree(ta, "otieno")
		self.assertEqual(ta.status, Status.AWAITING, "approving in her place is answered on its own row")
		self.assertEqual(ta.authorities[0].acceptance, "Pending")
		fx.as_user(self.otieno_user, actions.respond_authority, ta.name, ta.authorities[0].name, "Accepted")
		ta.reload()
		self.assertEqual(ta.status, Status.ACCEPTED)

	def test_declining_to_approve_needs_a_reason(self):
		_la, ta = self._handover(start_offset=3)
		row = ta.authorities[0].name
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, actions.respond_authority, ta.name, row, "Declined", " ")
		fx.as_user(self.otieno_user, actions.respond_authority, ta.name, row, "Declined", "I report to Achieng myself")
		ta.reload()
		self.assertEqual(ta.status, Status.DECLINED)

	def test_only_the_named_person_answers_for_an_approval(self):
		_la, ta = self._handover(start_offset=3)
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, actions.respond_authority, ta.name, ta.authorities[0].name, "Accepted")

	def test_an_unknown_kind_is_refused(self):
		la = fx.leave(self.achieng, 3, 2)
		ta = frappe.new_doc("Task Assignment")
		ta.employee, ta.leave_application, ta.task_assignee = self.achieng, la.name, self.otieno
		ta.task_description = "Cover"
		ta.append("authorities", {"authority": "signing_cheques"})
		with self.assertRaises(frappe.ValidationError):
			ta.insert(ignore_permissions=True)


class TestApprovingWhileAway(ActingTestCase):
	def test_stand_in_can_approve_while_away_and_it_is_recorded(self):
		pending = fx.leave(self.njeri, 2, 2)  # waiting on Achieng before she went
		_la, ta = self._in_effect()
		self.assertIn("Leave Approver", frappe.get_roles(self.otieno_user))
		self.assertTrue(frappe.has_permission("Leave Application", "submit", doc=pending.name, user=self.otieno_user))

		def approve():
			doc = frappe.get_doc("Leave Application", pending.name)
			doc.status = "Approved"
			doc.submit()

		fx.as_user(self.otieno_user, approve)
		comments = frappe.get_all("Comment", filters={"reference_doctype": "Leave Application",
		                                              "reference_name": pending.name}, pluck="content")
		self.assertTrue(any("acting for" in (c or "") and ta.name in c for c in comments), comments)

	def test_leave_raised_while_away_reaches_the_stand_in(self):
		_la, ta = self._in_effect()
		new = fx.leave(self.njeri, 5, 2)
		self.assertTrue(frappe.db.exists("DocShare", {"share_doctype": "Leave Application", "share_name": new.name,
		                                              "user": self.otieno_user}))
		shares = json.loads(frappe.db.get_value("Task Assignment Authority", ta.authorities[0].name, "shares"))
		self.assertTrue(shares, "the share is recorded so it can be taken back")

	def test_stand_in_cannot_approve_their_own_leave(self):
		_la, ta = self._in_effect()
		# Otieno's own approver is Achieng, the person he is approving for.
		mine = fx.leave(self.otieno, 10, 2)

		def approve_own():
			doc = frappe.get_doc("Leave Application", mine.name)
			doc.status = "Approved"
			doc.save()

		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, approve_own)

	def test_no_chaining(self):
		_la, ta = self._in_effect()
		self.assertEqual(acting.acting_stand_in(self.achieng_user, "leave_approval"), self.otieno_user)
		self.assertIsNone(acting.acting_stand_in(self.otieno_user, "leave_approval"),
		                  "Otieno being a stand-in does not make anyone his")


class TestOnReturn(ActingTestCase):
	def test_what_was_given_is_taken_back(self):
		pending = fx.leave(self.njeri, 2, 2)
		_la, ta = self._in_effect()
		handover.hand_back(ta.name)
		self.assertNotIn("Leave Approver", frappe.get_roles(self.otieno_user))
		self.assertFalse(frappe.db.exists("DocShare", {"share_doctype": "Leave Application",
		                                               "share_name": pending.name, "user": self.otieno_user}))
		self.assertIsNone(acting.acting_stand_in(self.achieng_user, "leave_approval"))

	def test_a_role_already_held_is_left_alone(self):
		fx.ensure_user("otieno", roles=("Employee", "Leave Approver"))
		_la, ta = self._in_effect()
		self.assertFalse(frappe.db.get_value("Task Assignment Authority", ta.authorities[0].name, "role_added_by_assignment"))
		handover.hand_back(ta.name)
		self.assertIn("Leave Approver", frappe.get_roles(self.otieno_user), "he was an approver before; he still is")


class TestHeadOfDepartment(ActingTestCase):
	"""Achieng heads Kilimani Operations: her department's leave and expense approvals go as one line."""

	DEPARTMENT = "Kilimani Operations"

	def setUp(self):
		super().setUp()
		self._strip(self.otieno_user, "Expense Approver")
		self.department = self._department()

	def tearDown(self):
		super().tearDown()
		if frappe.db.exists("Department", self.department):
			frappe.delete_doc("Department", self.department, force=1, ignore_permissions=True)

	def _department(self):
		abbr = frappe.db.get_value("Company", fx.COMPANY, "abbr")
		name = f"{self.DEPARTMENT} - {abbr}"
		if frappe.db.exists("Department", name):
			frappe.delete_doc("Department", name, force=1, ignore_permissions=True)
		doc = frappe.new_doc("Department")
		doc.department_name = self.DEPARTMENT
		doc.company = fx.COMPANY
		doc.append("leave_approvers", {"approver": self.achieng_user})
		doc.append("expense_approvers", {"approver": self.achieng_user})
		doc.insert(ignore_permissions=True)
		return doc.name

	def _hod_handover(self):
		la = fx.leave(self.achieng, 0, 4)
		frappe.db.set_value("Leave Application", la.name, "leave_approver", "Administrator", update_modified=False)
		ta = frappe.new_doc("Task Assignment")
		ta.employee, ta.leave_application, ta.task_assignee = self.achieng, la.name, self.otieno
		ta.task_description = "<p>Approve Kilimani Operations' leave and claims.</p>"
		ta.append("authorities", {"authority": "head_of_department"})
		ta.insert(ignore_permissions=True)
		ta.submit()
		fx.approve(la)
		fx.agree(ta, "otieno")
		fx.as_user(self.otieno_user, actions.respond_authority, ta.name, ta.authorities[0].name, "Accepted")
		ta.reload()
		self.assertEqual(ta.status, Status.ACTIVE)
		return ta

	def test_a_department_head_is_offered_one_line_not_three(self):
		kinds = [a["authority"] for a in acting.suggest_authorities(self.achieng)]
		self.assertIn("head_of_department", kinds)
		self.assertNotIn("leave_approval", kinds, "covered by the department line")
		self.assertNotIn("expense_approval", kinds, "covered by the department line")

	def test_the_stand_in_approves_both_kinds_and_loses_both_on_return(self):
		ta = self._hod_handover()
		roles = frappe.get_roles(self.otieno_user)
		self.assertIn("Leave Approver", roles)
		self.assertIn("Expense Approver", roles)
		self.assertEqual(acting.acting_stand_in(self.achieng_user, "leave_approval"), self.otieno_user)
		self.assertEqual(acting.acting_stand_in(self.achieng_user, "expense_approval"), self.otieno_user)
		handover.hand_back(ta.name)
		roles = frappe.get_roles(self.otieno_user)
		self.assertNotIn("Leave Approver", roles)
		self.assertNotIn("Expense Approver", roles)

	def test_leave_raised_for_the_head_reaches_the_stand_in(self):
		ta = self._hod_handover()
		new = fx.leave(self.njeri, 6, 2)  # Njeri's approver is Achieng
		self.assertTrue(frappe.db.exists("DocShare", {"share_doctype": "Leave Application", "share_name": new.name,
		                                              "user": self.otieno_user}))


@unittest.skipUnless("seal_common" in frappe.get_installed_apps(), "seal_common is not installed")
class TestOtherAppsCanAsk(ActingTestCase):
	"""seal_common.delegation is how seal_buying and seal_leave_planning learn who is acting."""

	def test_the_answer_follows_the_handover(self):
		from seal_common import delegation

		_la, ta = self._in_effect()
		delegation.forget()
		self.assertEqual(delegation.acting_stand_in(self.achieng_user, "leave_approval"), self.otieno_user)
		handover.hand_back(ta.name)
		self.assertIsNone(delegation.acting_stand_in(self.achieng_user, "leave_approval"))

	def test_others_are_told_when_acting_starts_and_ends(self):
		heard = []

		def listen(capacity, principal, stand_in, started):
			from seal_common import delegation

			# Asked at the moment of the announcement, as a re-stamping app would.
			heard.append((capacity, started, delegation.acting_stand_in(principal, capacity)))

		hooks = {"acting_change_subscribers": ["x.listen"], "acting_delegation_providers": ["seal_hrms.seal_hrms.acting.delegations"]}
		with patch("seal_common.delegation._hook_paths", side_effect=lambda name: hooks.get(name, [])), \
		     patch.object(frappe, "get_attr", side_effect=lambda path: listen if path == "x.listen" else _real_get_attr(path)):
			_la, ta = self._in_effect()
			handover.hand_back(ta.name)
		self.assertIn(("leave_approval", True, self.otieno_user), heard)
		self.assertIn(("leave_approval", False, None), heard, "by the end, nobody counts as acting any more")


class TestRegistry(IntegrationTestCase):
	def test_kinds_are_read_from_the_hooks_module(self):
		"""§2.17: a nested dict read through get_hooks comes back reshaped; the module is the source."""
		from seal_hrms import hooks

		kinds = acting.registry()
		self.assertEqual(kinds["leave_approval"].holds, hooks.task_assignment_authorities["leave_approval"]["holds"])
		self.assertEqual(kinds["leave_approval"].app, "seal_hrms")

	def test_another_app_can_declare_a_kind_and_can_switch_it_off(self):
		declared = SimpleNamespace(task_assignment_authorities={
			"signing_payments": {"label": "Signing payments", "holds": "x.y", "pending": "x.z"},
			"statutory_signing": {"label": "Statutory signing", "holds": "x.y", "enabled": False},
		})
		real = frappe.get_module

		def fake(name):
			return declared if name == "seal_fake_app.hooks" else real(name)

		with patch.object(frappe, "get_installed_apps", return_value=frappe.get_installed_apps() + ["seal_fake_app"]), \
		     patch.object(frappe, "get_module", side_effect=fake):
			kinds = acting.registry()
		self.assertIn("signing_payments", kinds)
		self.assertNotIn("statutory_signing", kinds)
