# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Compensatory leave requests in Self Service (seal_hrms/seal_hrms/compensatory_leave.py; my_desk api, approvals).

Baraka Mutua worked the Mashujaa Day clinic outreach (Tuesday 20 October 2026, a holiday on his
holiday list) and asks for a day off in return. Zawadi Njoroge is his leave approver and decides it;
Kiprop Chebet is a colleague with no part in it; Amina Hassan approves another team's leave
(`_phone_cast`). Pinned: the request is Baraka's own, through his Employee record (the days land in
his company's leave period, not his login's default company); nobody else on staff sees it; it is
assigned to Zawadi and waits in her Approvals only; she approves (Frappe HR adds the day) or rejects
with a reason; Amina, Kiprop and Baraka cannot decide it; a leave type banked as time off in lieu is
never offered nor accepted; a site Workflow makes all of this stand down.
"""

from unittest.mock import patch

import frappe

from seal_hrms.my_desk import api, approvals, links, push
from seal_hrms.seal_hrms import compensatory_leave as cl
from seal_hrms.tests._phone_cast import COMPANY, CastTestCase, as_user

LEAVE_TYPE = "Public Holiday Duty Off"
HOLIDAYS = "Mvua Health Holidays 2026"
MASHUJAA = "2026-10-20"
REASON = "Ran the Mashujaa Day immunisation outreach at Kibera clinic"


def _ensure_leave_period(company: str) -> None:
	if not frappe.db.exists("Leave Period", {"company": company, "is_active": 1, "from_date": ["<=", "2026-10-21"], "to_date": [">=", "2026-10-21"]}):
		doc = frappe.new_doc("Leave Period")
		doc.update({"from_date": "2026-01-01", "to_date": "2026-12-31", "company": company, "is_active": 1})
		doc.insert(ignore_permissions=True)


class CompensatoryTestCase(CastTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.exists("Leave Type", LEAVE_TYPE):
			doc = frappe.new_doc("Leave Type")
			doc.update({"leave_type_name": LEAVE_TYPE, "is_compensatory": 1, "max_leaves_allowed": 10})
			doc.insert(ignore_permissions=True)
		if not frappe.db.exists("Holiday List", HOLIDAYS):
			doc = frappe.new_doc("Holiday List")
			doc.update({"holiday_list_name": HOLIDAYS, "from_date": "2026-01-01", "to_date": "2026-12-31"})
			doc.append("holidays", {"holiday_date": MASHUJAA, "description": "Mashujaa Day"})
			doc.append("holidays", {"holiday_date": "2026-12-12", "description": "Jamhuri Day"})
			doc.insert(ignore_permissions=True)
		frappe.db.set_value("Employee", self.baraka, {"holiday_list": HOLIDAYS, "leave_approver": self.zawadi_user})
		frappe.db.set_value("Employee", self.kiprop, {"holiday_list": HOLIDAYS, "leave_approver": self.amina_user})
		for employee in (self.baraka, self.kiprop):
			frappe.clear_document_cache("Employee", employee)
			# Frappe HR 16.53 reads holiday lists from submitted assignments, not the Employee field.
			assignment = frappe.new_doc("Holiday List Assignment")
			assignment.update(
				{"applicable_for": "Employee", "assigned_to": employee, "holiday_list": HOLIDAYS, "from_date": "2026-01-01"}
			)
			assignment.insert(ignore_permissions=True)
			assignment.submit()
		_ensure_leave_period(COMPANY)
		for employee in (self.baraka, self.kiprop):
			attendance = frappe.new_doc("Attendance")
			attendance.update({"employee": employee, "attendance_date": MASHUJAA, "status": "Present", "company": COMPANY})
			attendance.insert(ignore_permissions=True)
			attendance.submit()
		# A workflow on the site, or a time off in lieu policy banking our type, is the site's: not here.
		self.no_workflow = patch.object(cl, "has_workflow", return_value=False)
		self.no_workflow.start()
		self.addCleanup(self.no_workflow.stop)

	def _request(self, user=None, leave_type=LEAVE_TYPE):
		return as_user(user or self.baraka_user, api.request_compensatory_leave, leave_type, MASHUJAA, MASHUJAA, REASON)

	def _decide(self, user, name, action, reason=None):
		return as_user(user, approvals.act_on_compensatory, name, action, reason)


class TestTheRequestIsBarakasOwn(CompensatoryTestCase):
	def test_request_is_his_and_goes_to_his_leave_approver(self):
		answer = self._request()
		doc = frappe.get_doc(cl.DOCTYPE, answer["name"])
		self.assertEqual((doc.employee, doc.leave_type, doc.docstatus), (self.baraka, LEAVE_TYPE, 0))
		self.assertEqual(answer["state"], cl.WAITING)
		self.assertEqual(cl.waiting_with(doc.name), [self.zawadi_user])

	def test_company_comes_from_the_employee_not_the_login(self):
		other = frappe.db.get_value("Company", {"name": ["!=", COMPANY]}, "name")
		if not other:
			self.skipTest("only one company on this site")
		frappe.defaults.set_user_default("company", other, self.baraka_user)
		self.addCleanup(frappe.defaults.clear_user_default, "company", self.baraka_user)
		name = self._request()["name"]
		self._decide(self.zawadi_user, name, approvals.APPROVE)
		allocation = frappe.db.get_value(cl.DOCTYPE, name, "leave_allocation")
		self.assertTrue(allocation)
		row = frappe.db.get_value("Leave Allocation", allocation, ["employee", "leave_type", "company"], as_dict=True)
		self.assertEqual((row.employee, row.leave_type, row.company), (self.baraka, LEAVE_TYPE, COMPANY))

	def test_the_form_says_who_will_approve(self):
		answer = as_user(self.baraka_user, api.compensatory_options)
		self.assertIn(LEAVE_TYPE, answer["leave_types"])
		self.assertEqual(answer["approver_name"], "Zawadi Njoroge")

	def test_a_time_off_in_lieu_type_is_never_offered_nor_taken(self):
		with patch("seal_hrms.seal_hrms.working_time.policy.toil_leave_types", return_value={LEAVE_TYPE}):
			self.assertNotIn(LEAVE_TYPE, as_user(self.baraka_user, api.compensatory_options)["leave_types"])
			with self.assertRaises(frappe.ValidationError):
				self._request()


class TestNobodyElseOnStaffSeesIt(CompensatoryTestCase):
	def test_two_people_see_only_their_own(self):
		mine = self._request()["name"]
		theirs = self._request(self.kiprop_user)["name"]
		self.assertEqual([r.name for r in as_user(self.baraka_user, api.compensatory_list)], [mine])
		self.assertEqual([r.name for r in as_user(self.kiprop_user, api.compensatory_list)], [theirs])
		with self.assertRaises(frappe.PermissionError):
			as_user(self.kiprop_user, api.compensatory_record, mine)
		with self.assertRaises(frappe.PermissionError):
			as_user(self.baraka_user, api.compensatory_record, theirs)

	def test_the_approver_opens_it_read_only(self):
		name = self._request()["name"]
		record = as_user(self.zawadi_user, api.compensatory_record, name)
		self.assertEqual((record["employee_name"], record["mine"], record["can_withdraw"]), ("Baraka Mutua", False, False))
		self.assertEqual(record["approver_name"], "Zawadi Njoroge")

	def test_only_he_withdraws_it(self):
		name = self._request()["name"]
		with self.assertRaises(frappe.PermissionError):
			as_user(self.kiprop_user, api.compensatory_action, name, "Withdraw")
		as_user(self.baraka_user, api.compensatory_action, name, "Withdraw")
		self.assertFalse(frappe.db.exists(cl.DOCTYPE, name))
		self.assertEqual(approvals.compensatory_items(self.zawadi_user), [])


class TestTheApprovalSource(CompensatoryTestCase):
	def test_it_waits_for_zawadi_only(self):
		name = self._request()["name"]
		items = approvals.compensatory_items(self.zawadi_user)
		self.assertEqual([(i.doctype, i.name, i.on_behalf_of) for i in items], [(cl.DOCTYPE, name, None)])
		self.assertEqual([a.key for a in items[0].actions], [approvals.APPROVE, approvals.REJECT])
		self.assertTrue(items[0].actions[1].needs_reason)
		for user in (self.amina_user, self.kiprop_user, self.baraka_user):
			self.assertEqual(approvals.compensatory_items(user), [], user)

	def test_nobody_else_decides_it(self):
		name = self._request()["name"]
		for user in (self.amina_user, self.baraka_user):
			with self.assertRaises(frappe.PermissionError):
				self._decide(user, name, approvals.APPROVE)
		self.assertEqual(frappe.db.get_value(cl.DOCTYPE, name, "docstatus"), 0)

	def test_hr_decides_on_the_desk_not_from_the_inbox(self):
		# Amina may submit any request as HR User, but the inbox is for the approver or their stand-in (P4-13).
		frappe.get_doc("User", self.amina_user).add_roles("HR User")
		# HR reads every employee's records: without Frappe HR's own-Employee User Permission (P4 finding).
		for row in frappe.get_all("User Permission", filters={"user": self.amina_user, "allow": "Employee"}, pluck="name"):
			frappe.delete_doc("User Permission", row, ignore_permissions=True)
		frappe.clear_cache(user=self.amina_user)
		name = self._request()["name"]
		self.assertEqual(as_user(self.amina_user, api.compensatory_record, name)["employee_name"], "Baraka Mutua")
		with self.assertRaises(frappe.PermissionError):
			self._decide(self.amina_user, name, approvals.APPROVE)
		self.assertEqual(frappe.db.get_value(cl.DOCTYPE, name, "docstatus"), 0)

	def test_approving_adds_the_day(self):
		name = self._request()["name"]
		self._decide(self.zawadi_user, name, approvals.APPROVE)
		doc = frappe.get_doc(cl.DOCTYPE, name)
		self.assertEqual((doc.docstatus, cl.state_of(doc)), (1, cl.APPROVED))
		self.assertEqual(cl.waiting_with(name), [])
		self.assertEqual(approvals.compensatory_items(self.zawadi_user), [])
		self.assertEqual(frappe.db.get_value("Leave Allocation", doc.leave_allocation, "new_leaves_allocated"), 1)

	def test_rejecting_needs_a_reason_and_tells_baraka(self):
		name = self._request()["name"]
		with self.assertRaises(frappe.ValidationError):
			self._decide(self.zawadi_user, name, approvals.REJECT)
		self._decide(self.zawadi_user, name, approvals.REJECT, "The outreach was covered by the county team that day")
		doc = frappe.get_doc(cl.DOCTYPE, name)
		self.assertEqual((doc.docstatus, cl.state_of(doc)), (0, cl.REJECTED))
		self.assertEqual(approvals.compensatory_items(self.zawadi_user), [])
		record = as_user(self.baraka_user, api.compensatory_record, name)
		self.assertEqual(record["note"], "The outreach was covered by the county team that day")
		self.assertTrue(frappe.db.exists("Notification Log", {"for_user": self.baraka_user, "document_type": cl.DOCTYPE, "document_name": name}))
		with self.assertRaises(frappe.ValidationError):
			self._decide(self.zawadi_user, name, approvals.APPROVE)

	def test_a_site_workflow_makes_it_stand_down(self):
		with patch.object(cl, "has_workflow", return_value=True):
			name = self._request()["name"]
			self.assertEqual(cl.waiting_with(name), [])
			self.assertEqual(approvals.compensatory_items(self.zawadi_user), [])
			with self.assertRaises(frappe.ValidationError):
				self._decide(self.zawadi_user, name, approvals.APPROVE)

	def test_declared_as_a_source(self):
		from seal_hrms import hooks

		source = next(s for s in hooks.seal_desk_approval_sources if s["key"] == "seal_hrms.compensatory_leave")
		self.assertEqual(source["doctypes"], [cl.DOCTYPE])
		self.assertIs(frappe.get_attr(source["act"]), approvals.act_on_compensatory)
		self.assertIn(approvals.act_on_compensatory, frappe.whitelisted)
		self.assertIn(cl.DOCTYPE, hooks.seal_desk_app_sections[0]["claims"])


class TestNoticesAndLinks(CompensatoryTestCase):
	def test_waiting_for_zawadi_is_an_approval_then_hr(self):
		name = self._request()["name"]
		self.assertTrue(push.waiting_for(self.zawadi_user, cl.DOCTYPE, name))
		self.assertFalse(push.waiting_for(self.amina_user, cl.DOCTYPE, name))
		self.assertFalse(push.waiting_for(self.baraka_user, cl.DOCTYPE, name))
		log = frappe._dict(document_type=cl.DOCTYPE, document_name=name, for_user=self.zawadi_user)
		self.assertIsNone(push.kind_of(log))
		self._decide(self.zawadi_user, name, approvals.APPROVE)
		self.assertEqual(push.kind_of(log), push.HR)
		self.assertEqual(push.kind_of(frappe._dict(log, for_user=self.baraka_user)), push.HR)

	def test_frappe_hrs_new_link_opens_the_form(self):
		self.assertEqual(links.target("compensatory-leave-requests/new", True), f"{links.MY_HR}/compensatory-leave/new")
		self.assertEqual(links.target("compensatory-leave-requests", True), f"{links.MY_DESK}/l/Compensatory%20Leave%20Request")
