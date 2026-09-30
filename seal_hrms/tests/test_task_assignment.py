# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Task Assignment: work moves to the stand-in, and comes back.

Wanjiku goes on leave; Otieno covers. The things that went wrong before 1.3.0
are each pinned here: work that never came back, a stand-in handed a document
they could not open, the original assignor overwritten, and tasks typed into
the handover whose ToDo was never recorded.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today

from seal_hrms.seal_hrms import handover, handover_jobs
from seal_hrms.seal_hrms.handover import RowStatus, Status
from seal_hrms.seal_hrms.task_assignment_access import has_permission, query_conditions
from seal_hrms.tests import _handover_fixtures as fx


class TaskAssignmentTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.otieno = fx.ensure_employee("otieno")
		cls.njeri = fx.ensure_employee("njeri")
		cls.wanjiku_user = fx.email("wanjiku")
		cls.otieno_user = fx.email("otieno")
		cls.njeri_user = fx.email("njeri")

	def setUp(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno, self.njeri])

	def tearDown(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno, self.njeri])

	def _handover_with_task(self, start_offset=3, days=5, submit=True):
		"""A handover that has taken effect: agreed, approved, and the leave begun."""
		task = fx.project_task("Reconcile the Westlands petty cash")
		todo = fx.assign(task, self.wanjiku_user)
		la = fx.leave(self.wanjiku, start_offset, days)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"todo": todo, "description": "Reconcile petty cash",
		                                                   "reference_type": "Task", "reference_name": task}],
		                 submit=submit)
		if submit:
			fx.take_effect(ta, la)
		return task, todo, la, ta

	def _typed_in(self, description):
		la = fx.leave(self.wanjiku, 3, 5)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"description": description}])
		return fx.take_effect(ta, la)


class TestWorkMoves(TaskAssignmentTestCase):
	def test_stand_in_gets_the_work_and_can_open_it(self):
		task, todo, _la, ta = self._handover_with_task()
		ta.reload()
		row = ta.assignment_todos[0]

		self.assertEqual(ta.status, Status.ACTIVE)
		self.assertEqual(row.row_status, RowStatus.HANDED_OVER)
		stand_in_todos = fx.open_todos(self.otieno_user, task)
		self.assertEqual(stand_in_todos, [row.stand_in_todo])
		self.assertEqual(frappe.db.get_value("ToDo", row.stand_in_todo, "assigned_by"), self.wanjiku_user)
		# Otieno has no Task permission of his own: without the share he could not open the work.
		self.assertTrue(frappe.db.exists("DocShare", {"share_doctype": "Task", "share_name": task, "user": self.otieno_user}))
		self.assertTrue(row.shared_with_stand_in)

	def test_employee_todo_is_cancelled_not_rewritten(self):
		task, todo, _la, ta = self._handover_with_task()
		original = frappe.get_doc("ToDo", todo)
		self.assertEqual(original.status, "Cancelled")
		self.assertEqual(original.allocated_to, self.wanjiku_user)
		self.assertEqual(original.assigned_by, "Administrator", "the original assignor must survive the move")
		ta.reload()
		self.assertEqual(ta.assignment_todos[0].original_assignor, "Administrator")
		assigned = frappe.parse_json(frappe.db.get_value("Task", task, "_assign") or "[]")
		self.assertEqual(assigned, [self.otieno_user])

	def test_moving_twice_does_nothing_the_second_time(self):
		task, _todo, _la, ta = self._handover_with_task()
		frappe.db.set_value("Task Assignment", ta.name, "activated_at", None)  # pretend a second caller got in
		self.assertTrue(handover.activate(ta.name))
		self.assertEqual(len(fx.open_todos(self.otieno_user, task)), 1, "the row remembers it has moved")
		self.assertFalse(handover.activate(ta.name), "the second call sees activated_at and stops")

	def test_typed_in_task_gets_a_todo_and_it_is_recorded(self):
		ta = self._typed_in("Call Kilimani landlord about the lease")
		row = ta.assignment_todos[0]
		self.assertTrue(row.stand_in_todo, "the 2024 code created this ToDo and never wrote it back")
		self.assertEqual(frappe.db.get_value("ToDo", row.stand_in_todo, "allocated_to"), self.otieno_user)

	def test_closed_work_is_not_handed_over(self):
		task = fx.project_task("File the August KRA returns")
		todo = fx.assign(task, self.wanjiku_user)
		frappe.db.set_value("ToDo", todo, "status", "Closed")
		la = fx.leave(self.wanjiku, 3, 5)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"todo": todo, "description": "KRA returns",
		                                                   "reference_type": "Task", "reference_name": task}])
		fx.take_effect(ta, la)
		self.assertEqual(ta.assignment_todos[0].row_status, RowStatus.ALREADY_DONE)
		self.assertEqual(fx.open_todos(self.otieno_user, task), [])


class TestWorkComesBack(TaskAssignmentTestCase):
	def test_open_work_returns_from_the_original_assignor(self):
		task, _todo, _la, ta = self._handover_with_task()
		self.assertTrue(handover.hand_back(ta.name))
		ta.reload()
		row = ta.assignment_todos[0]

		self.assertEqual(ta.status, Status.HANDED_BACK)
		self.assertEqual(row.row_status, RowStatus.HANDED_BACK)
		self.assertEqual(fx.open_todos(self.otieno_user, task), [])
		mine = fx.open_todos(self.wanjiku_user, task)
		self.assertEqual(mine, [row.todo])
		self.assertEqual(frappe.db.get_value("ToDo", row.todo, "assigned_by"), "Administrator")
		self.assertFalse(frappe.db.exists("DocShare", {"share_doctype": "Task", "share_name": task, "user": self.otieno_user}),
		                 "the share was only for the cover")
		self.assertFalse(handover.hand_back(ta.name), "a second return does nothing")

	def test_work_finished_while_away_stays_finished(self):
		task, _todo, _la, ta = self._handover_with_task()
		ta.reload()
		frappe.db.set_value("ToDo", ta.assignment_todos[0].stand_in_todo, "status", "Closed")
		handover.hand_back(ta.name)
		ta.reload()
		self.assertEqual(ta.assignment_todos[0].row_status, RowStatus.DONE_WHILE_AWAY)
		self.assertEqual(fx.open_todos(self.wanjiku_user, task), [], "finished work is not handed back to do again")

	def test_stand_in_keeps_work_they_already_had(self):
		task = fx.project_task("Supplier onboarding for Mombasa Road depot")
		todo = fx.assign(task, self.wanjiku_user)
		already = fx.assign(task, self.otieno_user)
		la = fx.leave(self.wanjiku, 3, 5)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"todo": todo, "description": "Supplier onboarding",
		                                                   "reference_type": "Task", "reference_name": task}])
		fx.take_effect(ta, la)
		handover.hand_back(ta.name)
		self.assertEqual(frappe.db.get_value("ToDo", already, "status"), "Open",
		                 "Otieno was on this before the handover and stays on it")

	def test_typed_in_task_comes_back_to_the_owner(self):
		ta = self._typed_in("Call Kilimani landlord about the lease")
		handover.hand_back(ta.name)
		ta.reload()
		row = ta.assignment_todos[0]
		self.assertEqual(frappe.db.get_value("ToDo", row.stand_in_todo, "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("ToDo", row.todo, "allocated_to"), self.wanjiku_user)

	def test_daily_job_returns_work_on_the_first_day_back(self):
		_task, _todo, la, ta = self._handover_with_task(start_offset=1, days=2)
		self.assertEqual(handover_jobs.hand_back_ended_leave(on_date=la.to_date), [], "not while still away")
		self.assertEqual(handover_jobs.hand_back_ended_leave(on_date=ta.return_date), [ta.name])

	def test_cancelling_the_leave_calls_off_the_handover(self):
		task, _todo, la, ta = self._handover_with_task()
		la.reload()
		la.cancel()
		ta.reload()
		self.assertEqual(ta.docstatus, 2)
		self.assertEqual(ta.status, Status.CANCELLED)
		self.assertEqual(len(fx.open_todos(self.wanjiku_user, task)), 1)
		self.assertEqual(fx.open_todos(self.otieno_user, task), [])

	def test_rejecting_the_leave_calls_off_the_handover(self):
		task, _todo, la, ta = self._handover_with_task(submit=False)
		ta.submit()
		fx.agree(ta, "otieno")
		la.reload()
		la.status = "Rejected"
		la.submit()
		ta.reload()
		self.assertEqual(ta.status, Status.CANCELLED)
		self.assertEqual(len(fx.open_todos(self.wanjiku_user, task)), 1, "nothing had moved, and nothing is lost")


class TestChoosingAStandIn(TaskAssignmentTestCase):
	def test_stand_in_away_for_part_of_the_leave_is_refused(self):
		fx.leave(self.otieno, 6, 4)  # begins while Wanjiku is still away
		la = fx.leave(self.wanjiku, 3, 5)
		with self.assertRaises(frappe.ValidationError):
			fx.handover(self.wanjiku, self.otieno, la, [{"description": "Weekly stock count"}], submit=False)

	def test_cannot_cover_yourself(self):
		la = fx.leave(self.wanjiku, 3, 5)
		with self.assertRaises(frappe.ValidationError):
			fx.handover(self.wanjiku, self.wanjiku, la, [{"description": "Weekly stock count"}], submit=False)

	def test_picker_leaves_out_colleagues_who_are_away(self):
		from seal_hrms.seal_hrms.doctype.task_assignment.task_assignment import get_assignable_employees

		fx.leave(self.otieno, 4, 2)
		la = fx.leave(self.wanjiku, 3, 5)
		names = [r[0] for r in get_assignable_employees("Employee", "", "name", 0, 50,
		                                                 {"employee": self.wanjiku, "leave_application": la.name})]
		self.assertNotIn(self.otieno, names)
		self.assertIn(self.njeri, names)


class TestWhoCanSeeIt(TaskAssignmentTestCase):
	def test_permission_hook_returns_a_bool_for_every_ptype(self):
		_task, _todo, _la, ta = self._handover_with_task()
		for user in (self.wanjiku_user, self.otieno_user, self.njeri_user, fx.approver(), "Guest"):
			for ptype in ("read", "write", "submit", "cancel", "delete", "create", "amend", "print"):
				result = has_permission(ta, ptype, user)
				self.assertIsInstance(result, bool, f"{user}/{ptype} returned {result!r}")

	def test_each_person_sees_what_they_should(self):
		_task, _todo, _la, ta = self._handover_with_task()
		self.assertTrue(has_permission(ta, "write", self.wanjiku_user), "the owner prepares their own")
		self.assertTrue(has_permission(ta, "read", self.otieno_user), "the stand-in reads what they cover")
		self.assertFalse(has_permission(ta, "write", self.otieno_user), "the stand-in does not rewrite it")
		self.assertTrue(has_permission(ta, "read", fx.approver()), "the leave approver can check cover")
		self.assertFalse(has_permission(ta, "read", self.njeri_user), "an unrelated colleague cannot")

	def test_stand_in_can_open_the_form_through_the_whole_permission_stack(self):
		"""HRMS gives every login an "Employee = themselves" User Permission.

		Without ignore_user_permissions on the Employee links, that alone hides a
		colleague's handover from the stand-in it names, whatever our hook says.
		"""
		_task, _todo, _la, ta = self._handover_with_task()
		self.assertTrue(frappe.has_permission("Task Assignment", "read", doc=ta, user=self.otieno_user))
		self.assertFalse(frappe.has_permission("Task Assignment", "read", doc=ta, user=self.njeri_user))

	def test_list_shows_the_same_people(self):
		_task, _todo, _la, ta = self._handover_with_task()
		for user, expected in ((self.otieno_user, True), (self.njeri_user, False), (fx.approver(), True)):
			frappe.set_user(user)
			try:
				found = ta.name in frappe.get_list("Task Assignment", pluck="name")
			finally:
				frappe.set_user("Administrator")
			self.assertEqual(found, expected, f"{user} list visibility")
		self.assertEqual(query_conditions("Administrator"), "")

	def test_nobody_reads_someone_elses_work_list(self):
		from seal_hrms.seal_hrms.doctype.task_assignment.task_assignment import get_employee_tasks

		frappe.set_user(self.njeri_user)
		try:
			with self.assertRaises(frappe.PermissionError):
				get_employee_tasks(self.wanjiku)
		finally:
			frappe.set_user("Administrator")
