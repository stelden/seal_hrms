# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""People, calendar and rules for the time off in lieu tests.

The same small Nairobi office as the handover tests (`_handover_fixtures`):
Otieno is a programme officer who works extra, Achieng approves his leave, and
Njeri is a colleague who should see none of it. Everything goes through the ORM
(SEAL_DEV_RULES §1.9), and each test is rolled back to a savepoint.

Otieno gets his own holiday list, relative to today, so the kinds of day are
fixed whatever date the tests run on: Sundays are rest days, and one Tuesday a
week or more back is a public holiday.
"""

import frappe
from frappe.utils import add_days, getdate, today

from seal_hrms.tests import _handover_fixtures as fx

COMPANY = fx.COMPANY
LEAVE_TYPE = "Kilimani Time Off in Lieu"
GRADE = "Programme Officer - Kilimani"
OTHER_GRADE = "Senior Manager - Kilimani"
HOLIDAY_LIST = "Kilimani Office Calendar"
CLAIM = "Time Off in Lieu Claim"
NOTICE_FIELDS = (
	"custom_minimum_leave_application_days",
	"custom_min_application_advance_days",
	"custom_min_leave_days",
	"custom_is_plannable",
)


def _day(weekday: int, at_least_days_ago: int) -> str:
	"""The latest date with this weekday (Monday 0) at least `at_least_days_ago` days back."""
	day = getdate(add_days(today(), -at_least_days_ago))
	while day.weekday() != weekday:
		day = getdate(add_days(day, -1))
	return str(day)


def public_holiday() -> str:
	return _day(1, 8)  # a Tuesday


def rest_day() -> str:
	return _day(6, 2)  # a Sunday


def working_day(at_least_days_ago: int = 2) -> str:
	day = _day(2, at_least_days_ago)  # a Wednesday, never the Tuesday holiday
	return day


def ensure_leave_type() -> str:
	if not frappe.db.exists("Leave Type", LEAVE_TYPE):
		doc = frappe.new_doc("Leave Type")
		doc.leave_type_name = LEAVE_TYPE
		doc.is_compensatory = 1
		doc.include_holiday = 1
		doc.insert(ignore_permissions=True)
	doc = frappe.get_doc("Leave Type", LEAVE_TYPE)
	for field in NOTICE_FIELDS:
		if doc.meta.has_field(field) and doc.get(field):
			doc.set(field, 0)
	doc.save(ignore_permissions=True)
	return LEAVE_TYPE


def ensure_grade(name: str = GRADE) -> str:
	if not frappe.db.exists("Employee Grade", name):
		doc = frappe.new_doc("Employee Grade")
		doc.name = name
		doc.insert(ignore_permissions=True)
	return name


def ensure_holiday_list() -> str:
	if not frappe.db.exists("Holiday List", HOLIDAY_LIST):
		doc = frappe.new_doc("Holiday List")
		doc.holiday_list_name = HOLIDAY_LIST
		doc.from_date = add_days(today(), -120)
		doc.to_date = add_days(today(), 120)
		doc.weekly_off = "Sunday"
		doc.get_weekly_off_dates()
		doc.append(
			"holidays", {"holiday_date": public_holiday(), "description": "Utamaduni Day", "weekly_off": 0}
		)
		doc.insert(ignore_permissions=True)
	return HOLIDAY_LIST


def assign_holiday_list(employee: str) -> None:
	if frappe.db.exists(
		"Holiday List Assignment", {"assigned_to": employee, "holiday_list": HOLIDAY_LIST, "docstatus": 1}
	):
		return
	doc = frappe.new_doc("Holiday List Assignment")
	doc.applicable_for = "Employee"
	doc.assigned_to = employee
	doc.holiday_list = ensure_holiday_list()
	doc.from_date = add_days(today(), -120)
	doc.insert(ignore_permissions=True)
	doc.submit()


def ensure_leave_period() -> None:
	"""A leave period covering today, so these tests outlive the one dev.local has."""
	from hrms.hr.utils import get_leave_period

	if get_leave_period(today(), today(), COMPANY):
		return
	year = getdate(today()).year
	doc = frappe.new_doc("Leave Period")
	doc.from_date = f"{year}-01-01"
	doc.to_date = f"{year}-12-31"
	doc.company = COMPANY
	doc.is_active = 1
	doc.insert(ignore_permissions=True)


def policy(**values):
	"""Turn time off in lieu on for the test company, with any rules overridden."""
	if frappe.db.exists("Working Time Policy", COMPANY):
		doc = frappe.get_doc("Working Time Policy", COMPANY)
	else:
		doc = frappe.new_doc("Working Time Policy")
		doc.company = COMPANY
	doc.update(
		{
			"hours_per_day": 8,
			"toil_enabled": 1,
			"leave_type": ensure_leave_type(),
			"claim_within_days": 0,
			"validity_days": 90,
			"balance_cap": 0,
			"minimum_hours": 1,
			"daily_cap": 0,
			"after_hours_rate": 1,
			"rest_day_rate": 1,
			"public_holiday_rate": 1,
		}
	)
	doc.update(values)
	doc.set("eligible_grades", [{"grade": ensure_grade()}])
	doc.save(ignore_permissions=True)
	return doc


def set_up_otieno() -> str:
	"""Otieno: a programme officer in a banking grade, approved by Achieng, on his own calendar."""
	employee = fx.ensure_employee("otieno")
	doc = frappe.get_doc("Employee", employee)
	doc.grade = ensure_grade()
	doc.leave_approver = fx.approver()
	doc.save(ignore_permissions=True)
	# Links fetch through the process's value cache; make it read his new grade and approver.
	frappe.db.value_cache.clear()
	assign_holiday_list(employee)
	return employee


def claim(employee: str, lines: list[tuple[str, float]], as_user: str | None = None, insert: bool = True):
	doc = frappe.new_doc(CLAIM)
	doc.employee = employee
	# Permission is checked before links fetch, so a blank company would be the creator's default.
	doc.company = frappe.db.get_value("Employee", employee, "company")
	for work_date, hours in lines:
		doc.append(
			"lines",
			{"work_date": work_date, "hours": hours, "work_done": "Community health drive in Kibera"},
		)
	if insert:
		if as_user:
			fx.as_user(as_user, doc.insert)
		else:
			doc.insert()
	return doc


# ---------------------------------------------------------------- browser walks


def browser_set_up(password_otieno: str, password_achieng: str, **rules) -> dict:
	"""Seed a committed browser walk; returns what `browser_tear_down` needs to put things back."""
	from frappe.utils.password import update_password

	employee = fx.ensure_employee("otieno")
	original = frappe.db.get_value(
		"Employee", employee, ["company", "grade", "leave_approver", "department", "reports_to"], as_dict=True
	)
	had_policy = frappe.db.exists("Working Time Policy", COMPANY)
	ensure_leave_period()
	started = str(frappe.utils.now_datetime())
	set_up_otieno()
	if not frappe.db.exists("Activity Type", "Community Outreach"):
		activity = frappe.new_doc("Activity Type")
		activity.activity_type = "Community Outreach"
		activity.insert(ignore_permissions=True)
	policy(**rules)
	for key, password in (("otieno", password_otieno), ("achieng", password_achieng)):
		user = frappe.get_doc("User", fx.email(key))
		user.user_type = "System User"
		user.save(ignore_permissions=True)
		update_password(user.name, password)
	return {
		"employee": employee,
		"otieno_user": fx.email("otieno"),
		"achieng_user": fx.approver(),
		"original": original,
		"had_policy": bool(had_policy),
		"rest_day": rest_day(),
		"working_day": working_day(),
		"started": started,
	}


def browser_tear_down(seed: dict) -> None:
	"""Remove what the walk made (its claims, allocation, ledger rows, calendar) and put Otieno back."""
	from seal_hrms.seal_hrms.toil.ledger import toil_ledger_writes

	employee = seed["employee"]
	with toil_ledger_writes():
		for name in frappe.get_all(CLAIM, filters={"employee": employee}, pluck="name"):
			frappe.db.delete("Leave Ledger Entry", {"custom_toil_claim": name})
			frappe.db.set_value(CLAIM, name, "docstatus", 2)  # a submitted claim cannot be deleted
			frappe.delete_doc(CLAIM, name, force=1, ignore_permissions=True)
		for name in frappe.get_all(
			"Leave Allocation", filters={"employee": employee, "leave_type": LEAVE_TYPE}, pluck="name"
		):
			frappe.db.delete("Leave Ledger Entry", {"transaction_name": name})
			frappe.db.set_value("Leave Allocation", name, "docstatus", 2)
			frappe.delete_doc("Leave Allocation", name, force=1, ignore_permissions=True)
		for name in frappe.get_all(
			"Holiday List Assignment",
			filters={"assigned_to": employee, "holiday_list": HOLIDAY_LIST},
			pluck="name",
		):
			frappe.db.set_value("Holiday List Assignment", name, "docstatus", 2)
			frappe.delete_doc("Holiday List Assignment", name, force=1, ignore_permissions=True)
	for name in frappe.get_all(
		"Timesheet",
		filters=[["employee", "=", employee], ["creation", ">=", seed.get("started") or "2999-01-01"]],
		pluck="name",
	):
		frappe.db.set_value("Timesheet", name, "docstatus", 2)
		frappe.delete_doc("Timesheet", name, force=1, ignore_permissions=True)
	if not seed.get("had_policy") and frappe.db.exists("Working Time Policy", COMPANY):
		frappe.delete_doc("Working Time Policy", COMPANY, force=1, ignore_permissions=True)
	original = seed["original"]
	frappe.db.set_value("Employee", employee, original, update_modified=False)
