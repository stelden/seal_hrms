# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Server methods backing the Leave Planning report pages.

Three @whitelist endpoints, each returning a JSON-serialisable dict the
client renders. Pure read functions — no DB writes, no notifications.

Per SEAL_DEV_RULES:
  - §2.8 — uses frappe.get_list (NOT get_all) so DocPerm + query_conditions
           filtering applies. Leave Approvers see own department; HR sees all.
  - §2.5 — Pages auto-apply Data Masking via get_list. Future masked fields
           (e.g. salary on Employee) would appear masked in the slide-in panel
           without code changes.
  - §3.4 — relies on the permission_query_conditions wired in hooks.py.
"""

from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import flt, getdate


HR_BACKOFFICE_ROLES = {"HR User", "HR Manager"}


@frappe.whitelist()
def departmental_coverage(
	company: str,
	department: str | None = None,
	leave_period: str | None = None,
	leave_types: list[str] | str | None = None,
	start_week: str | None = None,
	end_week: str | None = None,
) -> dict:
	"""Weekly absence aggregation for a department (or scope visible to caller).

	Returns:
	  {
	    weeks: ["2026-W01", "2026-W02", ...],
	    headcount: {<dept>: int},
	    cells: [{department, week, absent_days, absent_employees, headcount, percent_absent}],
	  }
	"""
	leave_types = _normalise_list(leave_types)
	period = _resolve_period(leave_period, company)
	week_start, week_end = _resolve_window(start_week, end_week, period)

	viewable_depts = _viewable_departments(company, department)
	if not viewable_depts:
		return {"weeks": [], "headcount": {}, "cells": []}

	employees = frappe.get_list(
		"Employee",
		filters={
			"status": "Active",
			"company": company,
			"department": ["in", viewable_depts],
		},
		fields=["name", "employee_name", "department", "holiday_list"],
	)
	if not employees:
		return {"weeks": _iso_weeks(week_start, week_end), "headcount": {d: 0 for d in viewable_depts}, "cells": []}

	emp_by_name = {e.name: e for e in employees}
	headcount: dict[str, int] = {}
	for e in employees:
		headcount[e.department] = headcount.get(e.department, 0) + 1

	plans = frappe.get_list(
		"Leave Plan",
		filters={
			"employee": ["in", list(emp_by_name.keys())],
			"docstatus": 1,
		},
		fields=["name", "employee"],
	)
	if not plans:
		return {"weeks": _iso_weeks(week_start, week_end), "headcount": headcount, "cells": []}

	plan_to_emp = {p.name: p.employee for p in plans}

	slot_filters = {
		"parent": ["in", list(plan_to_emp.keys())],
		"slot_status": ["!=", "Cancelled"],
	}
	if leave_types:
		slot_filters["leave_type"] = ["in", leave_types]

	slots = frappe.get_list(
		"Leave Plan Slot",
		filters=slot_filters,
		fields=["parent", "leave_type", "from_date", "to_date", "days"],
		parent_doctype="Leave Plan",
	)

	cell_acc: dict[tuple, dict] = {}
	for slot in slots:
		emp_id = plan_to_emp.get(slot.parent)
		if not emp_id:
			continue
		dept = emp_by_name[emp_id].department
		s_from = max(getdate(slot.from_date), week_start)
		s_to = min(getdate(slot.to_date), week_end)
		if s_from > s_to:
			continue

		for week_label, week_from, week_to in _week_buckets(s_from, s_to):
			day_count = _working_days(emp_by_name[emp_id], week_from, week_to)
			if day_count <= 0:
				continue
			key = (dept, week_label)
			c = cell_acc.setdefault(key, {
				"department": dept,
				"week": week_label,
				"absent_days": 0.0,
				"absent_employee_set": set(),
				"headcount": headcount.get(dept, 0),
			})
			c["absent_days"] += day_count
			c["absent_employee_set"].add(emp_id)

	cells = []
	for c in cell_acc.values():
		emp_count = len(c["absent_employee_set"])
		hc = c["headcount"]
		cells.append({
			"department": c["department"],
			"week": c["week"],
			"absent_days": flt(c["absent_days"], 2),
			"absent_employees": emp_count,
			"headcount": hc,
			"percent_absent": flt((emp_count / hc * 100) if hc else 0, 1),
		})
	cells.sort(key=lambda x: (x["department"], x["week"]))

	return {
		"weeks": _iso_weeks(week_start, week_end),
		"headcount": headcount,
		"cells": cells,
	}


@frappe.whitelist()
def compliance_roster(
	cycle: str,
	department: str | None = None,
	status_filter: list[str] | str | None = None,
	search: str | None = None,
) -> dict:
	"""Per-cycle compliance roster: who has filed, who hasn't.

	Returns:
	  {
	    cycle: {name, status, deadline, days_remaining},
	    summary: {total, approved, pending, draft, not_started, exempt, percent_*},
	    members: [{employee, employee_name, department, plan_status, plan, ...}],
	  }
	"""
	if not frappe.db.exists("Leave Planning Cycle", cycle):
		frappe.throw(_("Cycle {0} not found").format(cycle))
	status_filter = _normalise_list(status_filter)

	cycle_row = frappe.db.get_value(
		"Leave Planning Cycle", cycle,
		["name", "status", "submission_deadline", "company"],
		as_dict=True,
	)
	days_remaining = (getdate(cycle_row.submission_deadline) - getdate()).days if cycle_row.submission_deadline else None

	filters = {"cycle": cycle}
	if department:
		filters["department"] = department
	if status_filter:
		filters["plan_status"] = ["in", status_filter]

	members = frappe.get_list(
		"Leave Planning Cycle Member",
		filters=filters,
		fields=[
			"name", "employee", "department", "plan", "plan_status",
			"nudges_sent", "last_nudge_at", "exempt", "exempt_reason",
			"leave_approver",
		],
		order_by="department asc, employee asc",
	)

	if search:
		needle = search.lower()
		emp_names = {e.name: e.employee_name for e in frappe.get_list(
			"Employee", filters={"name": ["in", [m.employee for m in members]]},
			fields=["name", "employee_name"],
		)}
		members = [m for m in members if needle in m.employee.lower()
		           or needle in (emp_names.get(m.employee, "") or "").lower()]
	else:
		emp_names = {e.name: e.employee_name for e in frappe.get_list(
			"Employee", filters={"name": ["in", [m.employee for m in members]]},
			fields=["name", "employee_name"],
		)}

	for m in members:
		m["employee_name"] = emp_names.get(m.employee, m.employee)

	total = len(members)
	bucket = {"approved": 0, "pending": 0, "draft": 0, "not_started": 0, "exempt": 0, "cancelled": 0}
	for m in members:
		if m.exempt:
			bucket["exempt"] += 1
		elif m.plan_status == "Approved":
			bucket["approved"] += 1
		elif m.plan_status in ("Pending Manager", "Pending HR", "Returned"):
			bucket["pending"] += 1
		elif m.plan_status == "Draft":
			bucket["draft"] += 1
		elif m.plan_status == "Not Started":
			bucket["not_started"] += 1
		elif m.plan_status == "Cancelled":
			bucket["cancelled"] += 1

	summary = {"total": total, **bucket}
	for k in ("approved", "pending", "draft", "not_started", "exempt"):
		summary[f"percent_{k}"] = flt((bucket[k] / total * 100) if total else 0, 1)

	return {
		"cycle": {
			"name": cycle_row.name,
			"status": cycle_row.status,
			"deadline": str(cycle_row.submission_deadline) if cycle_row.submission_deadline else None,
			"days_remaining": days_remaining,
		},
		"summary": summary,
		"members": members,
	}


def _normalise_list(value) -> list:
	if value is None:
		return []
	if isinstance(value, str):
		import json
		try:
			parsed = json.loads(value)
			if isinstance(parsed, list):
				return parsed
		except (ValueError, TypeError):
			pass
		return [value] if value else []
	if isinstance(value, list):
		return value
	return []


def _resolve_period(leave_period: str | None, company: str):
	if leave_period:
		row = frappe.db.get_value("Leave Period", leave_period, ["from_date", "to_date"], as_dict=True)
		if row:
			return row
	row = frappe.db.sql(
		"""
		SELECT from_date, to_date FROM `tabLeave Period`
		WHERE company = %s AND is_active = 1
		ORDER BY from_date DESC LIMIT 1
		""",
		(company,),
		as_dict=True,
	)
	if row:
		return row[0]
	today = date.today()
	return frappe._dict(from_date=date(today.year, 1, 1), to_date=date(today.year, 12, 31))


def _resolve_window(start_week, end_week, period):
	def week_to_date(s):
		try:
			y, w = s.split("-W")
			return date.fromisocalendar(int(y), int(w), 1)
		except (ValueError, AttributeError):
			return None

	start = week_to_date(start_week) if start_week else getdate(period.from_date)
	end = week_to_date(end_week) if end_week else getdate(period.to_date)
	if end < start:
		end = start + timedelta(days=6)
	return start, end


def _viewable_departments(company: str, department: str | None) -> list[str]:
	user = frappe.session.user
	user_roles = set(frappe.get_roles(user))
	is_hr = bool(user_roles & HR_BACKOFFICE_ROLES) or user == "Administrator"

	if is_hr:
		all_depts = frappe.get_all("Department", filters={"company": company}, pluck="name")
		if department:
			return [department] if department in all_depts else []
		return all_depts

	emp_dept = frappe.db.get_value(
		"Employee", {"user_id": user, "company": company}, "department",
	)
	if not emp_dept:
		return []
	if department and department != emp_dept:
		return []
	return [emp_dept]


def _iso_weeks(start: date, end: date) -> list[str]:
	out = []
	cursor = start - timedelta(days=start.weekday())
	while cursor <= end:
		y, w, _ = cursor.isocalendar()
		out.append(f"{y}-W{w:02d}")
		cursor += timedelta(days=7)
	return out


def _week_buckets(start: date, end: date):
	cursor = start
	while cursor <= end:
		monday = cursor - timedelta(days=cursor.weekday())
		sunday = monday + timedelta(days=6)
		bucket_end = min(end, sunday)
		y, w, _ = monday.isocalendar()
		yield f"{y}-W{w:02d}", cursor, bucket_end
		cursor = bucket_end + timedelta(days=1)


def _working_days(employee, from_date: date, to_date: date) -> int:
	from hrms.hr.utils import get_holidays_for_employee
	holidays = get_holidays_for_employee(employee.name, from_date, to_date) or []
	holiday_dates = {getdate(h["holiday_date"]) for h in holidays}
	total = (to_date - from_date).days + 1
	return sum(
		1 for i in range(total)
		if (from_date + timedelta(days=i)) not in holiday_dates
	)
