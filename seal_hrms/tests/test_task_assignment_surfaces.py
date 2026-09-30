# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Where handovers show up: My Desk, the reports, and the Self Service workspace.

The first class runs on every site. My Desk is optional, so this app may not
import it anywhere it would load on a site without it (SEAL_DEV_RULES §3.15).
"""

import ast
import json
import pathlib
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms import handover, handover_work
from seal_hrms.tests import _handover_fixtures as fx

HOST = "seal_desk"
APP = "seal_hrms"


def _imports_that_run_on_load(tree: ast.AST) -> list[int]:
	found, stack = [], [tree]
	while stack:
		node = stack.pop()
		for child in ast.iter_child_nodes(node):
			if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
				continue
			names = []
			if isinstance(child, ast.Import):
				names = [alias.name for alias in child.names]
			elif isinstance(child, ast.ImportFrom):
				names = [child.module or ""]
			if any(name.split(".")[0] == HOST for name in names):
				found.append(child.lineno)
			stack.append(child)
	return found


class TestDeskSubscriptionNeedsNoDesk(unittest.TestCase):
	def test_no_module_level_import_of_the_desk(self):
		root = pathlib.Path(frappe.get_app_path(APP))
		offenders = {
			str(path.relative_to(root)): lines
			for path in root.rglob("*.py")
			if "node_modules" not in path.parts and (lines := _imports_that_run_on_load(ast.parse(path.read_text())))
		}
		self.assertEqual(offenders, {}, f"{HOST} imported at module level: {offenders}")

	def test_the_desk_is_not_required(self):
		required = frappe.get_hooks("required_apps", app_name=APP) or []
		self.assertNotIn(HOST, [entry.split("/")[-1] for entry in required])


class SurfacesTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.otieno = fx.ensure_employee("otieno")
		cls.wanjiku_user, cls.otieno_user = fx.email("wanjiku"), fx.email("otieno")

	def setUp(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno])

	def tearDown(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno])

	def _titles(self, user, on_date=None):
		return [w.title for w in handover_work.work_for(user, on_date)]


class TestWhatReachesEachPerson(SurfacesTestCase):
	def test_leave_coming_up_asks_for_a_handover(self):
		fx.leave(self.wanjiku, 3, 2)
		self.assertTrue(any("Hand over your work" in t for t in self._titles(self.wanjiku_user)))

	def test_leave_far_off_does_not_nag_yet(self):
		fx.leave(self.wanjiku, 40, 2)
		self.assertFalse(any("Hand over your work" in t for t in self._titles(self.wanjiku_user)))

	def test_the_stand_in_is_asked_then_sees_the_cover(self):
		la = fx.leave(self.wanjiku, 3, 2)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"description": "Weekly stock count"}])
		asked = [w for w in handover_work.work_for(self.otieno_user) if w.name == ta.name]
		self.assertEqual([w.kind for w in asked], ["approval"])
		self.assertFalse(any("Hand over your work" in t for t in self._titles(self.wanjiku_user)),
		                 "a handover exists, so the owner is not asked again")
		fx.take_effect(ta, la)
		covering = [w for w in handover_work.work_for(self.otieno_user) if w.name == ta.name]
		self.assertEqual([w.kind for w in covering], ["task"])
		self.assertIn("Covering for", covering[0].title)

	def test_the_owner_hears_the_work_is_back(self):
		la = fx.leave(self.wanjiku, 3, 2)
		ta = fx.handover(self.wanjiku, self.otieno, la, [{"description": "Weekly stock count"}])
		fx.take_effect(ta, la)
		handover.hand_back(ta.name)
		self.assertTrue(any("Welcome back" in t for t in self._titles(self.wanjiku_user)))
		later = add_days(today(), handover_work.WELCOME_BACK_DAYS + 1)
		self.assertFalse(any("Welcome back" in t for t in self._titles(self.wanjiku_user, later)))


@unittest.skipUnless(HOST in frappe.get_installed_apps(), f"{HOST} is not installed")
class TestDeskItems(SurfacesTestCase):
	def test_records_become_desk_items(self):
		from seal_desk.desk.schema import Item

		from seal_hrms.desk.providers import handover_work as provider

		fx.leave(self.wanjiku, 3, 2)

		class Ctx:
			cache = {}

			def memo(self, key, factory):
				return self.cache.setdefault(key, factory())

			def priority_from_due(self, due):
				return 0

		items = provider(self.wanjiku_user, Ctx())
		self.assertTrue(items and all(isinstance(i, Item) for i in items))

	def test_the_provider_is_declared(self):
		self.assertIn("seal_hrms.desk.providers.handover_work", frappe.get_hooks("seal_desk_providers", app_name=APP))


class TestTheFormKnowsWhoIsLooking(SurfacesTestCase):
	def test_staff_learn_their_own_employee_from_the_server(self):
		"""Found by the browser suite: staff may not filter Employee on user_id from the client.

		The form asked `frappe.db.get_value("Employee", {"user_id": ...})` and
		every non-HR stand-in got a permission error instead of an Accept button.
		"""
		from seal_hrms.seal_hrms.task_assignment_access import my_employee

		self.assertEqual(fx.as_user(self.otieno_user, my_employee), self.otieno)
		self.assertIn(my_employee, frappe.whitelisted)


class TestReports(SurfacesTestCase):
	def test_who_is_covering_whom_lists_undecided_cover_first(self):
		from seal_hrms.seal_hrms.report.who_is_covering_whom.who_is_covering_whom import execute

		la_a = fx.leave(self.wanjiku, 3, 2)
		agreed = fx.handover(self.wanjiku, self.otieno, la_a, [{"description": "Stock count"}])
		fx.agree(agreed, "otieno")
		la_b = fx.leave(self.wanjiku, 8, 2)
		waiting = fx.handover(self.wanjiku, self.otieno, la_b, [{"description": "Board pack"}])
		_columns, rows = execute({"company": fx.COMPANY, "from_date": today(), "to_date": add_days(today(), 20)})
		names = [r["name"] for r in rows]
		self.assertLess(names.index(waiting.name), names.index(agreed.name))

	def test_stand_in_load_counts_colleagues_covered_at_once(self):
		from seal_hrms.seal_hrms.report.stand_in_load.stand_in_load import execute

		njeri = fx.ensure_employee("njeri")
		try:
			fx.handover(self.wanjiku, self.otieno, fx.leave(self.wanjiku, 3, 4), [{"description": "Stock count"}])
			fx.handover(njeri, self.otieno, fx.leave(njeri, 4, 2), [{"description": "Payroll queries"}])
			_columns, rows = execute({"company": fx.COMPANY, "from_date": today(), "to_date": add_days(today(), 20)})
			otieno = next(r for r in rows if r["stand_in"] == self.otieno)
			self.assertEqual(otieno["people"], 2)
			self.assertEqual(otieno["at_once"], 2)
		finally:
			fx.cleanup([njeri])


class TestWorkspaceWiring(unittest.TestCase):
	def test_self_service_reaches_handovers(self):
		root = pathlib.Path(frappe.get_app_path(APP))
		sidebar = json.loads((root / "workspace_sidebar" / "self_service.json").read_text())
		links = {i.get("link_to") for i in sidebar["items"]}
		self.assertTrue({"Task Assignment", "Who Is Covering Whom", "Stand-in Load", "Task Assignment Policy"} <= links)
		workspace = json.loads((root / "seal_hrms" / "workspace" / "self_service" / "self_service.json").read_text())
		self.assertIn("Task Assignment", {s["link_to"] for s in workspace["shortcuts"]})
		blocks = json.loads((root / "fixtures" / "custom_html_block.json").read_text())
		overview = next(b for b in blocks if b["name"] == "HRMS ESS Overview")
		self.assertIn('href="/app/task-assignment"', overview["html"])
