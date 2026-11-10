# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""The Line Manager role and page (seal_hrms/seal_hrms/line_manager.py; Keith, 2026-11-11).

Achieng Odhiambo manages Otieno Ochieng, who manages Njeri Mwangi; Wanjiku Kamau is a
colleague. Pinned: the role follows who has direct reports, on Employee and User saves and
the daily pass; a role given by hand or by a Role Profile is never taken away; a Role
Profile rebuilding a user's roles does not drop it; the team is the direct reports and one
level down; "Who's Away This Week" shows only leave the viewer may read; the shipped page is
offered to the role once and never over a Desk Manager's choice.

Each test runs inside a savepoint that is rolled back, and refuses a commit.
"""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from seal_hrms.seal_hrms import line_manager as lm
from seal_hrms.tests import _handover_fixtures as fx

SAVEPOINT = "seal_hrms_test_line_manager"
PROFILE = "Kilimani Supervisors"


def _refuse_commit():
	raise AssertionError("a line manager test tried to commit")


class LineManagerTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		frappe.set_user("Administrator")
		cls.achieng = fx.ensure_employee("achieng")
		cls.otieno = fx.ensure_employee("otieno")
		cls.njeri = fx.ensure_employee("njeri")
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.achieng_user, cls.otieno_user, cls.wanjiku_user = fx.email("achieng"), fx.email("otieno"), fx.email("wanjiku")
		fx.approver()  # Achieng approves leave

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.savepoint(SAVEPOINT)
		frappe.db.before_commit.add(_refuse_commit)
		lm.ensure_role()
		for user in (self.achieng_user, self.otieno_user):
			if frappe.db.get_value("User", user, "user_type") != "System User":
				self.skipTest(f"{user} is not a desk user on this site")
		# Start from nobody reporting to anyone in the cast, and no role. Arranged directly (rolled
		# back): years of dev.local data may not pass an Employee save, and these are not under test.
		for emp in (self.achieng, self.otieno, self.njeri, self.wanjiku):
			frappe.db.set_value("Employee", emp, "reports_to", None, update_modified=False)
		for emp in frappe.get_all("Employee", filters={"reports_to": ["in", [self.achieng, self.otieno, self.wanjiku]]}, pluck="name"):
			frappe.db.set_value("Employee", emp, "reports_to", None, update_modified=False)
		frappe.db.delete("Has Role", {"role": lm.ROLE, "parent": ["in", [self.achieng_user, self.otieno_user, self.wanjiku_user]]})
		frappe.db.delete("DefaultValue", {"parent": lm.LEDGER})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.before_commit.reset()
		frappe.db.rollback(save_point=SAVEPOINT)
		for user in (self.achieng_user, self.otieno_user, self.wanjiku_user):
			frappe.clear_cache(user=user)

	def _newcomers(self):
		"""Kamau Njoroge (a desk user) and Akinyi Wekesa, new this test: tests that save a User leave
		the shared cast alone, whose accounts other suites sign in with."""
		people = []
		for first, last, gender, roles, phone in (
			("Kamau", "Njoroge", "Male", ("Employee", "Leave Approver"), "254722604118"),
			("Akinyi", "Wekesa", "Female", ("Employee",), "254733215907"),
		):
			address = f"{first.lower()}.{last.lower()}@{fx.DOMAIN}"
			if not frappe.db.exists("User", address):
				user = frappe.new_doc("User")
				user.update({"email": address, "first_name": first, "last_name": last, "send_welcome_email": 0})
				user.insert(ignore_permissions=True)
				user.add_roles(*roles)
			emp = frappe.db.get_value("Employee", {"user_id": address}, "name")
			if not emp:
				doc = frappe.new_doc("Employee")
				doc.update({
					"first_name": first, "last_name": last, "gender": gender, "date_of_birth": "1991-07-03",
					"date_of_joining": "2023-03-01", "status": "Active", "company": fx.COMPANY, "user_id": address, "cell_number": phone,
					"holiday_list": frappe.db.get_value("Company", fx.COMPANY, "default_holiday_list"),
				})
				doc.insert(ignore_permissions=True)
				emp = doc.name
			self.addCleanup(frappe.clear_cache, user=address)
			people.append(frappe._dict(user=address, employee=emp))
		if frappe.db.get_value("User", people[0].user, "user_type") != "System User":
			self.skipTest("Kamau is not a desk user on this site")
		return people[0], people[1].employee

	def _report(self, employee, manager):
		doc = frappe.get_doc("Employee", employee)
		doc.reports_to = manager
		doc.save(ignore_permissions=True)

	def _holds(self, user):
		return lm._holds(user)


class TestTheRole(LineManagerTestCase):
	def test_a_manager_gets_the_role_when_someone_reports_to_them(self):
		self.assertFalse(self._holds(self.achieng_user))
		self._report(self.otieno, self.achieng)
		self.assertTrue(self._holds(self.achieng_user))
		self.assertTrue(lm._granted_by_us(self.achieng_user))
		self.assertFalse(self._holds(self.otieno_user), "nobody reports to Otieno yet")

	def test_the_role_goes_with_the_last_report(self):
		self._report(self.otieno, self.achieng)
		self._report(self.njeri, self.achieng)
		self._report(self.otieno, None)
		self.assertTrue(self._holds(self.achieng_user), "Njeri still reports to her")
		self._report(self.njeri, self.otieno)
		self.assertFalse(self._holds(self.achieng_user))
		self.assertFalse(lm._granted_by_us(self.achieng_user))
		self.assertTrue(self._holds(self.otieno_user), "the new manager gets it in the same save")

	def test_a_report_who_leaves_takes_it_away(self):
		self._report(self.otieno, self.achieng)
		frappe.db.set_value("Employee", self.otieno, "status", "Left", update_modified=False)
		self.assertEqual(lm.sync_user(self.achieng_user), "removed")

	def test_a_role_given_by_hand_stays(self):
		frappe.get_doc("User", self.otieno_user).add_roles(lm.ROLE)
		self.assertIsNone(lm.sync_user(self.otieno_user))
		self.assertTrue(self._holds(self.otieno_user))

	def test_only_desk_users_get_it(self):
		if frappe.db.get_value("User", self.wanjiku_user, "user_type") == "System User":
			self.skipTest("Wanjiku is a desk user on this site")
		self._report(self.njeri, self.wanjiku)
		self.assertFalse(self._holds(self.wanjiku_user), "My Desk is for desk users; the role would reach nothing")

	def _profile(self, *roles):
		"""A Role Profile, written row by row: inserting one through its controller queues an update
		of its users behind a lock file that outlives the test's rollback."""
		profile = frappe.new_doc("Role Profile")
		profile.role_profile = profile.name = PROFILE
		for role in roles:
			profile.append("roles", {"role": role})
		profile.db_insert()
		for row in profile.roles:
			row.db_insert()
		frappe.clear_document_cache("Role Profile", PROFILE)
		return PROFILE

	def test_a_role_profile_save_does_not_drop_it(self):
		manager, report = self._newcomers()
		self._report(report, manager.employee)
		self.assertTrue(self._holds(manager.user))
		user = frappe.get_doc("User", manager.user)
		user.append("role_profiles", {"role_profile": self._profile("Employee", "Leave Approver")})
		user.save(ignore_permissions=True)  # rebuilds the roles from the profile, which lacks Line Manager
		self.assertTrue(self._holds(manager.user))

	def test_a_role_from_a_profile_is_not_removed(self):
		manager, report = self._newcomers()
		self._report(report, manager.employee)
		frappe.get_doc({"doctype": "User Role Profile", "parent": manager.user, "parenttype": "User", "parentfield": "role_profiles", "role_profile": self._profile("Employee", lm.ROLE)}).insert(ignore_permissions=True)
		self._report(report, None)
		self.assertTrue(self._holds(manager.user))
		self.assertFalse(lm._granted_by_us(manager.user))

	def test_the_daily_pass_catches_up(self):
		frappe.db.set_value("Employee", self.otieno, "reports_to", self.achieng, update_modified=False)  # no event ran
		self.assertFalse(self._holds(self.achieng_user))
		lm.sync_user(self.achieng_user)  # what sync_all does for each manager, without touching the site's other users
		self.assertTrue(self._holds(self.achieng_user))

	def test_the_role_grants_no_desk_access(self):
		self.assertEqual(frappe.db.get_value("Role", lm.ROLE, "desk_access"), 0)


class TestTheTeam(LineManagerTestCase):
	def test_team_is_direct_reports_and_one_level_down(self):
		self._report(self.otieno, self.achieng)
		self._report(self.njeri, self.otieno)
		self.assertEqual(lm.team(self.achieng_user), [self.otieno, self.njeri])
		self.assertEqual(lm.team(self.otieno_user), [self.njeri])
		self.assertEqual(lm.team(self.wanjiku_user), [])  # nobody reports to her

	def test_week_runs_monday_to_sunday(self):
		self.assertEqual([str(d) for d in lm.week_of("2026-11-12")], ["2026-11-09", "2026-11-15"])

	def test_whos_away_shows_only_leave_the_viewer_may_read(self):
		self._report(self.otieno, self.achieng)
		self._report(self.njeri, self.otieno)
		leave = fx.leave(self.njeri, 0, 1)  # today is always this week; approver: Achieng
		rows = fx.as_user(self.achieng_user, lm.away_rows, self.achieng_user)
		self.assertEqual([r.name for r in rows], [leave.name])
		self.assertIn("waiting for approval", rows[0].meta)

	def test_leave_the_viewer_may_not_read_is_left_out(self):
		# Kamau reads leave through a User Permission on his own Employee record, which Frappe
		# extends to the people below him unless it hides them.
		manager, report = self._newcomers()
		self._report(report, manager.employee)
		leave = fx.leave(report, 0, 1)
		# Frappe HR gives a new employee's user that permission itself; make it if this site does not.
		name = frappe.db.get_value("User Permission", {"user": manager.user, "allow": "Employee", "for_value": manager.employee})
		perm = frappe.get_doc("User Permission", name) if name else frappe.new_doc("User Permission")
		perm.update({"user": manager.user, "allow": "Employee", "for_value": manager.employee, "apply_to_all_doctypes": 1, "hide_descendants": 0})
		perm.save(ignore_permissions=True)
		self.addCleanup(frappe.cache.hdel, "user_permissions", manager.user)
		self.assertEqual([r.name for r in fx.as_user(manager.user, lm.away_rows, manager.user)], [leave.name])
		perm.hide_descendants = 1
		perm.save(ignore_permissions=True)
		rows = fx.as_user(manager.user, lm.away_rows, manager.user)
		self.assertEqual([r.name for r in rows], [None])
		self.assertEqual(rows[0].title, "Nobody away this week")

	def test_leave_outside_the_week_is_left_out(self):
		self._report(self.otieno, self.achieng)
		fx.leave(self.otieno, 14, 2)
		rows = fx.as_user(self.achieng_user, lm.away_rows, self.achieng_user)
		self.assertEqual([r.name for r in rows], [None])

	def test_no_team_no_rows(self):
		self.assertEqual(lm.away_rows(self.wanjiku_user), [])


class TestThePage(unittest.TestCase):
	"""The shipped file, and offering it once. Nothing is written to Desk Page here: on a shared
	site another process may hold its rows (the phone harness keeps one transaction open)."""

	PATH = os.path.join(os.path.dirname(lm.__file__), "desk_page", "line_manager", "line_manager.json")

	def test_the_shipped_page_carries_its_parts_and_no_audience(self):
		with open(self.PATH) as fh:
			page = json.load(fh)
		self.assertEqual(
			[i["widget"] for i in page["items"]],
			["seal-desk-approvals", "seal-hrms-team-away", "seal-hrms-cover", "seal-hrms-timesheet-work", "seal-hrms-time-off-work", "seal-desk-my-tasks"],
		)
		self.assertEqual((page["name"], page["status"], page["is_standard"], page["roles"], page["role_profiles"]), (lm.PAGE, "Draft", 1, [], []))
		widgets = os.path.join(os.path.dirname(lm.__file__), "desk_widget")
		shipped = {json.load(open(os.path.join(widgets, d, f"{d}.json")))["name"] for d in os.listdir(widgets)}
		self.assertLessEqual({w for w in (i["widget"] for i in page["items"]) if w.startswith("seal-hrms-")}, shipped)

	def _offer(self, page, offered=False):
		inserted = []
		exists = {("DocType", "Desk Page"): True, ("Desk Page", lm.PAGE): True}

		def fake_exists(doctype, filters=None, *a, **k):
			if doctype == "DefaultValue":
				return offered
			return exists.get((doctype, filters), False)

		def fake_get_doc(arg, *a, **k):
			if arg == "Desk Page":
				return page
			inserted.append(arg)
			return SimpleNamespace(insert=lambda **kw: None, db_insert=lambda: None)

		with patch.object(lm.frappe.db, "exists", side_effect=fake_exists), patch.object(lm.frappe, "get_doc", side_effect=fake_get_doc):
			lm.offer_page()
		return inserted

	def test_a_page_nobody_was_given_is_offered_to_the_role(self):
		inserted = self._offer(frappe._dict(roles=[], role_profiles=[], published_version=0))
		self.assertEqual([r["role"] for r in inserted if r["doctype"] == "Desk Page Role"], [lm.ROLE])
		self.assertEqual([r["defkey"] for r in inserted if r["doctype"] == "DefaultValue"], [lm.PAGE_OFFERED])

	def test_a_desk_managers_choice_is_left_alone(self):
		for page in (
			frappe._dict(roles=[frappe._dict(role="HR Manager")], role_profiles=[], published_version=0),
			frappe._dict(roles=[], role_profiles=[frappe._dict(role_profile="Supervisors")], published_version=0),
			frappe._dict(roles=[], role_profiles=[], published_version=2),
		):
			inserted = self._offer(page)
			self.assertEqual([r for r in inserted if r["doctype"] == "Desk Page Role"], [])

	def test_it_is_offered_only_once(self):
		self.assertEqual(self._offer(frappe._dict(roles=[], role_profiles=[], published_version=0), offered=True), [])


class TestTheListOnMyDesk(LineManagerTestCase):
	"""The adapter (desk/providers.py) turns the rows into seal_desk's ListRow, opening the leave."""

	def setUp(self):
		super().setUp()
		try:
			import seal_desk.role_center.schema  # noqa: F401
		except ImportError:
			self.skipTest("My Desk is not installed on this site")

	def test_rows_open_the_leave_application(self):
		from seal_hrms.desk.providers import team_away_rows

		self._report(self.otieno, self.achieng)
		leave = fx.leave(self.otieno, 0, 1)
		ctx = SimpleNamespace(user=self.achieng_user, today=frappe.utils.getdate(today()), company=None)
		rows = fx.as_user(self.achieng_user, team_away_rows, ctx)
		self.assertEqual(rows[0].target.route, ["Form", "Leave Application", leave.name])
		ctx.company = "_Test Company 1"  # the company chosen on My Desk (D143)
		rows = fx.as_user(self.achieng_user, team_away_rows, ctx)
		self.assertIsNone(rows[0].target)
