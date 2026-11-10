# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""What Otieno's week on the phone needs on dev.local, made inside the harness's one transaction.

Nothing here is committed (``harness.py``): the borrowed schema, the people's sign-in details,
the company's rules, the payslip and everything the walk creates vanish when the harness stops.
Records are made through the ORM (SEAL_DEV_RULES §1.9).

People (seal_hrms' own test people, ``tests/_handover_fixtures.py``): **Otieno Ochieng**, a
programme officer at the Kilimani office, does his week of self service; **Achieng Odhiambo**
approves his leave, time off, timesheets and expense claims; **Njeri Mwangi**, a colleague,
covers his work while he is away. Each gets a mobile number and a password for this run, so
password-then-code sign-in works.

The schema dev.local lacks until Keith migrates is borrowed (seal_desk P3's ``seed_desk.py``,
copied here unchanged, plus seal_hrms' Payout Change Request).
"""

import os

import frappe
from frappe.utils import add_days, add_months, get_first_day, get_last_day, getdate, today
from frappe.utils.password import update_password

import seed_desk

HERE = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "Kibera-Walk#2026"
EXPENSE_TYPE = "Kilimani Field Travel"
ACTIVITY = "Community Outreach"
COMPONENT = "Kilimani Basic Pay"
STRUCTURE = "Kilimani Programme Staff 2026"

#: Read by the suite through /__harness/seeded.
SEEDED: dict = {}


def borrow_schema() -> set[str]:
	"""seal_common P2's sign-in and push DocTypes, seal_desk P3's new column, seal_hrms' Payout Change Request."""
	from seal_common.seal_common.tests.borrowed_doctypes import borrow_doctype
	from seal_common.seal_common.tests.passkey_fixtures import install_login_passkey
	from seal_common.seal_common.tests.push_fixtures import install_push_doctypes

	made = set()
	if install_login_passkey():
		made.add("tabLogin Passkey")
	if install_push_doctypes():
		made |= {"tabPush Private Document Type", "tabPush Subscription"}
	seed_desk._teach_options("OTP Log", "purpose", frappe.get_app_path("seal_common", "otp", "doctype", "otp_log", "otp_log.json"))
	made |= seed_desk.shadow_with_new_columns(
		"Desk Page Item", frappe.get_app_path("seal_desk", "seal_desk", "doctype", "desk_page_item", "desk_page_item.json")
	)
	path = frappe.get_app_path("seal_hrms", "seal_hrms", "doctype", "payout_change_request", "payout_change_request.json")
	if borrow_doctype(path):
		made.add("tabPayout Change Request")
	return made


# --- people -------------------------------------------------------------------------------


def _sign_in_details(user: str, mobile: str) -> None:
	doc = frappe.get_doc("User", user)
	doc.user_type = "System User"
	doc.mobile_no = mobile
	doc.save(ignore_permissions=True)
	update_password(user, PASSWORD)


def _people() -> dict:
	from seal_hrms.tests import _handover_fixtures as fx
	from seal_hrms.tests import _toil_fixtures as tf

	tf.ensure_leave_period()
	otieno = tf.set_up_otieno()  # his grade banks hours; Achieng approves his leave; his own calendar
	njeri = fx.ensure_employee("njeri")
	achieng = fx.approver()
	frappe.get_doc("User", achieng).add_roles("Leave Approver", "Expense Approver")
	frappe.db.set_value("Employee", otieno, {"expense_approver": achieng, "cell_number": fx.PHONES["otieno"]})
	for key, mobile in (("otieno", "0733902614"), ("achieng", "0745130968"), ("njeri", "0711560287")):
		_sign_in_details(fx.email(key), mobile)
	return {"otieno": otieno, "njeri": njeri, "otieno_user": fx.email("otieno"), "achieng_user": achieng, "njeri_user": fx.email("njeri")}


# --- the company's rules --------------------------------------------------------------------


def _rules(company: str) -> None:
	from seal_hrms.tests import _toil_fixtures as tf

	if not frappe.db.exists("Activity Type", ACTIVITY):
		frappe.new_doc("Activity Type").update({"activity_type": ACTIVITY}).insert(ignore_permissions=True)
	# Time off in lieu, approved timesheets kept by the week, the claim window wide enough for last week.
	tf.policy(timesheet_approval=1, weekly_timesheets=1, default_activity_type=ACTIVITY, claim_within_days=30, evidence_attendance=0, evidence_timesheets=0)
	# Cover is suggested for leave of a day or more (the handover step shows; a stand-in is optional).
	if frappe.db.exists("Task Assignment Policy", company):
		policy = frappe.get_doc("Task Assignment Policy", company)
	else:
		policy = frappe.new_doc("Task Assignment Policy")
		policy.company = company
	policy.update({"requirement": "Warn", "min_days": 1})
	policy.set("leave_types", [])
	policy.save(ignore_permissions=True)
	frappe.db.set_single_value("HR Settings", "allow_employee_checkin_from_mobile_app", 1)
	# dev.local's own Property Setters (no module: a site's, not an app's) put the claim's payable
	# account at permission level 1, so a claim staff make has none and its approval is refused
	# ("Account is required"), on the desk as on the phone. A site artefact (HANDOVER finding); for
	# this run only, the field is as Frappe HR ships it.
	for name in frappe.get_all("Property Setter", filters={"doc_type": "Expense Claim", "field_name": "payable_account", "property": "permlevel", "module": ["is", "not set"]}, pluck="name"):
		frappe.delete_doc("Property Setter", name, ignore_permissions=True)
	frappe.clear_cache(doctype="Expense Claim")
	if not frappe.db.exists("Expense Claim Type", EXPENSE_TYPE):
		account = frappe.db.get_value("Account", {"company": company, "root_type": "Expense", "is_group": 0}, "name")
		doc = frappe.new_doc("Expense Claim Type")
		doc.expense_type = EXPENSE_TYPE
		doc.append("accounts", {"company": company, "default_account": account})
		doc.insert(ignore_permissions=True)


# --- last month's payslip -------------------------------------------------------------------


def _payslip(employee: str, company: str) -> str:
	"""A submitted slip for last month, through Frappe HR's own structure, assignment and slip."""
	currency = frappe.db.get_value("Company", company, "default_currency")
	if not frappe.db.exists("Salary Component", COMPONENT):
		frappe.new_doc("Salary Component").update({"salary_component": COMPONENT, "salary_component_abbr": "KBP", "type": "Earning"}).insert(ignore_permissions=True)
	structure = frappe.new_doc("Salary Structure")
	structure.update({"name": STRUCTURE, "__newname": STRUCTURE, "company": company, "payroll_frequency": "Monthly", "currency": currency, "is_active": "Yes"})
	structure.append("earnings", {"salary_component": COMPONENT, "abbr": "KBP", "amount_based_on_formula": 1, "formula": "base"})
	structure.insert(ignore_permissions=True)
	structure.submit()
	start = get_first_day(add_months(today(), -1))
	assignment = frappe.new_doc("Salary Structure Assignment")
	assignment.update(
		{
			"employee": employee,
			"salary_structure": structure.name,
			"company": company,
			"currency": currency,
			"from_date": add_months(start, -2),
			"base": 86500,
			"payroll_payable_account": frappe.db.get_value("Company", company, "default_payroll_payable_account"),
		}
	)
	assignment.insert(ignore_permissions=True)
	assignment.submit()
	slip = frappe.new_doc("Salary Slip")
	slip.update({"employee": employee, "company": company, "posting_date": get_last_day(start), "start_date": start, "end_date": get_last_day(start), "payroll_frequency": "Monthly", "currency": currency})
	slip.insert(ignore_permissions=True)
	slip.submit()
	return slip.name


def seed() -> None:
	"""Everything the walk reads, in the harness's transaction (as Administrator)."""
	from seal_common.messaging import push

	from seal_hrms.tests import _handover_fixtures as fx
	from seal_hrms.tests import _toil_fixtures as tf

	frappe.flags.in_test = True  # governance and similar guards let fixtures in; reset below
	try:
		people = _people()
		company = frappe.db.get_value("Employee", people["otieno"], "company")
		_rules(company)
		slip = _payslip(people["otieno"], company)
		push.ensure_keys()
	finally:
		frappe.flags.in_test = False
	frappe.clear_cache()
	monday = getdate(today())
	last_monday = add_days(monday, -monday.weekday() - 7)
	SEEDED.update(
		{
			**people,
			"otieno_name": "Otieno Ochieng",
			"achieng_name": "Achieng Odhiambo",
			"njeri_name": "Njeri Mwangi",
			"password": PASSWORD,
			"company": company,
			"payslip": slip,
			"leave_type": fx.ensure_leave_type(),
			"expense_type": EXPENSE_TYPE,
			"activity": ACTIVITY,
			"last_monday": str(last_monday),
			"rest_day": tf.rest_day(),
			"working_day": tf.working_day(),
			"started": str(frappe.utils.now_datetime()),
		}
	)


# --- asked for by the suite ---------------------------------------------------------------


def state() -> dict:
	"""Otieno's records as the database has them now (the suite checks the walk landed)."""
	employee = SEEDED["otieno"]
	pick = lambda doctype, fields, **filters: frappe.get_all(doctype, filters={"employee": employee, **filters}, fields=fields, order_by="creation asc")  # noqa: E731
	return {
		"leave": pick("Leave Application", ["name", "leave_type", "status", "docstatus", "from_date", "to_date"]),
		"handovers": frappe.get_all("Task Assignment", filters={"employee": employee}, fields=["name", "docstatus"], order_by="creation asc"),
		"toil": pick("Time Off in Lieu Claim", ["name", "status", "docstatus", "days"]),
		"timesheets": pick("Timesheet", ["name", "custom_approval_state", "custom_approver", "docstatus", "total_hours", "custom_week_start"]),
		"expenses": pick("Expense Claim", ["name", "approval_status", "docstatus", "total_claimed_amount"]),
		"checkins": pick("Employee Checkin", ["name", "log_type", "device_id"]),
		"payout": pick("Payout Change Request", ["name", "status", "change", "mobile_no"]),
		"notifications": frappe.get_all(
			"Notification Log",
			filters={"for_user": ["in", [SEEDED["otieno_user"], SEEDED["achieng_user"], SEEDED["njeri_user"]]], "creation": [">=", SEEDED.get("started", "2000-01-01")]},
			fields=["for_user", "subject", "document_type", "document_name"],
			order_by="creation asc",
		),
	}


def push_answers() -> list[dict]:
	"""For every HR Notification Log made in this run: the kind seal_hrms gives it and what a locked phone would show."""
	from seal_common.messaging import push as engine

	from seal_hrms.my_desk import push

	out = []
	for row in frappe.get_all(
		"Notification Log",
		filters={"creation": [">=", SEEDED.get("started", "2000-01-01")], "document_type": ["in", list(push.HR_DOCTYPES)]},
		fields=["name"],
		order_by="creation asc",
	):
		log = frappe.get_doc("Notification Log", row.name)
		out.append({"for_user": log.for_user, "doctype": log.document_type, "subject": log.subject, "kind": push.kind_of(log), "body": engine.message_for_log(log)["body"]})
	return out
