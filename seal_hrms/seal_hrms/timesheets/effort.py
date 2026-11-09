# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Does a week of timesheet account for the person's time? Checked against their calendar, leave and attendance.

For weekly timesheets (timesheets/week.py), per day:

    expected   = 0 on a rest day or public holiday, else the company's working day
    leave      = the working day x the approved leave that day (1, or 0.5 for a half day)
    logged     = hours on the timesheet that day
    accounted  = logged + leave

and these flags:

    on_leave        hours logged on a day of approved leave, beyond what the leave leaves free
    no_attendance   hours logged on a day attendance does not show the person present
                    (only for people whose attendance is kept: any in the 30 days before)
    short           a working day not accounted for
    extra           hours on a rest day or holiday, or beyond the working day (time off in lieu, maybe)

A company chooses (policy "Checking the week") whether gaps are only pointed out
or whether a week with a working day not accounted for, or with hours on a full
day of leave, cannot be sent for approval. Day by day: extra hours on one day do
not make up a short one. No tolerance (decision D10, recommended, `[unsupervised — review]`).

`check_days` is pure; the loaders read only.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, flt, formatdate, getdate

from seal_hrms.seal_hrms.toil.days import WORKING, round2
from seal_hrms.seal_hrms.working_time.policy import policy_for

EPS = 0.01
POINT_OUT = "Point out gaps"
REFUSE = "Refuse to send a week that is not accounted for"
ON_LEAVE, NO_ATTENDANCE, SHORT, EXTRA = "on_leave", "no_attendance", "short", "extra"
PRESENT = ("Present", "Half Day", "Work From Home")


@dataclass
class Day:
	date: date
	kind: str = WORKING
	leave_fraction: float = 0.0
	logged: float = 0.0
	attendance_kept: bool = False
	present: bool = False
	expected: float = 0.0
	accounted: float = 0.0
	flags: list = field(default_factory=list)


@dataclass
class Week:
	days: list
	expected: float = 0.0
	accounted: float = 0.0

	@property
	def short(self) -> bool:
		return self.accounted < self.expected - EPS

	def flagged(self, flag: str) -> list:
		return [d for d in self.days if flag in d.flags]


# ---------------------------------------------------------------- pure


def check_days(days: list[Day], hours_per_day: float) -> Week:
	for day in days:
		working = day.kind == WORKING
		day.expected = hours_per_day if working else 0.0
		leave_hours = hours_per_day * day.leave_fraction if working else 0.0
		day.accounted = round2(day.logged + leave_hours)
		if day.leave_fraction and day.logged > hours_per_day * (1 - day.leave_fraction) + EPS:
			day.flags.append(ON_LEAVE)
		if day.logged > EPS and day.attendance_kept and not day.present and not day.leave_fraction == 1:
			day.flags.append(NO_ATTENDANCE)
		if working and day.accounted < day.expected - EPS:
			day.flags.append(SHORT)
		if day.logged > EPS and (not working or day.logged > hours_per_day + EPS):
			day.flags.append(EXTRA)
	return Week(
		days=days,
		expected=round2(sum(d.expected for d in days)),
		accounted=round2(sum(d.accounted for d in days)),
	)


# ---------------------------------------------------------------- loaders


def facts(employee: str, dates: list[date], logged: dict) -> list[Day]:
	"""A Day per date, from the person's calendar, approved leave and attendance."""
	from seal_hrms.seal_hrms.timesheets.week import _half_days
	from seal_hrms.seal_hrms.toil.rules import leave_dates
	from seal_hrms.seal_hrms.working_time.calendar import day_kinds

	kinds = day_kinds(employee, dates)
	leave = leave_dates(employee, dates)
	half = _half_days(leave)
	present = set(
		getdate(d)
		for d in frappe.get_all(
			"Attendance",
			filters=[
				["employee", "=", employee],
				["docstatus", "=", 1],
				["status", "in", PRESENT],
				["attendance_date", "in", dates],
			],
			pluck="attendance_date",
		)
	)
	kept = bool(
		frappe.db.exists(
			"Attendance",
			[
				["employee", "=", employee],
				["docstatus", "=", 1],
				["attendance_date", ">=", add_days(min(dates), -30)],
				["attendance_date", "<=", max(dates)],
			],
		)
	)
	return [
		Day(
			date=day,
			kind=kinds[day],
			leave_fraction=0.5 if day in half else (1.0 if day in leave else 0.0),
			logged=round2(flt(logged.get(day))),
			attendance_kept=kept,
			present=day in present,
		)
		for day in dates
	]


def week_of(doc) -> Week | None:
	"""The check for a weekly timesheet, or None for one that is not a week."""
	if not doc.get("custom_week_start") or not doc.get("employee"):
		return None
	start = getdate(doc.custom_week_start)
	dates = [start + timedelta(days=n) for n in range(7)]
	logged: dict = {}
	for line in doc.get("time_logs") or []:
		if line.from_time:
			day = getdate(line.from_time)
			logged[day] = logged.get(day, 0) + flt(line.hours)
	return check_days(facts(doc.employee, dates, logged), flt(policy_for(doc.company).hours_per_day))


def describe(week: Week) -> list[str]:
	"""What the person should look at, one line per point, in their words."""
	lines = []
	for day in week.flagged(ON_LEAVE):
		lines.append(_("{0}: hours recorded on a day of approved leave.").format(formatdate(day.date)))
	for day in week.flagged(NO_ATTENDANCE):
		lines.append(
			_("{0}: hours recorded, but attendance does not show you present.").format(formatdate(day.date))
		)
	for day in week.flagged(SHORT):
		lines.append(
			_("{0}: {1} of {2} hours accounted for.").format(
				formatdate(day.date), f"{day.accounted:g}", f"{day.expected:g}"
			)
		)
	return lines


def check_before_sending(doc) -> None:
	"""At Send for Approval: where the company refuses unaccounted weeks, refuse one."""
	if policy_for(doc.company).effort_rule != REFUSE:
		return
	week = week_of(doc)
	if not week:
		return
	# Day by day, as the policy says: extra hours on one day do not make up a short one.
	full_leave = [d for d in week.flagged(ON_LEAVE) if d.leave_fraction == 1]
	if week.flagged(SHORT) or full_leave:
		frappe.throw(
			_("This week does not yet account for your time. Correct it, then send it:")
			+ "<ul>"
			+ "".join(f"<li>{line}</li>" for line in describe(week))
			+ "</ul>",
			title=_("Week Not Accounted For"),
		)
