# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""The Frappe Workflow that moves time off claims, and what code still keeps (toil/workflow.py).

Decision 2026-11-10 (WORKING_TIME_DESIGN.md §9i): the workflow owns states,
actions and roles; the controller owns who exactly, the reason, the lock while
waiting, and the side effects. These tests pin both halves.
"""

from unittest.mock import patch

import frappe
from frappe.model.workflow import get_transitions

from seal_hrms.seal_hrms.timesheets import approval as timesheet_approval
from seal_hrms.seal_hrms.toil import approval
from seal_hrms.seal_hrms.toil import workflow as wf
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_toil_claim import ToilTestCase


def _forget_workflow():
	frappe.cache.hdel("workflow", tf.CLAIM)
	frappe.clear_document_cache("Workflow", wf.WORKFLOW)


class TestTheWorkflowItself(ToilTestCase):
	def tearDown(self):
		super().tearDown()
		_forget_workflow()

	def test_it_is_there_and_complete(self):
		self.assertEqual(wf.problems(), [])

	def test_ensuring_it_twice_changes_nothing(self):
		before = frappe.db.count("Workflow Transition", {"parent": wf.WORKFLOW})
		wf.ensure_workflow()
		self.assertEqual(frappe.db.count("Workflow", {"document_type": tf.CLAIM}), 1)
		self.assertEqual(frappe.db.count("Workflow Transition", {"parent": wf.WORKFLOW}), before)

	def test_a_site_change_is_kept(self):
		frappe.db.set_value(
			"Workflow Transition", {"parent": wf.WORKFLOW, "action": wf.APPROVE}, "allowed", "HR Manager"
		)
		wf.ensure_workflow()
		self.assertEqual(
			set(
				frappe.get_all(
					"Workflow Transition", {"parent": wf.WORKFLOW, "action": wf.APPROVE}, pluck="allowed"
				)
			),
			{"HR Manager"},
		)

	def test_a_switched_off_workflow_is_reported(self):
		frappe.db.set_value("Workflow", wf.WORKFLOW, "is_active", 0)
		_forget_workflow()
		self.assertEqual(len(wf.problems()), 1)

	def test_a_missing_step_is_reported(self):
		frappe.db.delete("Workflow Document State", {"parent": wf.WORKFLOW, "state": wf.RETURNED})
		_forget_workflow()
		self.assertTrue(any(wf.RETURNED in p for p in wf.problems()))


class TestTheActionsOffered(ToilTestCase):
	def _actions(self, doc, user):
		frappe.set_user(user)
		try:
			return {t.action for t in get_transitions(frappe.get_doc(tf.CLAIM, doc.name))}
		finally:
			frappe.set_user("Administrator")

	def test_a_draft_is_sent_by_its_owner(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 3)], as_user=self.otieno_user)
		self.assertEqual(self._actions(doc, self.otieno_user), {wf.SEND})

	def test_the_approver_decides(self):
		doc = self._sent([(tf.rest_day(), 3)])
		self.assertEqual(self._actions(doc, self.achieng_user), {wf.APPROVE, wf.RETURN, wf.REJECT})

	def test_a_colleague_with_the_role_is_still_refused(self):
		# The workflow lets any Leave Approver see the actions; the controller names the one person.
		doc = self._sent([(tf.rest_day(), 3)])
		frappe.get_doc("User", self.njeri_user).add_roles("Leave Approver")
		try:
			frappe.share.add_docshare(
				tf.CLAIM,
				doc.name,
				self.njeri_user,
				read=1,
				write=1,
				submit=1,
				flags={"ignore_share_permission": True},
			)
			with self.assertRaises(frappe.PermissionError):
				fx.as_user(self.njeri_user, approval.approve, doc.name)
		finally:
			frappe.clear_cache(user=self.njeri_user)
		self.assertEqual(frappe.db.get_value(tf.CLAIM, doc.name, "docstatus"), 0)


class TestWhatCodeStillKeeps(ToilTestCase):
	def test_the_status_cannot_be_typed_in(self):
		doc = tf.claim(self.otieno, [(tf.rest_day(), 3)], as_user=self.otieno_user)
		# Typing "Waiting for Approval" is the same as sending it, and checked the same;
		# a move it does not offer is refused (by us or by Frappe, whichever checks first).
		doc.status = wf.APPROVED
		with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
			fx.as_user(self.otieno_user, doc.save)
		self.assertEqual(frappe.db.get_value(tf.CLAIM, doc.name, "status"), wf.DRAFT)

	def test_a_waiting_claim_is_locked_even_for_the_approver(self):
		doc = self._sent([(tf.rest_day(), 3)])
		doc = frappe.get_doc(tf.CLAIM, doc.name)
		doc.lines[0].hours = 2
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.achieng_user, doc.save)

	def test_the_reason_is_saved_before_return(self):
		doc = self._sent([(tf.rest_day(), 3)])
		fx.as_user(self.achieng_user, approval.return_claim, doc.name, "Only two hours were on the rota")
		doc.reload()
		self.assertEqual((doc.status, doc.decision_note), (wf.RETURNED, "Only two hours were on the rota"))
		self.assertEqual(doc.approved_by, self.achieng_user)

	def test_only_a_decider_writes_the_reason(self):
		doc = self._sent([(tf.rest_day(), 3)])
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, wf.set_decision_note, doc.name, "Approve it please")

	def test_sending_again_clears_the_old_reason(self):
		doc = self._sent([(tf.rest_day(), 3)])
		fx.as_user(self.achieng_user, approval.return_claim, doc.name, "Say what the work was")
		fx.as_user(self.otieno_user, approval.send_for_approval, doc.name)
		doc.reload()
		self.assertEqual((doc.status, doc.decision_note), (wf.WAITING, None))

	def test_cancel_through_the_workflow_takes_the_time_back(self):
		doc = self._approved([(tf.rest_day(), 8)])
		self.assertTrue(doc.days_credited)
		wf.act(doc.name, wf.CANCEL)
		doc.reload()
		self.assertEqual((doc.docstatus, doc.status), (2, wf.CANCELLED))
		rows = frappe.get_all(
			"Leave Ledger Entry", filters={"custom_toil_claim": doc.name, "docstatus": 1}, pluck="leaves"
		)
		self.assertEqual(sorted(rows), [-1, 1])


class TestTimesheetsStandDownForASiteWorkflow(ToilTestCase):
	def test_a_site_workflow_switches_ours_off(self):
		tf.policy(timesheet_approval=1)
		doc = frappe._dict(employee=self.otieno, company=tf.COMPANY)
		self.assertTrue(timesheet_approval.applies(doc))
		with patch("frappe.model.workflow.get_workflow_name", return_value="Timesheet Sign-off"):
			self.assertFalse(timesheet_approval.applies(doc))
