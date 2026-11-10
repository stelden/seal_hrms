# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""The My HR section's backend (seal_hrms/my_desk/api.py, section.py; MY_DESK_P5_PLAN.md).

Otieno Ochieng is a programme officer at the test company; Njeri Mwangi a colleague; Achieng
Odhiambo approves leave. Pinned: every list and record is the person's own (Njeri never sees
Otieno's); every record the phone creates takes the employee's company and approvers, never
the creator's default company; payout details are read masked; check-in follows HR's switch;
leave with a required handover cannot go without a stand-in, and goes to the stand-in with it.

Rows are created and rolled back per test (ToilTestCase); no SMS or email leaves the process.
"""

import json
from unittest.mock import patch

import frappe
from frappe.utils import add_days, today

from seal_hrms.my_desk import api, section
from seal_hrms.seal_hrms import payout_change as pc
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests import _toil_fixtures as tf
from seal_hrms.tests._borrowed_doctype import borrow
from seal_hrms.tests.test_timesheet_approval import ACTIVITY_TYPE
from seal_hrms.tests.test_toil_claim import ToilTestCase

APP = "seal_hrms"
POLICY = "Task Assignment Policy"


class SectionTestCase(ToilTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		borrow(pc.DOCTYPE, frappe.get_app_path(APP, "seal_hrms", "doctype", "payout_change_request", "payout_change_request.json"), cls)
		cls.company = frappe.db.get_value("Employee", cls.otieno, "company")
		# Another company is Otieno's default: a record that took the default would fail his User Permission.
		cls.other_company = frappe.db.get_value("Company", {"name": ["!=", cls.company]}, "name")

	def setUp(self):
		super().setUp()
		self.mail = []
		for target in ("frappe.sendmail", "frappe.enqueue"):
			p = patch(target, side_effect=lambda *a, **k: self.mail.append(k))
			p.start()
			self.addCleanup(p.stop)
		if self.other_company:
			# As on a group of companies: Otieno may open only his own company's records, and his
			# login's default company is another one. A record that took the default is refused.
			if not frappe.db.exists("User Permission", {"user": self.otieno_user, "allow": "Company", "for_value": self.company}):
				frappe.get_doc({"doctype": "User Permission", "user": self.otieno_user, "allow": "Company", "for_value": self.company, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
			frappe.defaults.set_user_default("company", self.other_company, self.otieno_user)
			self.addCleanup(frappe.defaults.clear_user_default, "company", self.otieno_user)
			self.addCleanup(frappe.clear_cache, user=self.otieno_user)

	def as_otieno(self, fn, *args, **kwargs):
		return fx.as_user(self.otieno_user, fn, *args, **kwargs)

	def as_njeri(self, fn, *args, **kwargs):
		return fx.as_user(self.njeri_user, fn, *args, **kwargs)


class TestTheHookEntry(SectionTestCase):
	def test_one_section_declared_with_the_contract_keys(self):
		entries = frappe.get_hooks("seal_desk_app_sections", app_name=APP)
		self.assertEqual(len(entries), 1)
		entry = entries[0]
		self.assertEqual(entry["key"], "seal_hrms.my_hr")
		self.assertTrue(entry["module"].startswith("/assets/seal_hrms/my-desk/") and entry["module"].endswith(".js"))
		self.assertTrue(entry["css"].startswith("/assets/seal_hrms/my-desk/") and entry["css"].endswith(".css"))
		self.assertIs(frappe.get_attr(entry["visible"]), section.visible)
		for doctype in entry["claims"]:
			with self.subTest(doctype=doctype):
				self.assertTrue(frappe.db.exists("DocType", doctype), f"{doctype} is not a DocType here")

	def test_the_built_bundle_is_where_the_entry_points(self):
		entry = frappe.get_hooks("seal_desk_app_sections", app_name=APP)[0]
		public = frappe.get_app_path(APP, "public")
		for url in (entry["module"], entry["css"], entry["module"].rsplit("/", 1)[0] + "/section.json"):
			path = url.replace("/assets/seal_hrms", public)
			with self.subTest(url=url):
				with open(path) as handle:
					self.assertTrue(handle.read(1), f"{url} is empty")
		with open(frappe.get_app_path(APP, "public", "my-desk", "section.json")) as handle:
			self.assertEqual(json.load(handle)["kind"], "section")

	def test_visible_to_staff_only(self):
		self.assertTrue(section.visible(self.otieno_user))
		self.assertFalse(section.visible("Guest"))
		self.assertFalse(section.visible("Administrator"))  # no Employee record of their own


class TestOwnRecordsOnly(SectionTestCase):
	def test_lists_hold_only_the_persons_own(self):
		claim = self.as_otieno(api.claim_expenses, [{"expense_type": self._expense_type(), "amount": 1850, "description": "Matatu fares to Kibera clinic"}])
		advance = self.as_otieno(api.request_advance, "Field visit to Garissa sub-county", 12000)
		self.assertIn(claim, [r.name for r in self.as_otieno(api.expense_list)])
		self.assertIn(advance, [r.name for r in self.as_otieno(api.advance_list)])
		self.assertNotIn(claim, [r.name for r in self.as_njeri(api.expense_list)])
		self.assertNotIn(advance, [r.name for r in self.as_njeri(api.advance_list)])

	def test_another_persons_record_is_refused(self):
		claim = self.as_otieno(api.claim_expenses, [{"expense_type": self._expense_type(), "amount": 640, "description": "Airtime for the Mathare outreach line"}])
		with self.assertRaises(frappe.PermissionError):
			self.as_njeri(api.expense_record, claim)
		self.assertEqual(self.as_otieno(api.expense_record, claim)["total_claimed_amount"], 640)

	def test_someone_with_no_staff_record_is_told_so(self):
		with self.assertRaises(frappe.PermissionError):
			fx.as_user("Administrator", api.home)

	def test_home_answers_for_the_person(self):
		answer = self.as_otieno(api.home)
		self.assertEqual(answer["employee"]["name"], self.otieno)
		self.assertIn("offered", answer["checkin"])

	def _expense_type(self):
		name = "Local Travel"
		if not frappe.db.exists("Expense Claim Type", name):
			doc = frappe.new_doc("Expense Claim Type")
			doc.expense_type = name
			doc.append("accounts", {"company": self.company, "default_account": frappe.db.get_value("Account", {"company": self.company, "is_group": 0, "root_type": "Expense"}, "name")})
			doc.insert(ignore_permissions=True)
		return name


class TestCompanyComesFromTheEmployee(SectionTestCase):
	def test_every_create_takes_the_employees_company(self):
		advance = self.as_otieno(api.request_advance, "Training in Nakuru", 8000)
		request = self.as_otieno(api.request_attendance, tf.working_day(), tf.working_day(), "On Duty", "Community health drive in Kibera")
		claim = self.as_otieno(api.save_toil_claim, [{"work_date": tf.working_day(), "hours": 3, "work_done": "Evening session with Kibera youth group"}])
		payout = self.as_otieno(api.request_payout_change, "Mobile Money", mobile_no="0712 345 678", reason="New Safaricom line")
		for doctype, name in (("Employee Advance", advance), ("Attendance Request", request), ("Time Off in Lieu Claim", claim), (pc.DOCTYPE, payout)):
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.db.get_value(doctype, name, ["employee", "company"]), (self.otieno, self.company))

	def test_leave_takes_company_and_approver(self):
		answer = self.as_otieno(api.apply_for_leave, fx.ensure_leave_type(), add_days(today(), 30), add_days(today(), 31), "Family matters upcountry in Nyeri")
		row = frappe.db.get_value("Leave Application", answer["name"], ["employee", "company", "leave_approver", "status", "docstatus"], as_dict=True)
		self.assertEqual((row.employee, row.company, row.leave_approver, row.status, row.docstatus), (self.otieno, self.company, self.achieng_user, "Open", 0))

	def test_a_claim_cannot_be_changed_by_someone_else(self):
		claim = self.as_otieno(api.save_toil_claim, [{"work_date": tf.working_day(), "hours": 2, "work_done": "Weekend stock count at the Ngong Road store"}])
		with self.assertRaises(frappe.PermissionError):
			self.as_njeri(api.save_toil_claim, [{"work_date": tf.working_day(), "hours": 9, "work_done": "x"}], None, claim)
		with self.assertRaises(frappe.PermissionError):
			self.as_njeri(api.toil_action, claim, "Send for Approval")

	def test_a_claim_is_sent_through_its_workflow(self):
		claim = self.as_otieno(api.save_toil_claim, [{"work_date": tf.working_day(), "hours": 3, "work_done": "Evening session with Kibera youth group"}])
		record = self.as_otieno(api.toil_record, claim)
		self.assertTrue(record["can_edit"])
		self.assertTrue(record["stage"]["items"] and "<" not in record["stage"]["items"][0]["text"])
		self.assertEqual(self.as_otieno(api.toil_action, claim, record["actions"][0]), "Waiting for Approval")
		with self.assertRaises(frappe.ValidationError):
			self.as_otieno(api.toil_action, claim, "Approve")


class TestLeaveWithAHandover(SectionTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.delete(POLICY, {"company": self.company})
		policy = frappe.new_doc(POLICY)
		policy.update({"company": self.company, "requirement": "Require on Approval", "min_days": 0})
		policy.insert(ignore_permissions=True)

	def test_no_stand_in_is_refused_where_cover_is_required(self):
		options = self.as_otieno(api.leave_options, fx.ensure_leave_type(), add_days(today(), 40), add_days(today(), 44))
		self.assertTrue(options["handover"]["needed"] and options["handover"]["required"])
		with self.assertRaises(frappe.ValidationError):
			self.as_otieno(api.apply_for_leave, fx.ensure_leave_type(), add_days(today(), 40), add_days(today(), 44))

	def test_the_handover_goes_to_the_stand_in_with_the_leave(self):
		answer = self.as_otieno(
			api.apply_for_leave,
			fx.ensure_leave_type(),
			add_days(today(), 40),
			add_days(today(), 44),
			"Burial in Siaya",
			0,
			self.njeri,
			"Call the Kisumu partners on Tuesday.",
			[],
			[],
		)
		ta = frappe.get_doc("Task Assignment", answer["handover"])
		self.assertEqual((ta.leave_application, ta.task_assignee, ta.docstatus, ta.status), (answer["name"], self.njeri, 1, "Awaiting Acceptance"))
		waiting = self.as_njeri(api.cover)["to_answer"]
		self.assertIn(ta.name, [r["name"] for r in waiting])
		self.assertTrue(self.as_njeri(api.handover_record, ta.name)["can_answer"])
		self.assertTrue(self.as_otieno(api.handover_record, ta.name)["is_owner"])


class TestPayoutDetailsAreMasked(SectionTestCase):
	ACCOUNT = "01109384756200"

	def setUp(self):
		super().setUp()
		bank = "Kilimani Cooperative Bank"
		if not frappe.db.exists("Bank", bank):
			frappe.get_doc({"doctype": "Bank", "bank_name": bank}).insert(ignore_permissions=True)
		account = frappe.new_doc("Bank Account")
		account.update({"account_name": "Otieno Ochieng", "bank": bank, "bank_account_no": self.ACCOUNT, "party_type": "Employee", "party": self.otieno, "is_default": 1})
		account.insert(ignore_permissions=True)
		frappe.db.set_value("Employee", self.otieno, "custom_salary_bank_account", account.name)

	def test_no_full_number_is_ever_read(self):
		answer = self.as_otieno(api.my_details)
		text = json.dumps(answer, default=str)
		self.assertNotIn(self.ACCOUNT, text)
		self.assertNotIn(fx.PHONES["otieno"], text)
		self.assertEqual(answer["payout"]["account_no"], "•••• 6200")
		self.assertEqual(answer["payout"]["bank"], "Kilimani Cooperative Bank")

	def test_a_request_reads_masked_and_only_by_its_owner(self):
		name = self.as_otieno(api.request_payout_change, "Bank Account", bank="Kilimani Cooperative Bank", bank_account_no="01109384756311", account_name="Otieno Ochieng")
		record = self.as_otieno(api.payout_request_record, name)
		self.assertEqual(record["account_no"], "•••• 6311")
		self.assertNotIn("01109384756311", json.dumps(record, default=str))
		with self.assertRaises(frappe.PermissionError):
			self.as_njeri(api.payout_request_record, name)
		with self.assertRaises(frappe.PermissionError):
			self.as_njeri(api.set_payout_evidence, name, "/private/files/otieno-bank-letter.pdf")

	def test_mask(self):
		self.assertEqual(api.mask("0712 345 678"), "•••• 5678")
		self.assertEqual(api.mask("123"), "•••")
		self.assertIsNone(api.mask(None))


class TestCheckIn(SectionTestCase):
	def _settings(self, offered, location):
		frappe.db.set_single_value("HR Settings", {"allow_employee_checkin_from_mobile_app": offered, "allow_geolocation_tracking": location})

	def test_check_in_is_the_persons_own_with_location_when_asked(self):
		self._settings(1, 1)
		answer = self.as_otieno(api.check_in, "IN", -1.2921, 36.8219)
		row = frappe.db.get_value("Employee Checkin", answer["name"], ["employee", "log_type", "latitude"], as_dict=True)
		self.assertEqual((row.employee, row.log_type, round(row.latitude, 4)), (self.otieno, "IN", -1.2921))
		self.assertEqual(self.as_otieno(api.checkin_status)["next"], "OUT")
		self.assertEqual(self.as_njeri(api.checkin_status)["today"], [])

	def test_no_location_kept_when_hr_does_not_ask(self):
		self._settings(1, 0)
		answer = self.as_otieno(api.check_in, "IN", -1.2921, 36.8219)
		self.assertFalse(frappe.db.get_value("Employee Checkin", answer["name"], "latitude"))

	def test_refused_when_hr_has_it_off(self):
		self._settings(0, 0)
		with self.assertRaises(frappe.ValidationError):
			self.as_otieno(api.check_in, "IN")


class TestTimesheetWeek(SectionTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.exists("Activity Type", ACTIVITY_TYPE):
			frappe.get_doc({"doctype": "Activity Type", "activity_type": ACTIVITY_TYPE}).insert(ignore_permissions=True)
		tf.policy(weekly_timesheets=1, timesheet_approval=1, default_activity_type=ACTIVITY_TYPE)
		self.monday = str(frappe.utils.getdate(add_days(tf.working_day(), -7)) - frappe.utils.datetime.timedelta(days=frappe.utils.getdate(add_days(tf.working_day(), -7)).weekday()))

	def test_the_week_is_saved_for_the_person_and_sent(self):
		entries = [{"row": 1, "activity_type": ACTIVITY_TYPE, "description": "Household visits in Mathare North", "hours": [8, 8, 0, 0, 0, 0, 0]}]
		answer = self.as_otieno(api.save_timesheet_week, self.monday, entries, 1)
		doc = frappe.get_doc("Timesheet", answer["name"])
		self.assertEqual((doc.employee, doc.company, doc.custom_approval_state), (self.otieno, self.company, "Waiting for Approval"))
		self.assertEqual(self.as_otieno(api.timesheet_week, self.monday)["timesheet"]["name"], doc.name)
		self.assertNotIn(doc.name, [r.name for r in self.as_njeri(api.timesheets)["timesheets"]])
		with self.assertRaises(frappe.ValidationError):
			self.as_otieno(api.save_timesheet_week, self.monday, entries)


class TestPayslipFormat(SectionTestCase):
	def test_the_clients_default_print_format_else_standard(self):
		with patch.object(frappe.get_meta("Salary Slip"), "default_print_format", None):
			self.assertEqual(api.payslip_print_format(), "Standard")
		name = frappe.db.get_value("Print Format", {"doc_type": "Salary Slip", "disabled": 0}, "name")
		if not name:
			self.skipTest("no enabled Salary Slip print format on this site")
		with patch.object(frappe.get_meta("Salary Slip"), "default_print_format", name):
			self.assertEqual(api.payslip_print_format(), name)


class TestSelfServiceUserType(SectionTestCase):
	def test_the_section_doctypes_are_listed_with_their_rights(self):
		from seal_hrms.seal_hrms.working_time import user_type

		if not frappe.db.exists("User Type", user_type.USER_TYPE):
			self.skipTest("this site has no Self Service user type")
		frappe.db.set_value("User Document Type", {"parent": user_type.USER_TYPE, "document_type": "Employee Checkin"}, "create", 0)
		user_type.allow_claims_for_self_service()
		for doctype, perms in user_type.DOCTYPES.items():
			if not frappe.db.exists("DocType", doctype) or (doctype == pc.DOCTYPE and not frappe.db.exists("DocType", doctype, cache=False)):
				continue
			row = frappe.db.get_value("User Document Type", {"parent": user_type.USER_TYPE, "document_type": doctype}, list(perms), as_dict=True)
			with self.subTest(doctype=doctype):
				self.assertIsNotNone(row)
				self.assertTrue(all(row.get(p) for p in perms), row)
