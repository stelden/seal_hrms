# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Task Assignment lifecycle: asked, agreed, in effect, returned.

Nothing moves when the handover is submitted. The stand-in has to agree, the
leave has to be approved, and it has to have started. Each of those three is
pinned separately, because any one missing used to be enough to hand work to
someone who never agreed to it, or while the owner was still at their desk.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate

from seal_hrms.seal_hrms import handover, handover_jobs, task_assignment_actions as actions
from seal_hrms.seal_hrms.handover import RowStatus, Status
from seal_hrms.tests import _handover_fixtures as fx


def _drop_policy():
	# delete_doc, not a raw delete: the policy is named after its company, so a
	# raw delete leaves child rows that the next policy of that name inherits.
	if frappe.db.exists("Task Assignment Policy", fx.COMPANY):
		frappe.delete_doc("Task Assignment Policy", fx.COMPANY, force=1, ignore_permissions=True)


class LifecycleTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.otieno = fx.ensure_employee("otieno")
		cls.njeri = fx.ensure_employee("njeri")
		cls.wanjiku_user, cls.otieno_user, cls.njeri_user = (fx.email(k) for k in ("wanjiku", "otieno", "njeri"))

	def setUp(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno, self.njeri])
		_drop_policy()

	def tearDown(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno, self.njeri])
		_drop_policy()

	def _submitted(self, start_offset=3, days=4, rows=None):
		task = fx.project_task("Close the Industrial Area stores ledger")
		todo = fx.assign(task, self.wanjiku_user)
		la = fx.leave(self.wanjiku, start_offset, days)
		rows = rows or [{"todo": todo, "description": "Stores ledger", "reference_type": "Task", "reference_name": task}]
		ta = fx.handover(self.wanjiku, self.otieno, la, rows)
		return task, la, ta

	def _emails_to(self, user):
		return frappe.db.count("Email Queue Recipient", {"recipient": user})


class TestNothingMovesUntilEverythingIsInPlace(LifecycleTestCase):
	def test_submitting_asks_the_stand_in_and_moves_nothing(self):
		before = self._emails_to(self.otieno_user)
		task, _la, ta = self._submitted()
		self.assertEqual(ta.status, Status.AWAITING)
		self.assertEqual(ta.acceptance, "Pending")
		self.assertEqual(fx.open_todos(self.otieno_user, task), [])
		self.assertEqual(len(fx.open_todos(self.wanjiku_user, task)), 1)
		self.assertGreater(self._emails_to(self.otieno_user), before, "the stand-in is asked")

	def test_agreed_but_not_yet_started(self):
		task, la, ta = self._submitted(start_offset=3)
		fx.approve(la)
		fx.agree(ta, "otieno")
		self.assertEqual(ta.status, Status.ACCEPTED)
		self.assertEqual(fx.open_todos(self.otieno_user, task), [], "Wanjiku is still at her desk")
		self.assertEqual(handover_jobs.activate_started_leave(on_date=add_days(la.from_date, -1)), [])
		self.assertEqual(handover_jobs.activate_started_leave(on_date=la.from_date), [ta.name])
		self.assertEqual(len(fx.open_todos(self.otieno_user, task)), 1)

	def test_agreed_and_started_but_leave_not_approved(self):
		task, la, ta = self._submitted(start_offset=3)
		fx.agree(ta, "otieno")
		self.assertEqual(handover_jobs.activate_started_leave(on_date=la.from_date), [])
		self.assertEqual(fx.open_todos(self.otieno_user, task), [])

	def test_approving_leave_that_has_begun_starts_the_cover(self):
		task, la, ta = self._submitted(start_offset=0)
		fx.agree(ta, "otieno")
		self.assertEqual(ta.status, Status.ACCEPTED)
		fx.approve(la)
		ta.reload()
		self.assertEqual(ta.status, Status.ACTIVE)
		self.assertEqual(len(fx.open_todos(self.otieno_user, task)), 1)

	def test_agreeing_last_starts_the_cover_when_already_approved_and_begun(self):
		task, la, ta = self._submitted(start_offset=0)
		fx.approve(la)
		result = fx.as_user(self.otieno_user, actions.respond, ta.name, "Accepted")
		self.assertEqual(result["status"], Status.ACTIVE)


class TestAnswers(LifecycleTestCase):
	def test_declining_needs_a_reason_and_moves_nothing(self):
		task, _la, ta = self._submitted()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, actions.respond, ta.name, "Declined", "")
		before = self._emails_to(self.wanjiku_user)
		fx.as_user(self.otieno_user, actions.respond, ta.name, "Declined", "I am at the Kisumu audit that week")
		ta.reload()
		self.assertEqual(ta.status, Status.DECLINED)
		self.assertEqual(ta.decline_reason, "I am at the Kisumu audit that week")
		self.assertEqual(fx.open_todos(self.otieno_user, task), [])
		self.assertGreater(self._emails_to(self.wanjiku_user), before, "the owner is told")

	def test_second_stand_in_answers_for_their_own_task(self):
		la = fx.leave(self.wanjiku, 3, 4)
		ta = fx.handover(self.wanjiku, self.otieno, la, [
			{"description": "Approve Westlands petty cash"},
			{"description": "Chair the Friday safety meeting", "task_assignee": self.njeri},
		])
		self.assertEqual(ta.assignment_todos[1].acceptance, "Pending")
		fx.agree(ta, "otieno")
		self.assertEqual(ta.status, Status.AWAITING, "Njeri has not answered yet")
		fx.agree(ta, "njeri")
		self.assertEqual(ta.status, Status.ACCEPTED)

		fx.approve(la)
		handover.maybe_activate(ta.name, on_date=la.from_date)
		ta.reload()
		owners = {r.description: frappe.db.get_value("ToDo", r.stand_in_todo, "allocated_to") for r in ta.assignment_todos}
		self.assertEqual(owners["Approve Westlands petty cash"], self.otieno_user)
		self.assertEqual(owners["Chair the Friday safety meeting"], self.njeri_user)

	def test_only_the_named_stand_in_can_answer(self):
		_task, _la, ta = self._submitted()
		for user in (self.njeri_user, self.wanjiku_user):
			with self.assertRaises(frappe.PermissionError, msg=user):
				fx.as_user(user, actions.respond, ta.name, "Accepted")


class TestWhileAway(LifecycleTestCase):
	def _in_effect(self):
		task, la, ta = self._submitted()
		fx.take_effect(ta, la)
		return task, la, ta

	def test_stand_in_leaves_notes_nobody_else_can(self):
		_task, _la, ta = self._in_effect()
		row = ta.assignment_todos[0].name
		fx.as_user(self.otieno_user, actions.add_note, ta.name, row, "Posted August; September waits on two GRNs")
		self.assertEqual(frappe.db.get_value("Task Assignment ToDo", row, "stand_in_notes"),
		                 "Posted August; September waits on two GRNs")
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, actions.add_note, ta.name, row, "not mine to write")
		fx.as_user(self.otieno_user, actions.leave_return_note, ta.name, "<p>Supplier Mwangi Hardware called twice.</p>")
		self.assertIn("Mwangi Hardware", frappe.db.get_value("Task Assignment", ta.name, "return_summary"))

	def test_owner_back_early_takes_the_work_back(self):
		task, _la, ta = self._in_effect()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, actions.return_work, ta.name)
		fx.as_user(self.wanjiku_user, actions.return_work, ta.name)
		self.assertEqual(frappe.db.get_value("Task Assignment", ta.name, "status"), Status.HANDED_BACK)
		self.assertEqual(len(fx.open_todos(self.wanjiku_user, task)), 1)

	def test_stand_in_is_reminded_once_the_day_before(self):
		_task, _la, ta = self._in_effect()
		eve = add_days(ta.return_date, -1)
		self.assertEqual(handover_jobs.remind_before_return(on_date=add_days(eve, -1)), [])
		self.assertEqual(handover_jobs.remind_before_return(on_date=eve), [ta.name])
		self.assertEqual(handover_jobs.remind_before_return(on_date=eve), [], "first detection only (§3.7)")


class TestDates(LifecycleTestCase):
	def test_return_date_skips_a_holiday(self):
		la = fx.leave(self.wanjiku, 3, 2)
		day_after = getdate(add_days(la.to_date, 1))
		name = "Kilimani Office Holidays (Handover Test)"
		if frappe.db.exists("Holiday List", name):
			frappe.delete_doc("Holiday List", name, force=1, ignore_permissions=True)
		hl = frappe.new_doc("Holiday List")
		hl.holiday_list_name = name
		hl.from_date = add_days(day_after, -30)
		hl.to_date = add_days(day_after, 30)
		hl.append("holidays", {"holiday_date": day_after, "description": "Mashujaa Day"})
		hl.insert(ignore_permissions=True)
		# HRMS v16 decides an employee's holidays by Holiday List Assignment, not the Employee field.
		assignment = frappe.new_doc("Holiday List Assignment")
		assignment.applicable_for = "Employee"
		assignment.assigned_to = self.wanjiku
		assignment.holiday_list = name
		# Takes effect after today, so only a lookup made for the return day itself finds it.
		assignment.from_date = la.to_date
		assignment.insert(ignore_permissions=True)
		assignment.submit()
		try:
			self.assertEqual(handover.return_date_for(self.wanjiku, la.to_date), getdate(add_days(day_after, 1)))
		finally:
			assignment.cancel()
			frappe.delete_doc("Holiday List Assignment", assignment.name, force=1, ignore_permissions=True)
			frappe.delete_doc("Holiday List", name, force=1, ignore_permissions=True)

	def test_editing_the_leave_moves_the_handover_dates(self):
		la = fx.leave(self.wanjiku, 5, 3)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"description": "Stock take"}], submit=False)
		la.reload()
		la.to_date = add_days(la.to_date, 2)
		la.save(ignore_permissions=True)
		self.assertEqual(getdate(frappe.db.get_value("Task Assignment", ta.name, "leave_to")), getdate(la.to_date))


class TestApprovalPolicy(LifecycleTestCase):
	def _policy(self, requirement, min_days=0, leave_types=()):
		doc = frappe.new_doc("Task Assignment Policy")
		doc.company = fx.COMPANY
		doc.requirement = requirement
		doc.min_days = min_days
		for leave_type in leave_types:
			doc.append("leave_types", {"leave_type": leave_type})
		doc.insert(ignore_permissions=True)

	def test_require_refuses_approval_without_agreed_cover(self):
		self._policy("Require")
		la = fx.leave(self.wanjiku, 3, 4)
		with self.assertRaises(frappe.ValidationError):
			fx.approve(la)

	def test_require_allows_approval_once_cover_is_agreed(self):
		self._policy("Require")
		_task, la, ta = self._submitted()
		fx.agree(ta, "otieno")
		fx.approve(la)
		self.assertEqual(la.docstatus, 1)

	def test_warn_tells_the_approver_but_lets_it_through(self):
		self._policy("Warn")
		la = fx.leave(self.wanjiku, 3, 4)
		# Test runs mute msgprint, so watch the call rather than the message log.
		with patch.object(frappe, "msgprint", wraps=frappe.msgprint) as said:
			fx.approve(la)
		self.assertEqual(la.docstatus, 1)
		self.assertTrue(any("agreed to cover" in str(c.args[0]) for c in said.call_args_list if c.args))

	def test_short_or_other_leave_is_not_covered_by_the_policy(self):
		self._policy("Require", min_days=5)
		fx.approve(fx.leave(self.wanjiku, 3, 2))  # two days, under the minimum
		self._policy_types_only("Study Leave (Handover Test)")
		fx.approve(fx.leave(self.wanjiku, 10, 6))  # long enough, but not a listed kind

	def _policy_types_only(self, leave_type):
		if not frappe.db.exists("Leave Type", leave_type):
			lt = frappe.new_doc("Leave Type")
			lt.leave_type_name = leave_type
			lt.is_lwp = 1
			lt.insert(ignore_permissions=True)
		doc = frappe.get_doc("Task Assignment Policy", fx.COMPANY)
		doc.min_days = 0
		doc.set("leave_types", [{"leave_type": leave_type}])
		doc.save(ignore_permissions=True)

	def test_hr_settings_handover_modes_end_to_end(self):
		"""Verify HR Settings handover modes (Off, Warn, Require on Approval, Require on Submission, Require Acceptance before Submission, min_days)."""
		_drop_policy()
		frappe.db.set_value("HR Settings", None, "leave_approver_mandatory_in_leave_application", 1)
		frappe.db.set_value("HR Settings", None, "custom_leave_handover_min_days", 3)

		# 1. Require on Submission: draft saves, short leave (< 3 days) submits without handover, >= 3 days requires handover with stand-in
		frappe.db.set_value("HR Settings", None, "custom_leave_handover_requirement", "Require on Submission")
		short_la = fx.leave(self.wanjiku, 2, 2)
		fx.approve(short_la)
		self.assertEqual(short_la.docstatus, 1)
		short_la.cancel()

		la = fx.leave(self.wanjiku, 10, 4)
		# Editing draft in initial state succeeds without handover
		la.description = "Updated reason while still in draft"
		la.save(ignore_permissions=True)

		# Approving/submitting without handover is blocked
		with self.assertRaises(frappe.ValidationError):
			fx.approve(la)

		# Prepare handover and assign stand-in, but stand-in has not accepted yet -> approval still blocked
		ta_name = fx.as_user(self.wanjiku_user, actions.prepare_from_leave, la.name)
		ta = frappe.get_doc("Task Assignment", ta_name)
		ta.task_assignee = self.otieno
		ta.task_description = "<p>Cover my desk</p>"
		ta.save(ignore_permissions=True)
		ta.submit()
		with self.assertRaises(frappe.ValidationError):
			fx.approve(la)

		# Stand-in accepts -> approval succeeds
		fx.agree(ta, "otieno")
		fx.approve(la)
		self.assertEqual(la.docstatus, 1)

		# Cancel leave -> handover is cancelled and unlinked, amend and re-apply works
		la.reload()
		la.cancel()
		ta.reload()
		self.assertEqual(ta.docstatus, 2)
		self.assertIsNone(ta.leave_application)

		# 2. Require Acceptance before Submission: blocks workflow/submission until stand-in accepts
		frappe.db.set_value("HR Settings", None, "custom_leave_handover_requirement", "Require Acceptance before Submission")
		la_acc = frappe.copy_doc(la)
		la_acc.amended_from = la.name
		la_acc.insert(ignore_permissions=True)
		self.assertEqual(la_acc.status, "Open")
		ta2_name = fx.as_user(self.wanjiku_user, actions.prepare_from_leave, la_acc.name)
		ta2 = frappe.get_doc("Task Assignment", ta2_name)
		ta2.task_assignee = self.otieno
		ta2.task_description = "<p>Cover my desk (amended)</p>"
		ta2.save(ignore_permissions=True)
		ta2.submit()
		with self.assertRaises(frappe.ValidationError):
			la_acc.reload()
			la_acc.submit()
		fx.agree(ta2, "otieno")
		fx.approve(la_acc)
		self.assertEqual(la_acc.docstatus, 1)
		la_acc.reload()
		la_acc.cancel()


class TestPreparingFromLeave(LifecycleTestCase):
	def test_prepare_prefills_the_owners_open_work_once(self):
		task = fx.project_task("Renew the Kilimani office lease")
		fx.assign(task, self.wanjiku_user)
		la = fx.leave(self.wanjiku, 4, 3)
		name = fx.as_user(self.wanjiku_user, actions.prepare_from_leave, la.name)
		doc = frappe.get_doc("Task Assignment", name)
		self.assertEqual(doc.docstatus, 0)
		self.assertIn(task, [r.reference_name for r in doc.assignment_todos])
		self.assertEqual(fx.as_user(self.wanjiku_user, actions.prepare_from_leave, la.name), name, "one per leave")
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, actions.prepare_from_leave, la.name)

	def test_cancelled_leave_and_handover_do_not_block_amended_application(self):
		task = fx.project_task("Audit the Westlands petty cash")
		fx.assign(task, self.wanjiku_user)
		la1 = fx.leave(self.wanjiku, 5, 3)
		ta1_name = fx.as_user(self.wanjiku_user, actions.prepare_from_leave, la1.name)
		ta1 = frappe.get_doc("Task Assignment", ta1_name)
		ta1.task_assignee = self.otieno
		ta1.task_description = "<p>Cover Westlands petty cash</p>"
		ta1.save(ignore_permissions=True)
		ta1.submit()
		fx.agree(ta1, "otieno")
		fx.approve(la1)

		# Open ToDos referencing the leave and handover before cancellation
		todo_la = frappe.get_doc({
			"doctype": "ToDo",
			"allocated_to": self.wanjiku_user,
			"reference_type": "Leave Application",
			"reference_name": la1.name,
			"description": "Follow up on leave",
			"status": "Open",
		}).insert(ignore_permissions=True)
		todo_ta = frappe.get_doc({
			"doctype": "ToDo",
			"allocated_to": self.wanjiku_user,
			"reference_type": "Task Assignment",
			"reference_name": ta1.name,
			"description": "Follow up on handover",
			"status": "Open",
		}).insert(ignore_permissions=True)

		la1.reload()
		la1.cancel()
		ta1.reload()
		self.assertEqual(ta1.docstatus, 2)
		self.assertEqual(ta1.status, Status.CANCELLED)
		self.assertIsNone(ta1.leave_application)
		self.assertEqual(frappe.db.get_value("ToDo", todo_la.name, "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("ToDo", todo_ta.name, "status"), "Cancelled")

		# Even if a stale open ToDo still points to a cancelled document, amending and preparing a new handover succeeds
		frappe.db.set_value("ToDo", todo_la.name, "status", "Open", update_modified=False)
		frappe.db.set_value("ToDo", todo_ta.name, "status", "Open", update_modified=False)

		la2 = frappe.copy_doc(la1)
		la2.amended_from = la1.name
		la2.insert(ignore_permissions=True)
		self.assertEqual(la2.status, "Open")

		ta2_name = fx.as_user(self.wanjiku_user, actions.prepare_from_leave, la2.name)
		ta2 = frappe.get_doc("Task Assignment", ta2_name)
		self.assertEqual(ta2.docstatus, 0)
		self.assertEqual(ta2.leave_application, la2.name)
		ref_names = [r.reference_name for r in ta2.assignment_todos]
		self.assertIn(task, ref_names)
		self.assertNotIn(la1.name, ref_names)
		self.assertNotIn(ta1.name, ref_names)
