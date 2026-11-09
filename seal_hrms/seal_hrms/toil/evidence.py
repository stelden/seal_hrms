# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What the records say about extra hours: attendance, clock-ins and timesheets.

Shown beside each claim line, so an approver sees whether the hours are borne
out, and used to fill a claim from the records ("Fetch"). The supervisor's word
is always enough (decision 2026-11-09): a line no record supports is allowed
and marked "Approver only", so the approver knows they are confirming it.

Extra hours on a rest day or public holiday are all the hours worked; on a
working day, the hours beyond the normal day: the attendance's standard hours
if it has them, else the shift's length, else the company's working day.

Everything here reads; nothing is written (SEAL_DEV_RULES §3.1).
"""

from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

from seal_hrms.seal_hrms.toil import access, rules
from seal_hrms.seal_hrms.toil.days import WORKING, round2
from seal_hrms.seal_hrms.working_time.calendar import day_kinds
from seal_hrms.seal_hrms.working_time.policy import policy_for

ATTENDANCE, CLOCK_INS, TIMESHEET, APPROVER_ONLY = "Attendance", "Clock-ins", "Timesheet", "Approver only"
SOURCES = (ATTENDANCE, CLOCK_INS, TIMESHEET)
PRESENT = ("Present", "Half Day", "Work From Home")
TOLERANCE = 0.25  # a quarter of an hour either way is the same claim
MAX_FETCH_DAYS = 62


# ---------------------------------------------------------------- pure


def extra(kind: str, worked: float, normal: float) -> float:
	"""Extra hours in a day: all of it on a rest day or holiday, what is beyond the normal day otherwise."""
	if not worked:
		return 0.0
	return round2(worked if kind != WORKING else max(worked - normal, 0.0))


def supported_by(claimed: float, extras: dict) -> str:
	"""The first source, in SOURCES order, whose extra hours bear out the claim."""
	for source in SOURCES:
		if source in extras and extras[source] >= claimed - TOLERANCE:
			return source
	return APPROVER_ONLY


# ---------------------------------------------------------------- loaders


def _shift_hours(shift: str | None) -> float:
	if not shift:
		return 0.0
	from hrms.hr.doctype.employee_checkin.employee_checkin import calculate_time_difference

	start, end = frappe.db.get_value("Shift Type", shift, ["start_time", "end_time"]) or (None, None)
	return flt(calculate_time_difference(start, end)) if start is not None and end is not None else 0.0


def attendance(employee: str, dates) -> dict:
	"""{date: (hours worked, normal hours or 0)} from submitted attendance."""
	if not dates:
		return {}
	rows = frappe.get_all(
		"Attendance",
		filters=[
			["employee", "=", employee],
			["docstatus", "=", 1],
			["status", "in", PRESENT],
			["attendance_date", "in", list(dates)],
		],
		fields=["attendance_date", "working_hours", "standard_working_hours", "shift"],
	)
	return {
		getdate(r.attendance_date): (
			flt(r.working_hours),
			flt(r.standard_working_hours) or _shift_hours(r.shift),
		)
		for r in rows
	}


def clock_ins(employee: str, dates) -> dict:
	"""{date: hours from the first clock-in to the last} for dates with two or more clock-ins."""
	if not dates:
		return {}
	first, last = min(dates), max(dates)
	spans: dict[date, list] = {}
	for row in frappe.get_all(
		"Employee Checkin",
		filters=[
			["employee", "=", employee],
			["time", ">=", f"{first} 00:00:00"],
			["time", "<", f"{add_days(last, 1)} 00:00:00"],
		],
		fields=["time"],
		order_by="time asc",
	):
		spans.setdefault(getdate(row.time), []).append(row.time)
	return {
		day: round2((times[-1] - times[0]).total_seconds() / 3600)
		for day, times in spans.items()
		if len(times) > 1 and day in set(dates)
	}


def timesheet_hours(employee: str, dates) -> dict:
	"""{date: hours on submitted timesheets that start that day}."""
	if not dates:
		return {}
	first, last = min(dates), max(dates)
	rows = frappe.db.sql(
		"""
		SELECT DATE(d.from_time) AS day, SUM(d.hours) AS hours
		FROM `tabTimesheet Detail` d INNER JOIN `tabTimesheet` t ON t.name = d.parent
		WHERE t.employee = %(employee)s AND t.docstatus = 1
		  AND d.from_time >= %(first)s AND d.from_time < %(after)s
		GROUP BY DATE(d.from_time)
		""",
		{"employee": employee, "first": f"{first} 00:00:00", "after": f"{add_days(last, 1)} 00:00:00"},
		as_dict=True,
	)
	return {getdate(r.day): flt(r.hours) for r in rows if getdate(r.day) in set(dates)}


def records(employee: str, dates, kinds: dict, policy) -> dict:
	"""{date: {"normal": hours, ATTENDANCE: extra, CLOCK_INS: extra, TIMESHEET: extra}}, per the policy's switches."""
	dates = sorted({getdate(d) for d in dates})
	seen = attendance(employee, dates) if policy.evidence_attendance else {}
	clocked = clock_ins(employee, dates) if policy.evidence_attendance else {}
	logged = timesheet_hours(employee, dates) if policy.evidence_timesheets else {}
	result = {}
	for day in dates:
		kind = kinds.get(day, WORKING)
		worked, standard = seen.get(day, (0.0, 0.0))
		normal = standard or flt(policy.hours_per_day)
		found = {"normal": normal}
		if day in seen:
			found[ATTENDANCE] = extra(kind, worked, normal)
		if day in clocked:
			found[CLOCK_INS] = extra(kind, clocked[day], normal)
		if day in logged:
			found[TIMESHEET] = extra(kind, logged[day], flt(policy.hours_per_day))
		result[day] = found
	return result


def annotate(doc, policy, kinds: dict) -> None:
	"""Fill each claim line's "What the records show"."""
	found = records(doc.employee, [line.work_date for line in doc.lines if line.work_date], kinds, policy)
	for line in doc.lines:
		day = found.get(getdate(line.work_date), {"normal": flt(policy.hours_per_day)})
		line.normal_hours = day["normal"]
		line.attendance_hours = day.get(ATTENDANCE)
		line.clocked_hours = day.get(CLOCK_INS)
		line.timesheet_hours = day.get(TIMESHEET)
		line.supported_by = (
			supported_by(flt(line.hours or line.get("planned_hours")), day) if line.hours else None
		)


# ---------------------------------------------------------------- fetch


@frappe.whitelist()
def get_extra_time(employee: str, from_date: str, to_date: str, source: str) -> list[dict]:
	"""Days the records show extra hours on, ready to become claim lines. Reads only.

	Leaves out days in the future, under the company's minimum, already claimed,
	paid as overtime, or on approved leave.
	"""
	access.require_can_see_time(employee)
	if source not in (ATTENDANCE, TIMESHEET):
		frappe.throw(_("Fill from attendance or from timesheets."))
	start, end = getdate(from_date), min(getdate(to_date), getdate(today()))
	if end < start:
		return []
	if (end - start).days > MAX_FETCH_DAYS:
		frappe.throw(_("Pick at most {0} days at a time.").format(MAX_FETCH_DAYS))
	company = frappe.db.get_value("Employee", employee, "company")
	policy = policy_for(company)
	switched_on = policy.evidence_attendance if source == ATTENDANCE else policy.evidence_timesheets
	if not switched_on:
		frappe.throw(_("{0} does not use {1} as a record of extra hours.").format(company, _(source)))
	dates = [start + timedelta(days=n) for n in range((end - start).days + 1)]
	kinds = day_kinds(employee, dates)
	found = records(employee, dates, kinds, policy)
	taken = (
		set(rules.claimed_dates(employee, dates))
		| set(rules.paid_dates(employee, dates))
		| set(rules.leave_dates(employee, dates))
	)
	rows = []
	for day in dates:
		if day in taken:
			continue
		day_found = found.get(day, {})
		hours = (
			day_found.get(ATTENDANCE, day_found.get(CLOCK_INS))
			if source == ATTENDANCE
			else day_found.get(TIMESHEET)
		)
		if not hours or hours < flt(policy.minimum_hours):
			continue
		rows.append({"work_date": str(day), "hours": hours, "day_kind": kinds[day], "source": source})
	return rows
