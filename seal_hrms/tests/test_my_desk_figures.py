# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Balances, cover and headlines on My Desk (seal_hrms/my_desk/figures.py, HR_ON_MY_DESK.md §2.3–§2.5).

Otieno banks extra hours at the Kilimani office and has annual leave; Njeri is in no
banking grade. Each figure is the person's own, a line appears only when true, and
the shipped Desk Widget records and page name only groups this app declares.
"""

import json
import pathlib
from unittest.mock import patch

import frappe
from frappe.utils import add_days, getdate, today

from seal_hrms.my_desk import figures
from seal_hrms.seal_hrms import acting
from seal_hrms.seal_hrms.timesheets import approval as ts_approval
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests.test_my_desk_approvals import ApprovalsTestCase
from seal_hrms.tests.test_timesheet_approval import ACTIVITY_TYPE

ANNUAL = "Kilimani Annual Leave"


def _keys(rows):
	return [r.key for r in rows]


class TestBalances(ApprovalsTestCase):
	def _annual_allocation(self, days=21):
		if not frappe.db.exists("Leave Type", ANNUAL):
			lt = frappe.new_doc("Leave Type")
			lt.leave_type_name = ANNUAL
			lt.max_leaves_allowed = 30
			lt.insert(ignore_permissions=True)
		alloc = frappe.new_doc("Leave Allocation")
		alloc.employee = self.otieno
		alloc.leave_type = ANNUAL
		alloc.from_date = add_days(today(), -30)
		alloc.to_date = add_days(today(), 300)
		alloc.new_leaves_allocated = days
		alloc.insert(ignore_permissions=True)
		alloc.submit()
		return alloc

	def test_leave_left_per_type_for_the_person_only(self):
		self._annual_allocation(21)
		mine = {r.key: r for r in figures.balances(self.otieno_user)}
		self.assertEqual(mine[f"leave_left:{ANNUAL}"].value, 21)
		self.assertEqual(mine[f"leave_left:{ANNUAL}"].target.filters, {"employee": self.otieno})
		self.assertNotIn(f"leave_left:{tf.LEAVE_TYPE}", mine, "time off in lieu has its own figure")
		self.assertNotIn(f"leave_left:{ANNUAL}", _keys(figures.balances(self.njeri_user)))

	def test_time_off_left_and_lapsing_for_a_banking_grade(self):
		tf.policy(validity_days=20)
		self._approved([(tf.working_day(), 8)])
		mine = {r.key: r for r in figures.balances(self.otieno_user)}
		self.assertGreater(mine["toil_left"].value, 0)
		self.assertGreater(mine["toil_lapsing"].value, 0)
		self.assertNotIn("toil_left", _keys(figures.balances(self.njeri_user)), "Njeri's grade is paid, not banked")

	def test_a_figure_on_a_record_they_cannot_read_is_left_out(self):
		self._approved([(tf.working_day(), 8)])
		self.assertEqual(figures.balances(self.otieno_user, readable={"Leave Application"}), [])

	def test_nobody_without_an_employee_record_gets_figures(self):
		self.assertEqual(figures.balances("Administrator"), [])


class TestCover(ApprovalsTestCase):
	def _covered_by_njeri(self):
		la = fx.leave(self.otieno, 0, 3)
		ta = fx.handover(self.otieno, self.njeri, la, rows=[])
		return fx.take_effect(ta, la, "njeri")

	def test_each_side_sees_its_own_line(self):
		ta = self._covered_by_njeri()
		self.assertEqual(ta.status, "Active")
		otieno = [r.title for r in figures.cover(self.otieno_user)]
		njeri = [r.title for r in figures.cover(self.njeri_user)]
		self.assertTrue(any("is covering your work" in t and "Njeri" in t for t in otieno), otieno)
		self.assertTrue(any(t.startswith("You are covering Otieno") for t in njeri), njeri)
		self.assertEqual([r.title for r in figures.cover(self.achieng_user)], [])

	def test_approving_for_someone_is_a_line(self):
		ta = self._covered_by_njeri()
		row = frappe._dict(principal=self.achieng_user, stand_in=self.njeri_user, authority="leave_approval", assignment=ta.name, row="r1")
		with patch.object(acting, "acting_for", side_effect=lambda user: [row] if user == self.njeri_user else []):
			titles = [r.title for r in figures.cover(self.njeri_user)]
		self.assertTrue(any(t.startswith("You approve for Achieng") for t in titles), titles)


class TestHeadlines(ApprovalsTestCase):
	def test_none_when_nothing_is_true(self):
		self.assertEqual(figures.headlines(self.njeri_user), [])

	def test_approving_for_someone(self):
		row = frappe._dict(principal=self.achieng_user, stand_in=self.njeri_user, authority="leave_approval", assignment="TA-NONE", row="r1")
		with patch.object(acting, "acting_for", side_effect=lambda user: [row] if user == self.njeri_user else []):
			lines = figures.headlines(self.njeri_user)
		self.assertEqual(len(lines), 1)
		self.assertIn("approving for Achieng", lines[0].text)

	def test_time_off_lapsing_within_two_weeks(self):
		tf.policy(validity_days=10)
		self._approved([(tf.working_day(), 8)])
		lines = figures.headlines(self.otieno_user)
		self.assertTrue(any("lapse" in line.text for line in lines), [line.text for line in lines])

	def test_time_off_lapsing_later_is_not_a_headline(self):
		tf.policy(validity_days=80)
		self._approved([(tf.working_day(), 8)])
		self.assertFalse(any("lapse" in line.text for line in figures.headlines(self.otieno_user)))

	def test_last_weeks_timesheet_not_sent(self):
		tf.policy(weekly_timesheets=1, timesheet_approval=1)
		lines = [line.text for line in figures.headlines(self.otieno_user)]
		self.assertTrue(any("timesheet" in t for t in lines), lines)
		# Once sent, the line goes.
		if not frappe.db.exists("Activity Type", ACTIVITY_TYPE):
			frappe.get_doc({"doctype": "Activity Type", "activity_type": ACTIVITY_TYPE}).insert(ignore_permissions=True)
		monday = add_days(getdate(today()), -getdate(today()).weekday() - 7)
		ts = frappe.new_doc("Timesheet")
		ts.company = tf.COMPANY
		ts.employee = self.otieno
		ts.append("time_logs", {"activity_type": ACTIVITY_TYPE, "from_time": f"{monday} 08:00:00", "to_time": f"{monday} 16:00:00", "hours": 8, "description": "Clinic records in Kawangware"})
		with patch("seal_hrms.seal_hrms.timesheets.week.is_weekly", return_value=False), patch("seal_hrms.seal_hrms.timesheets.effort.check_before_sending"):
			fx.as_user(self.otieno_user, ts.insert)
			fx.as_user(self.otieno_user, ts_approval.send_for_approval, ts.name)
		self.assertFalse(any("timesheet" in line.text for line in figures.headlines(self.otieno_user)))

	def test_no_timesheet_line_without_weekly_timesheets(self):
		tf.policy(weekly_timesheets=0, timesheet_approval=1)
		self.assertFalse(any("timesheet" in line.text for line in figures.headlines(self.otieno_user)))


class TestShippedRecords(ApprovalsTestCase):
	"""The Desk Widget records and the page name only groups this app declares."""

	ROOT = pathlib.Path(frappe.get_app_path("seal_hrms", "seal_hrms"))

	def test_widgets_name_declared_groups(self):
		declared = {g["key"] for g in frappe.get_hooks("seal_desk_cue_groups", app_name="seal_hrms")}
		widgets = {}
		for path in (self.ROOT / "desk_widget").glob("*/*.json"):
			data = json.loads(path.read_text())
			widgets[data["name"]] = data
			self.assertIn(data["standard_group"], declared, path.name)
			self.assertEqual(data["name"].replace("-", "_"), path.stem)
		for name in ("seal-hrms-time-off-work", "seal-hrms-timesheet-work", "seal-hrms-cover", "seal-hrms-balances", "seal-hrms-hr-work"):
			self.assertIn(name, widgets)

	def test_the_page_carries_the_new_parts_and_actions(self):
		page = json.loads((self.ROOT / "desk_page" / "employee_self_service" / "employee_self_service.json").read_text())
		widgets = [i["widget"] for i in page["items"]]
		for name in ("seal-hrms-balances", "seal-hrms-time-off-work", "seal-hrms-timesheet-work", "seal-hrms-cover"):
			self.assertIn(name, widgets)
		new = {a["target"] for a in page["actions"] if a["area"] == "New"}
		self.assertTrue({"Time Off in Lieu Claim", "Payout Change Request"} <= new)
		self.assertEqual(len(page["checklist"]), 3)
		for step in page["checklist"]:
			self.assertLessEqual(len(step["short_title"]), 34)
			self.assertLessEqual(len(step["title"]), 53)
			self.assertLessEqual(len(step.get("description") or ""), 180)
