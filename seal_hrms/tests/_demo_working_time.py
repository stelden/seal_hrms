# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A small, removable set of records to try time off in lieu and timesheets by hand.

Not a test: a seed for a person clicking through, on one company of a local copy
(wel.local's "Women Empowerment Link (Demo)", 2026-11-10). Everything it makes is
listed in a site default, and `remove` deletes exactly that and what was done
with it (claims, timesheets, leave, allocations), so the site goes back as it was.

    bench --site wel.local execute seal_hrms.tests._demo_working_time.seed
    bench --site wel.local execute seal_hrms.tests._demo_working_time.remove

Logins use the reserved `.example` domain, so no real mail is sent anywhere.
"""

import contextlib
import json

import frappe
from frappe.utils.password import update_password

COMPANY = "Women Empowerment Link (Demo)"
YEAR = 2026
KEY = "seal_hrms_working_time_demo"
DOMAIN = "wel-demo.example"
PASSWORD = "Kilimani-Demo-2026!"
LEAVE_TYPE = "Time Off in Lieu"
GRADE = "Programme Officer"
HOLIDAY_LIST = "WEL Demo Office 2026"
ACTIVITY = "Execution"

#: Kenyan public holidays in 2026 that fall on a weekday (weekends are rest days anyway).
PUBLIC_HOLIDAYS = {
	"2026-01-01": "New Year's Day",
	"2026-04-03": "Good Friday",
	"2026-04-06": "Easter Monday",
	"2026-05-01": "Labour Day",
	"2026-06-01": "Madaraka Day",
	"2026-10-20": "Mashujaa Day",
	"2026-12-25": "Christmas Day",
}

#: key -> (first, last, gender, phone, approves others)
PEOPLE = {
	"wanjiru": ("Wanjiru", "Kariuki", "Female", "254722301845", True),
	"brian": ("Brian", "Otieno", "Male", "254733617290", False),
	"faith": ("Faith", "Achieng", "Female", "254711904356", False),
}


def _email(key: str) -> str:
	first, last, *_rest = PEOPLE[key]
	return f"{first.lower()}.{last.lower()}@{DOMAIN}"


@contextlib.contextmanager
def _governed():
	"""Write past data governance where it is installed, as a patch would (SEAL_DEV_RULES §3.11b)."""
	if "seal_governance" in frappe.get_installed_apps():
		from seal_governance.data_governance.change_request_utils import mdc_bypass

		with mdc_bypass():
			yield
	else:
		yield


def _made() -> list:
	return json.loads(frappe.db.get_default(KEY) or "[]")


def _remember(made: list) -> None:
	frappe.db.set_default(KEY, json.dumps(made))


def seed() -> dict:
	"""Create the demo set once; running it again changes nothing."""
	if not frappe.db.exists("Company", COMPANY):
		frappe.throw(f"{COMPANY} is not on this site")
	if _made():
		return {"already": True, "logins": {k: _email(k) for k in PEOPLE}, "password": PASSWORD}
	made: list = []

	def keep(doc):
		made.append([doc.doctype, doc.name])
		return doc

	with _governed():
		if not frappe.db.exists(
			"Leave Period", {"company": COMPANY, "is_active": 1, "from_date": f"{YEAR}-01-01"}
		):
			period = frappe.new_doc("Leave Period")
			period.update(
				{"from_date": f"{YEAR}-01-01", "to_date": f"{YEAR}-12-31", "company": COMPANY, "is_active": 1}
			)
			keep(period.insert(ignore_permissions=True))

		if not frappe.db.exists("Holiday List", HOLIDAY_LIST):
			holidays = frappe.new_doc("Holiday List")
			holidays.update(
				{"holiday_list_name": HOLIDAY_LIST, "from_date": f"{YEAR}-01-01", "to_date": f"{YEAR}-12-31"}
			)
			for weekly_off in ("Saturday", "Sunday"):
				holidays.weekly_off = weekly_off
				holidays.get_weekly_off_dates()
			for day, description in PUBLIC_HOLIDAYS.items():
				holidays.append(
					"holidays", {"holiday_date": day, "description": description, "weekly_off": 0}
				)
			keep(holidays.insert(ignore_permissions=True))
			assignment = frappe.new_doc("Holiday List Assignment")
			assignment.update(
				{
					"applicable_for": "Company",
					"assigned_to": COMPANY,
					"holiday_list": HOLIDAY_LIST,
					"from_date": f"{YEAR}-01-01",
				}
			)
			assignment.insert(ignore_permissions=True)
			assignment.submit()
			keep(assignment)

		if not frappe.db.exists("Employee Grade", GRADE):
			grade = frappe.new_doc("Employee Grade")
			grade.name = GRADE
			keep(grade.insert(ignore_permissions=True))

		if not frappe.db.exists("Leave Type", LEAVE_TYPE):
			leave_type = frappe.new_doc("Leave Type")
			leave_type.update({"leave_type_name": LEAVE_TYPE, "is_compensatory": 1, "include_holiday": 0})
			for field in (
				"custom_minimum_leave_application_days",
				"custom_is_plannable",
				"custom_include_in_leave_plan",
			):
				if leave_type.meta.has_field(field):
					leave_type.set(field, 0)
			keep(leave_type.insert(ignore_permissions=True))

		employees = {}
		for key in ("wanjiru", "brian", "faith"):
			first, last, gender, phone, approves = PEOPLE[key]
			user = frappe.new_doc("User")
			user.update(
				{
					"email": _email(key),
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Employee", "Employee Self Service", *(("Leave Approver",) if approves else ()))
			update_password(user.name, PASSWORD)
			keep(user)
			employee = frappe.new_doc("Employee")
			employee.update(
				{
					"first_name": first,
					"last_name": last,
					"gender": gender,
					"date_of_birth": "1990-06-15",
					"date_of_joining": "2024-02-01",
					"status": "Active",
					"company": COMPANY,
					"cell_number": phone,
					"user_id": user.name,
					"grade": GRADE if not approves else None,
					"leave_approver": None if approves else _email("wanjiru"),
				}
			)
			employees[key] = keep(employee.insert(ignore_permissions=True)).name
		for key in ("brian", "faith"):
			frappe.db.set_value("Employee", employees[key], "reports_to", employees["wanjiru"])

		if frappe.db.exists("Working Time Policy", COMPANY):
			frappe.throw(f"{COMPANY} already has a Working Time Policy; not touching it")
		policy = frappe.new_doc("Working Time Policy")
		policy.update(
			{
				"company": COMPANY,
				"toil_enabled": 1,
				"leave_type": LEAVE_TYPE,
				"timesheet_approval": 1,
				"weekly_timesheets": 1,
				"default_activity_type": ACTIVITY,
			}
		)
		policy.append("eligible_grades", {"grade": GRADE})
		keep(policy.insert(ignore_permissions=True))
	_remember(made)
	frappe.db.commit()
	return {"logins": {k: _email(k) for k in PEOPLE}, "password": PASSWORD, "made": made}


def remove() -> dict:
	"""Delete what `seed` made and everything done with it, newest first. Leaves all else alone."""
	from seal_hrms.seal_hrms.toil.ledger import toil_ledger_writes

	made = _made()
	employees = [name for doctype, name in made if doctype == "Employee"]
	users = [name for doctype, name in made if doctype == "User"]
	removed = []

	def drop(doctype, name):
		if not frappe.db.exists(doctype, name):
			return
		if frappe.get_meta(doctype).is_submittable:
			frappe.db.set_value(doctype, name, "docstatus", 2, update_modified=False)
		frappe.delete_doc(doctype, name, force=1, ignore_permissions=True, delete_permanently=True)
		removed.append([doctype, name])

	with _governed(), toil_ledger_writes():
		if employees:
			for doctype in (
				"Time Off in Lieu Claim",
				"Timesheet",
				"Leave Application",
				"Leave Allocation",
				"Attendance",
				"Employee Checkin",
				"Overtime Slip",
				"Task Assignment",
			):
				if not frappe.db.exists("DocType", doctype):
					continue
				for name in frappe.get_all(doctype, filters={"employee": ["in", employees]}, pluck="name"):
					if doctype == "Leave Allocation":
						frappe.db.delete("Leave Ledger Entry", {"transaction_name": name})
					if doctype == "Time Off in Lieu Claim":
						frappe.db.delete("Leave Ledger Entry", {"custom_toil_claim": name})
					drop(doctype, name)
			frappe.db.delete("Leave Ledger Entry", {"employee": ["in", employees]})
		for name in (
			frappe.get_all("ToDo", filters={"allocated_to": ["in", users]}, pluck="name") if users else []
		):
			drop("ToDo", name)
		for doctype, name in reversed(made):
			if doctype == "Employee":
				frappe.db.set_value(
					"Employee", name, {"reports_to": None, "user_id": None}, update_modified=False
				)
			drop(doctype, name)
	frappe.db.set_default(KEY, None)
	frappe.db.commit()
	return {"removed": len(removed)}
