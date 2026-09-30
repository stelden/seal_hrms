# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""The one-off return of work stranded by the pre-1.3.0 Task Assignment (decision T1).

Each case recreates what the 2024 code left behind: a submitted handover with
no status, and a ToDo edited in place to point at the stand-in. The handover
has to be marked submitted directly, because the current controller would move
the work properly and there would be nothing stranded to test.
"""

import frappe
from frappe.tests import IntegrationTestCase

from seal_hrms.patches.v1_11 import return_stranded_task_assignments as patch
from seal_hrms.seal_hrms.handover import Status
from seal_hrms.tests import _handover_fixtures as fx


class TestLegacyReturn(IntegrationTestCase):
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

	def tearDown(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno, self.njeri])

	def _legacy(self, stand_in, start_offset, rows):
		la = fx.leave(self.wanjiku, start_offset, 3)
		ta = fx.handover(self.wanjiku, stand_in, la, rows, submit=False)
		frappe.db.set_value("Task Assignment", ta.name, {"docstatus": 1, "status": ""}, update_modified=False)
		for row in ta.assignment_todos:
			frappe.db.set_value("Task Assignment ToDo", row.name, "docstatus", 1, update_modified=False)
		return ta

	def _as_2024_code_left_it(self, todo, stand_in_user):
		"""What `on_submit` did before 1.3.0: rewrite the ToDo to point at the stand-in."""
		doc = frappe.get_doc("ToDo", todo)
		doc.allocated_to = stand_in_user
		doc.assigned_by = self.wanjiku_user
		doc.save(ignore_permissions=True)

	def _task_todo(self, subject):
		task = fx.project_task(subject)
		return task, fx.assign(task, self.wanjiku_user)

	def test_stranded_work_goes_back_to_its_owner_once(self):
		task, todo = self._task_todo("Chase the Ngong Road rent arrears")
		ta = self._legacy(self.otieno, -20, [{"todo": todo, "description": "Rent arrears",
		                                      "reference_type": "Task", "reference_name": task}])
		self._as_2024_code_left_it(todo, self.otieno_user)

		patch.execute()
		self.assertEqual(frappe.db.get_value("ToDo", todo, "allocated_to"), self.wanjiku_user)
		self.assertEqual(frappe.db.get_value("Task Assignment", ta.name, "status"), Status.LEGACY)
		self.assertEqual(frappe.db.get_value("Task Assignment ToDo", ta.assignment_todos[0].name, "row_status"), "Handed Back")
		assigned = frappe.parse_json(frappe.db.get_value("Task", task, "_assign") or "[]")
		self.assertEqual(assigned, [self.wanjiku_user])

		emails = frappe.db.count("Email Queue", {"reference_name": ta.name})
		patch.execute()  # the second run
		self.assertEqual(frappe.db.count("Email Queue", {"reference_name": ta.name}), emails, "no second email")

	def test_status_default_left_by_migrate_is_still_legacy(self):
		"""Adding the column stamps every old row "Draft" before the patch runs."""
		task, todo = self._task_todo("Collect the Rongai site keys")
		ta = self._legacy(self.otieno, -20, [{"todo": todo, "description": "Site keys",
		                                      "reference_type": "Task", "reference_name": task}])
		frappe.db.set_value("Task Assignment", ta.name, "status", "Draft", update_modified=False)
		self._as_2024_code_left_it(todo, self.otieno_user)
		patch.execute()
		self.assertEqual(frappe.db.get_value("Task Assignment", ta.name, "status"), Status.LEGACY)
		self.assertEqual(frappe.db.get_value("ToDo", todo, "allocated_to"), self.wanjiku_user)

	def test_handover_to_yourself_has_nothing_to_return(self):
		"""Three MHC records name the owner as their own stand-in; they must not be "returned" every run."""
		task, todo = self._task_todo("Sunday service rota for Ruaka")
		la = fx.leave(self.wanjiku, -20, 3)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"todo": todo, "description": "Rota",
		                                                  "reference_type": "Task", "reference_name": task}], submit=False)
		# The 2024 form allowed it; today's validate refuses, so set it the way the old record reads.
		frappe.db.set_value("Task Assignment", ta.name, {"docstatus": 1, "status": "", "task_assignee": self.wanjiku},
		                    update_modified=False)
		# Names repeat across tests (each rolls back its naming series), so count the change.
		before = frappe.db.count("Email Queue", {"reference_name": ta.name})
		patch.execute()
		self.assertFalse(frappe.db.get_value("Task Assignment ToDo", ta.assignment_todos[0].name, "row_status"))
		self.assertEqual(frappe.db.count("Email Queue", {"reference_name": ta.name}), before)

	def test_typed_in_task_is_found_and_returned(self):
		ta = self._legacy(self.otieno, -20, [{"description": "Renew the Karen office insurance"}])
		made = frappe.new_doc("ToDo")  # the ToDo the 2024 code created and never recorded
		made.allocated_to = self.otieno_user
		made.assigned_by = self.wanjiku_user
		made.description = "Renew the Karen office insurance"
		made.insert(ignore_permissions=True)

		patch.execute()
		self.assertEqual(frappe.db.get_value("ToDo", made.name, "allocated_to"), self.wanjiku_user)
		self.assertEqual(frappe.db.get_value("Task Assignment ToDo", ta.assignment_todos[0].name, "todo"), made.name)

	def test_work_moved_on_since_is_left_alone(self):
		task, todo = self._task_todo("Quarterly fire drill at Upper Hill")
		self._legacy(self.otieno, -20, [{"todo": todo, "description": "Fire drill",
		                                 "reference_type": "Task", "reference_name": task}])
		self._as_2024_code_left_it(todo, self.njeri_user)
		patch.execute()
		self.assertEqual(frappe.db.get_value("ToDo", todo, "allocated_to"), self.njeri_user)

	def test_leave_not_yet_over_is_left_alone(self):
		task, todo = self._task_todo("Board pack for the October meeting")
		self._legacy(self.otieno, 5, [{"todo": todo, "description": "Board pack",
		                               "reference_type": "Task", "reference_name": task}])
		self._as_2024_code_left_it(todo, self.otieno_user)
		patch.execute()
		self.assertEqual(frappe.db.get_value("ToDo", todo, "allocated_to"), self.otieno_user)

	def test_the_most_recent_handover_decides(self):
		task, todo = self._task_todo("Payroll variance for Thika branch")
		row = {"todo": todo, "description": "Payroll variance", "reference_type": "Task", "reference_name": task}
		self._legacy(self.njeri, -40, [dict(row)])
		self._legacy(self.otieno, -20, [dict(row)])
		# Still with the stand-in of the OLDER handover: someone gave it to Njeri after Otieno had it.
		self._as_2024_code_left_it(todo, self.njeri_user)
		patch.execute()
		self.assertEqual(frappe.db.get_value("ToDo", todo, "allocated_to"), self.njeri_user)

	def test_drafts_become_draft_not_legacy(self):
		la = fx.leave(self.wanjiku, 10, 2)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"description": "Stock take"}], submit=False)
		frappe.db.set_value("Task Assignment", ta.name, "status", "", update_modified=False)
		patch.execute()
		self.assertEqual(frappe.db.get_value("Task Assignment", ta.name, "status"), Status.DRAFT)
