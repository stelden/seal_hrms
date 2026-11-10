# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""HR approvals on My Desk (seal_hrms/my_desk/approvals.py, HR_ON_MY_DESK.md §2.1).

Otieno works at the Kilimani office; Achieng approves his leave, time off and
timesheets, and his expense claims; Njeri is a colleague who approves nothing, until
she stands in for Achieng. Each kind of approval: only the viewer's items, stand-in
items carry whom they are for, nobody sees their own, and every `act_on_*` refuses
what it should even when called directly. The shape tests need seal_desk; the rest
run on any site.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.utils import getdate, today

from seal_hrms.my_desk import approvals
from seal_hrms.seal_hrms import acting
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests.test_timesheet_approval import TimesheetTestCase
from seal_hrms.tests.test_toil_claim import ToilTestCase
from seal_hrms.tests import _toil_fixtures as tf

HOOK = "seal_desk_approval_sources"
PATCH_POLICY = "seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy.policy_for"


def _names(items):
	return [i.name for i in items]


class ApprovalsTestCase(ToilTestCase):
	def setUp(self):
		super().setUp()
		# These are about deciding, not about whether leave needs a handover first.
		off = patch(PATCH_POLICY, return_value=frappe._dict(name="HR Settings", requirement="Off", min_days=0, leave_types=[], prep_reminder_days=7))
		off.start()
		self.addCleanup(off.stop)

	def njeri_stands_in_for_achieng(self, authority: str, *documents):
		"""What a handover in effect gives Njeri: the approver role, shares, and acting rows."""
		frappe.get_doc("User", self.njeri_user).add_roles("Leave Approver", "Expense Approver")
		self.addCleanup(frappe.clear_cache, user=self.njeri_user)
		for doctype, name in documents:
			frappe.share.add_docshare(doctype, name, self.njeri_user, read=1, write=1, submit=1, flags={"ignore_share_permission": True})
		row = frappe._dict(principal=self.achieng_user, stand_in=self.njeri_user, authority=authority, assignment="TA-TEST", row="r1")
		for target, value in (
			("acting_for", lambda user: [row] if user == self.njeri_user else []),
			("acting_stand_in", lambda principal, kind: self.njeri_user if principal == self.achieng_user else None),
		):
			p = patch.object(acting, target, side_effect=value)
			p.start()
			self.addCleanup(p.stop)

	def _leave(self, days_ahead=20):
		return fx.leave(self.otieno, days_ahead, 2)


class TestLeave(ApprovalsTestCase):
	def test_the_approver_sees_it_and_a_colleague_does_not(self):
		la = self._leave()
		self.assertIn(la.name, _names(approvals.leave_items(self.achieng_user)))
		self.assertNotIn(la.name, _names(approvals.leave_items(self.njeri_user)))
		item = next(i for i in approvals.leave_items(self.achieng_user) if i.name == la.name)
		self.assertIsNone(item.on_behalf_of)
		self.assertEqual([a.key for a in item.actions], ["Approve", "Reject"])
		self.assertTrue(next(a for a in item.actions if a.key == "Reject").needs_reason)

	def test_nobody_sees_their_own(self):
		la = self._leave()
		la.db_set("leave_approver", self.otieno_user)
		self.assertNotIn(la.name, _names(approvals.leave_items(self.otieno_user)))

	def test_a_stand_in_sees_it_for_the_approver(self):
		la = self._leave()
		self.njeri_stands_in_for_achieng("leave_approval", ("Leave Application", la.name))
		item = next(i for i in approvals.leave_items(self.njeri_user) if i.name == la.name)
		self.assertEqual(item.on_behalf_of, self.achieng_user)

	def test_the_approver_approves(self):
		la = self._leave()
		answer = fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Approve")
		self.assertTrue(answer["ok"])
		la.reload()
		self.assertEqual((la.docstatus, la.status), (1, "Approved"))

	def test_a_colleague_cannot_act(self):
		la = self._leave()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, approvals.act_on_leave, la.name, "Approve")

	def test_someone_who_can_open_it_but_is_not_the_approver_cannot_act(self):
		la = self._leave()
		frappe.get_doc("User", self.njeri_user).add_roles("Leave Approver")
		self.addCleanup(frappe.clear_cache, user=self.njeri_user)
		frappe.share.add_docshare("Leave Application", la.name, self.njeri_user, read=1, write=1, submit=1, flags={"ignore_share_permission": True})
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, approvals.act_on_leave, la.name, "Approve")

	def test_the_applicant_cannot_act_even_as_approver(self):
		la = self._leave()
		la.db_set("leave_approver", self.otieno_user)
		frappe.get_doc("User", self.otieno_user).add_roles("Leave Approver")
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, approvals.act_on_leave, la.name, "Approve")

	def test_rejecting_needs_a_reason_and_keeps_it(self):
		la = self._leave()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Reject", " ")
		fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Reject", "Stock count that week in Westlands")
		la.reload()
		self.assertEqual((la.docstatus, la.status), (1, "Rejected"))
		self.assertTrue(frappe.db.exists("Comment", {"reference_name": la.name, "content": ["like", "%Stock count%"]}))

	def test_a_decided_application_is_no_longer_waiting(self):
		la = self._leave()
		fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Approve")
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Approve")
		self.assertIn("no longer waiting", str(caught.exception))

	def test_an_unknown_action_is_refused(self):
		la = self._leave()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Cancel")

	def test_the_stand_in_approves_in_the_approvers_place(self):
		la = self._leave()
		self.njeri_stands_in_for_achieng("leave_approval", ("Leave Application", la.name))
		fx.as_user(self.njeri_user, approvals.act_on_leave, la.name, "Approve")
		la.reload()
		self.assertEqual(la.status, "Approved")

	def test_a_site_workflow_takes_over(self):
		la = self._leave()
		with patch.object(approvals, "_has_workflow", return_value=True):
			self.assertEqual(approvals.leave_items(self.achieng_user), [])
			with self.assertRaises(frappe.ValidationError):
				fx.as_user(self.achieng_user, approvals.act_on_leave, la.name, "Approve")


class TestExpenseClaims(ApprovalsTestCase):
	def _claim_type(self):
		"""Field travel, booked to one of the company's expense accounts."""
		name = "Kilimani Field Travel"
		if not frappe.db.exists("Expense Claim Type", name):
			account = frappe.db.get_value("Account", {"company": tf.COMPANY, "root_type": "Expense", "is_group": 0}, "name")
			doc = frappe.new_doc("Expense Claim Type")
			doc.expense_type = name
			doc.append("accounts", {"company": tf.COMPANY, "default_account": account})
			doc.insert(ignore_permissions=True)
		return name

	def _claim(self):
		frappe.db.set_value("Employee", self.otieno, "expense_approver", self.achieng_user, update_modified=False)
		frappe.get_doc("User", self.achieng_user).add_roles("Expense Approver")
		self.addCleanup(frappe.clear_cache, user=self.achieng_user)
		doc = frappe.new_doc("Expense Claim")
		doc.employee = self.otieno
		doc.company = tf.COMPANY
		doc.expense_approver = self.achieng_user
		doc.posting_date = today()
		doc.append("expenses", {"expense_date": today(), "expense_type": self._claim_type(), "amount": 3450, "sanctioned_amount": 3450, "description": "Matatu fares to Kibera outreach"})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		return doc

	def test_the_approver_sees_it_with_its_amount_and_a_fresh_check_on_approve(self):
		ec = self._claim()
		item = next(i for i in approvals.expense_items(self.achieng_user) if i.name == ec.name)
		self.assertEqual(item.amount, 3450)
		self.assertTrue(item.currency)
		self.assertTrue(next(a for a in item.actions if a.key == "Approve").verify)
		self.assertNotIn(ec.name, _names(approvals.expense_items(self.njeri_user)))

	def test_a_colleague_cannot_act(self):
		ec = self._claim()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, approvals.act_on_expense, ec.name, "Approve")

	def test_approving_asks_for_a_fresh_check_where_the_site_can(self):
		ec = self._claim()

		class Stale(frappe.PermissionError):
			pass

		recent = SimpleNamespace(is_recent=lambda minutes: False, VerificationNeeded=Stale)
		with patch("seal_hrms.seal_hrms.step_up._recent", return_value=recent):
			with self.assertRaises(Stale):
				fx.as_user(self.achieng_user, approvals.act_on_expense, ec.name, "Approve")

	def test_approving_submits_as_approved(self):
		from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim

		ec = self._claim()
		seen = []
		# The fresh check is the test above's; here she has just confirmed it is her. Without this the
		# test passed only where seal_common had no step-up (before 1.35.0), and failed beside it.
		with patch.object(ExpenseClaim, "submit", lambda self: seen.append(self.approval_status)), patch("seal_hrms.seal_hrms.step_up.require_fresh_check", return_value=True):
			fx.as_user(self.achieng_user, approvals.act_on_expense, ec.name, "Approve")
		self.assertEqual(seen, ["Approved"])  # the accounts this test site lacks are Frappe HR's to check

	def test_rejecting_needs_a_reason(self):
		ec = self._claim()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approvals.act_on_expense, ec.name, "Reject")


class TestTimeOffInLieu(ApprovalsTestCase):
	def test_the_approver_sees_the_workflow_steps_open_to_them(self):
		doc = self._sent([(tf.working_day(), 3)])
		item = next(i for i in approvals.toil_items(self.achieng_user) if i.name == doc.name)
		keys = [a.key for a in item.actions]
		self.assertIn("Approve", keys)
		self.assertIn("Return", keys)
		self.assertTrue(next(a for a in item.actions if a.key == "Return").needs_reason)
		self.assertNotIn(doc.name, _names(approvals.toil_items(self.njeri_user)))
		self.assertNotIn(doc.name, _names(approvals.toil_items(self.otieno_user)))

	def test_the_approver_approves(self):
		doc = self._sent([(tf.working_day(), 3)])
		fx.as_user(self.achieng_user, approvals.act_on_toil, doc.name, "Approve")
		doc.reload()
		self.assertEqual(doc.status, "Approved")

	def test_a_colleague_and_the_claimant_cannot_act(self):
		doc = self._sent([(tf.working_day(), 3)])
		for user in (self.njeri_user, self.otieno_user):
			with self.assertRaises(frappe.PermissionError):
				fx.as_user(user, approvals.act_on_toil, doc.name, "Approve")

	def test_returning_needs_a_reason(self):
		doc = self._sent([(tf.working_day(), 3)])
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approvals.act_on_toil, doc.name, "Return")
		fx.as_user(self.achieng_user, approvals.act_on_toil, doc.name, "Return", "Say which site visit this was")
		doc.reload()
		self.assertEqual(doc.status, "Returned")
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approvals.act_on_toil, doc.name, "Approve")


class TestTimesheets(TimesheetTestCase):
	def test_the_approver_sees_it_and_others_do_not(self):
		ts = self._sent()
		item = next(i for i in approvals.timesheet_items(self.achieng_user) if i.name == ts.name)
		self.assertEqual([a.key for a in item.actions], ["Approve", "Return"])
		self.assertNotIn(ts.name, _names(approvals.timesheet_items(self.njeri_user)))
		self.assertNotIn(ts.name, _names(approvals.timesheet_items(self.otieno_user)))

	def test_the_approver_approves_and_a_colleague_cannot(self):
		ts = self._sent()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, approvals.act_on_timesheet, ts.name, "Approve")
		fx.as_user(self.achieng_user, approvals.act_on_timesheet, ts.name, "Approve")
		ts.reload()
		self.assertEqual((ts.docstatus, ts.custom_approval_state), (1, "Approved"))

	def test_returning_needs_a_reason(self):
		ts = self._sent()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, approvals.act_on_timesheet, ts.name, "Return", "")
		fx.as_user(self.achieng_user, approvals.act_on_timesheet, ts.name, "Return", "Split the Mathare hours by project")
		ts.reload()
		self.assertEqual(ts.custom_approval_state, "Returned")

	def test_nothing_where_approval_is_off(self):
		ts = self._sent()
		tf.policy(timesheet_approval=0)
		with patch("seal_hrms.seal_hrms.timesheets.approval.site_workflow", return_value="Timesheet Approval"):
			self.assertNotIn(ts.name, _names(approvals.timesheet_items(self.achieng_user)))


class TestHookShape(unittest.TestCase):
	"""The declared sources are what seal_desk accepts (SECTIONS_CONTRACT.md §5)."""

	def test_each_source_is_well_formed(self):
		sources = frappe.get_hooks(HOOK, app_name="seal_hrms")
		self.assertEqual([s["key"] for s in sources], ["seal_hrms.leave", "seal_hrms.expense", "seal_hrms.toil", "seal_hrms.timesheets"])
		for source in sources:
			self.assertTrue(source["key"].startswith("seal_hrms."))
			self.assertTrue(source["doctypes"] and all(frappe.db.exists("DocType", d) for d in source["doctypes"]))
			frappe.get_attr(source["provider"])
			self.assertIn(frappe.get_attr(source["act"]), frappe.whitelisted)
			self.assertTrue(source["provider"].startswith("seal_hrms.desk.providers."), "one adapter module (§3.15)")

	def test_acts_take_name_action_reason(self):
		import inspect

		for source in frappe.get_hooks(HOOK, app_name="seal_hrms"):
			params = list(inspect.signature(frappe.get_attr(source["act"])).parameters)
			self.assertEqual(params, ["name", "action", "reason"])


@unittest.skipUnless("seal_desk" in frappe.get_installed_apps(), "seal_desk is not installed")
class TestTheDeskAcceptsThem(ApprovalsTestCase):
	def test_registry_accepts_every_source(self):
		from seal_desk.role_center import registry

		if not hasattr(registry, "approval_sources"):
			self.skipTest("this seal_desk has no approval sources")
		accepted, refused = registry.approval_sources()
		self.assertEqual([r for r in refused if r.app == "seal_hrms"], [])
		self.assertTrue({"seal_hrms.leave", "seal_hrms.toil"} <= {s.key for s in accepted})

	def test_providers_return_the_desks_types(self):
		try:
			from seal_desk.role_center import contract, registry
			from seal_desk.role_center.schema import ApprovalItem, DeskContext
		except ImportError:
			self.skipTest("this seal_desk has no approval sources")
		self._sent([(tf.working_day(), 3)])
		ctx = DeskContext(self.achieng_user, None, getdate(today()), frozenset())
		source = next(s for s in registry.approval_sources()[0] if s.key == "seal_hrms.toil")
		items, error = contract.run_approval_source(source, ctx)
		self.assertIsNone(error)
		self.assertTrue(items and all(isinstance(i, ApprovalItem) for i in items))
		self.assertEqual([i.problem() for i in items], [None] * len(items))
