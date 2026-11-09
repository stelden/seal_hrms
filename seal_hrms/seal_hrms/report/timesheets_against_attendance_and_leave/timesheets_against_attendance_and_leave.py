# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Each person's days: timesheet hours beside leave, holidays and attendance, and what does not add up.

The same rules as the weekly check on the Timesheet form (`timesheets/effort.py`),
over any dates (at most 62 days) and every active person at a company. Timesheet
hours include drafts, so HR sees a week before it is sent. One person's days are
worked out at a time; pick a department or a person to narrow a large company.
"""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import flt, getdate

from seal_hrms.seal_hrms.timesheets import effort
from seal_hrms.seal_hrms.working_time.policy import policy_for

MAX_DAYS = 62
FLAG_WORDS = {
	effort.ON_LEAVE: _("Hours on a day of leave"),
	effort.NO_ATTENDANCE: _("Hours, but not present"),
	effort.SHORT: _("Not accounted for"),
	effort.EXTRA: _("Extra hours"),
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return _columns(), _rows(filters)


def _columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{"label": _("Kind of Day"), "fieldname": "kind", "fieldtype": "Data", "width": 110},
		{"label": _("Leave"), "fieldname": "leave", "fieldtype": "Data", "width": 80},
		{"label": _("Present"), "fieldname": "present", "fieldtype": "Data", "width": 80},
		{"label": _("Timesheet Hours"), "fieldname": "logged", "fieldtype": "Float", "width": 120},
		{"label": _("Expected"), "fieldname": "expected", "fieldtype": "Float", "width": 90},
		{"label": _("Accounted For"), "fieldname": "accounted", "fieldtype": "Float", "width": 110},
		{"label": _("Issues"), "fieldname": "flags", "fieldtype": "Data", "width": 260},
	]


def _rows(filters):
	if not filters.company or not filters.from_date or not filters.to_date:
		return []
	start, end = getdate(filters.from_date), getdate(filters.to_date)
	if end < start:
		return []
	if (end - start).days >= MAX_DAYS:
		frappe.throw(_("Pick at most {0} days at a time.").format(MAX_DAYS))
	dates = [start + timedelta(days=n) for n in range((end - start).days + 1)]
	hours_per_day = flt(policy_for(filters.company).hours_per_day)
	people = frappe.get_list(
		"Employee",
		filters=[
			["company", "=", filters.company],
			["status", "=", "Active"],
			*([["department", "=", filters.department]] if filters.department else []),
			*([["name", "=", filters.employee]] if filters.employee else []),
		],
		fields=["name", "employee_name"],
		order_by="employee_name asc",
	)
	if not people:
		return []
	logged = _logged([p.name for p in people], start, end)
	rows = []
	for person in people:
		try:
			week = effort.check_days(
				effort.facts(person.name, dates, logged.get(person.name, {})), hours_per_day
			)
		except frappe.ValidationError:
			# No holiday list: the kinds of day cannot be told; say so once rather than guess.
			frappe.clear_last_message()
			rows.append(
				frappe._dict(
					employee=person.name, employee_name=person.employee_name, flags=_("No holiday list")
				)
			)
			continue
		for day in week.days:
			if filters.only_issues and not [f for f in day.flags if f != effort.EXTRA]:
				continue
			rows.append(
				frappe._dict(
					employee=person.name,
					employee_name=person.employee_name,
					date=day.date,
					kind=_(day.kind),
					leave=_("Full day")
					if day.leave_fraction == 1
					else (_("Half day") if day.leave_fraction else ""),
					present=_("Yes") if day.present else ("" if not day.attendance_kept else _("No")),
					logged=day.logged,
					expected=day.expected,
					accounted=day.accounted,
					flags=", ".join(FLAG_WORDS[f] for f in day.flags),
				)
			)
	return rows


def _logged(employees, start, end) -> dict:
	"""{employee: {date: hours}} on timesheets not cancelled (drafts included)."""
	rows = frappe.db.sql(
		"""
		SELECT t.employee, DATE(d.from_time) AS day, SUM(d.hours) AS hours
		FROM `tabTimesheet Detail` d INNER JOIN `tabTimesheet` t ON t.name = d.parent
		WHERE t.employee IN %(employees)s AND t.docstatus < 2
		  AND d.from_time >= %(start)s AND d.from_time < %(after)s
		GROUP BY t.employee, DATE(d.from_time)
		""",
		{
			"employees": employees,
			"start": f"{start} 00:00:00",
			"after": f"{end + timedelta(days=1)} 00:00:00",
		},
		as_dict=True,
	)
	out: dict = {}
	for r in rows:
		out.setdefault(r.employee, {})[getdate(r.day)] = flt(r.hours)
	return out
