# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A timesheet filled in as a week: lines down the side, Monday to Sunday across.

Where a company's Working Time Policy says "one timesheet per person per week",
the form shows a grid; what the person types is kept as JSON in
`custom_week_entries`, and the timesheet's time lines are written from it on
every save while it is a draft:

    [{"row": 1, "activity_type": "...", "project": "...", "task": "...",
      "description": "...", "is_billable": 0, "hours": [Mon, ..., Sun]}, ...]

Each day's lines are placed back to back from the company's day start (whole
minutes, so ERPNext's recalculation of hours from the times is exact), and a
day must end by 23:59: a line ending at 00:00 moves the timesheet's end date
into the next day (WORKING_TIME_DESIGN.md F9, pinned in
tests/test_hrms_time_behaviour.py). One timesheet per person per week, so
ERPNext's overlap checks have nothing to collide with.

Leave and public holidays are shown on the week, not written as time lines
(decision D9, recommended option, `[unsupervised — review]`): written, they
would add to project costing and to pay by the hour.

`rows_for` is pure; the rest reads and writes the timesheet in its hooks.
"""

import json
from datetime import date, datetime, time, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, flt, formatdate, get_link_to_form, getdate

from seal_hrms.seal_hrms.working_time.policy import policy_for

LAST_MINUTE = 23 * 60 + 59  # a day's lines end by 23:59
DAYS = 7


class DayTooLong(ValueError):
	pass


# ---------------------------------------------------------------- pure


def minutes(hours) -> int:
	return int(round(flt(hours) * 60))


def rows_for(week_start: date, entries: list[dict], day_start_minutes: int = 8 * 60) -> list[dict]:
	"""Time lines for a week's entries: back to back from the day start, every day ending by 23:59."""
	rows = []
	for offset in range(DAYS):
		day = week_start + timedelta(days=offset)
		cells = []
		for entry in sorted(entries, key=lambda e: int(e.get("row") or 0)):
			hours = (entry.get("hours") or [])[offset] if offset < len(entry.get("hours") or []) else 0
			length = minutes(hours)
			if length > 0:
				cells.append((entry, length))
		if not cells:
			continue
		total = sum(length for _entry, length in cells)
		if total > LAST_MINUTE:
			raise DayTooLong(day)
		cursor = datetime.combine(day, time()) + timedelta(
			minutes=min(day_start_minutes, LAST_MINUTE - total)
		)
		for entry, length in cells:
			end = cursor + timedelta(minutes=length)
			rows.append(
				{
					"from_time": cursor,
					"to_time": end,
					"hours": round(length / 60, 4),
					"activity_type": entry.get("activity_type"),
					"project": entry.get("project") or None,
					"task": entry.get("task") or None,
					"description": entry.get("description") or None,
					"is_billable": 1 if entry.get("is_billable") else 0,
					"custom_grid_row": int(entry.get("row") or 0),
				}
			)
			cursor = end
	return rows


def monday_of(day) -> date:
	day = getdate(day)
	return day - timedelta(days=day.weekday())


# ---------------------------------------------------------------- the timesheet


def is_weekly(doc) -> bool:
	return bool(doc.get("employee") and doc.get("company") and policy_for(doc.company).weekly_timesheets)


def entries_of(doc) -> list[dict]:
	raw = doc.get("custom_week_entries")
	if not raw:
		return []
	try:
		entries = json.loads(raw) if isinstance(raw, str) else raw
	except ValueError:
		frappe.throw(_("The week could not be read. Reload the timesheet and enter it again."))
	return [e for e in entries if isinstance(e, dict)]


def _day_start(company: str) -> int:
	value = policy_for(company).day_starts_at
	if not value:
		return 8 * 60
	if isinstance(value, timedelta):
		return int(value.total_seconds() // 60)
	parts = str(value).split(":")
	return int(parts[0]) * 60 + int(parts[1] if len(parts) > 1 else 0)


def before_validate(doc, method=None) -> None:
	"""Timesheet before_validate: write the time lines from the week, while it is a draft."""
	if doc.docstatus != 0 or not is_weekly(doc) or not doc.get("custom_week_start"):
		return
	week_start = getdate(doc.custom_week_start)
	if week_start.weekday() != 0:
		frappe.throw(_("A week starts on a Monday; {0} is not one.").format(formatdate(week_start)))
	entries = entries_of(doc)
	for entry in entries:
		if any(flt(h) for h in entry.get("hours") or []) and not entry.get("activity_type"):
			frappe.throw(
				_("Line {0}: say what kind of work it was (activity type).").format(entry.get("row"))
			)
	try:
		rows = rows_for(week_start, entries, _day_start(doc.company))
	except DayTooLong as too_long:
		frappe.throw(_("More than 23 hours 59 minutes on {0}.").format(formatdate(too_long.args[0])))
	if not rows:
		frappe.throw(_("Enter the hours worked in the week."))
	doc.set("time_logs", [])
	for row in rows:
		doc.append("time_logs", row)


def validate(doc, method=None) -> None:
	"""Timesheet validate: one per person per week, and every line inside the week."""
	if not is_weekly(doc) or not doc.get("custom_week_start"):
		return
	week_start = getdate(doc.custom_week_start)
	week_end = add_days(week_start, DAYS - 1)
	for line in doc.time_logs:
		if not (week_start <= getdate(line.from_time) <= getdate(week_end)):
			frappe.throw(
				_("Row {0} is outside the week starting {1}.").format(line.idx, formatdate(week_start))
			)
	other = frappe.db.get_value(
		"Timesheet",
		[
			["employee", "=", doc.employee],
			["docstatus", "<", 2],
			["name", "!=", doc.name or ""],
			["start_date", "<=", week_end],
			["end_date", ">=", week_start],
		],
		"name",
	)
	if other:
		frappe.throw(
			_("{0} already has a timesheet for the week starting {1}: {2}.").format(
				doc.employee_name, formatdate(week_start), get_link_to_form("Timesheet", other)
			),
			title=_("One Timesheet a Week"),
		)


# ---------------------------------------------------------------- what the form shows


@frappe.whitelist()
def week_context(employee: str, week_start: str, timesheet: str | None = None) -> dict:
	"""For the week grid: each day's kind, leave and attendance, and last week's lines to copy. Reads only."""
	from seal_hrms.seal_hrms.toil import access
	from seal_hrms.seal_hrms.toil.evidence import attendance
	from seal_hrms.seal_hrms.toil.rules import leave_dates
	from seal_hrms.seal_hrms.working_time.calendar import day_kinds

	access.require_can_see_time(employee)
	company = frappe.db.get_value("Employee", employee, "company")
	policy = policy_for(company)
	start = monday_of(week_start)
	dates = [start + timedelta(days=n) for n in range(DAYS)]
	kinds = day_kinds(employee, dates)
	leave = leave_dates(employee, dates)
	half_days = _half_days(leave)
	seen = attendance(employee, dates)
	days = [
		{
			"date": str(day),
			"kind": kinds[day],
			"leave": leave.get(day),
			"leave_fraction": 0.5 if day in half_days else (1 if day in leave else 0),
			"attendance_hours": seen[day][0] if day in seen else None,
		}
		for day in dates
	]
	previous = frappe.db.get_value(
		"Timesheet",
		{"employee": employee, "custom_week_start": add_days(start, -DAYS), "docstatus": ["<", 2]},
		"custom_week_entries",
	)
	checks = []
	if timesheet and frappe.db.exists("Timesheet", timesheet):
		from seal_hrms.seal_hrms.timesheets import effort

		saved = frappe.get_doc("Timesheet", timesheet)
		if saved.employee == employee:
			week_check = effort.week_of(saved)
			checks = effort.describe(week_check) if week_check else []
	return {
		"weekly": bool(policy.weekly_timesheets),
		"checks": checks,
		"effort_rule": policy.effort_rule,
		"week_start": str(start),
		"hours_per_day": flt(policy.hours_per_day),
		"default_activity_type": policy.default_activity_type,
		"days": days,
		"previous_entries": json.loads(previous) if previous else [],
	}


def _half_days(leave: dict) -> set:
	"""Dates that are a half day of leave."""
	if not leave:
		return set()
	rows = frappe.get_all(
		"Leave Application",
		filters={"name": ["in", list(set(leave.values()))], "half_day": 1},
		fields=["half_day_date", "from_date", "to_date"],
	)
	return {getdate(r.half_day_date or r.from_date) for r in rows}


@frappe.whitelist()
def weekly_for(employee: str) -> dict:
	"""Whether this person's company fills timesheets in by the week, for a timesheet not yet saved. Reads only."""
	from seal_hrms.seal_hrms.toil import access

	access.require_can_see_time(employee)  # the person, their approver (or stand-in), HR
	policy = policy_for(frappe.db.get_value("Employee", employee, "company"))
	return {"weekly": bool(policy.weekly_timesheets), "default_activity_type": policy.default_activity_type}
