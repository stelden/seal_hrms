# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""People covering for colleagues, and how many at once.

A stand-in covering one person is ordinary. Covering three at once, on top of
their own work, is where things get dropped, and nobody sees it from any single
handover. "At Once" is the most colleagues this person covers on any one day in
the period.
"""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return _columns(), _rows(filters)


def _columns():
	return [
		{"label": _("Stand-in"), "fieldname": "stand_in", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Name"), "fieldname": "stand_in_name", "fieldtype": "Data", "width": 180},
		{"label": _("People Covered"), "fieldname": "people", "fieldtype": "Int", "width": 120},
		{"label": _("At Once"), "fieldname": "at_once", "fieldtype": "Int", "width": 90},
		{"label": _("Tasks"), "fieldname": "tasks", "fieldtype": "Int", "width": 80},
		{"label": _("Approvals"), "fieldname": "approvals", "fieldtype": "Int", "width": 90},
		{"label": _("Covering For"), "fieldname": "covering_for", "fieldtype": "Data", "width": 300},
	]


def _rows(filters):
	start = getdate(filters.from_date or today())
	end = getdate(filters.to_date or add_days(start, 30))
	conditions = [["docstatus", "=", 1], ["status", "in", ["Accepted", "Active", "Awaiting Acceptance"]],
	              ["leave_from", "<=", end], ["leave_to", ">=", start]]
	if filters.company:
		conditions.append(["company", "=", filters.company])
	load = {}
	for name in frappe.get_all("Task Assignment", filters=conditions, pluck="name"):
		doc = frappe.get_doc("Task Assignment", name)
		window = (max(getdate(doc.leave_from), start), min(getdate(doc.leave_to), end))
		covering = {doc.task_assignee} if doc.task_assignee else set()
		for row in [*doc.assignment_todos, *doc.get("authorities")]:
			covering.add(row.task_assignee or doc.task_assignee)
		covering.discard(None)
		for stand_in in covering:
			entry = load.setdefault(stand_in, {"people": {}, "tasks": 0, "approvals": 0})
			entry["people"][doc.employee_name] = window
			entry["tasks"] += sum(1 for r in doc.assignment_todos if (r.task_assignee or doc.task_assignee) == stand_in)
			entry["approvals"] += sum(1 for r in doc.get("authorities") if (r.task_assignee or doc.task_assignee) == stand_in)
	rows = []
	for stand_in, entry in load.items():
		rows.append({
			"stand_in": stand_in,
			"stand_in_name": frappe.db.get_value("Employee", stand_in, "employee_name"),
			"people": len(entry["people"]),
			"at_once": _most_at_once(list(entry["people"].values())),
			"tasks": entry["tasks"],
			"approvals": entry["approvals"],
			"covering_for": ", ".join(sorted(entry["people"])),
		})
	rows.sort(key=lambda r: (-r["at_once"], -r["people"], r["stand_in_name"] or ""))
	return rows


def _most_at_once(windows) -> int:
	"""The most windows that overlap on any single day."""
	best = 0
	for day_start, _day_end in windows:
		best = max(best, sum(1 for s, e in windows if s <= day_start <= e))
	return best
