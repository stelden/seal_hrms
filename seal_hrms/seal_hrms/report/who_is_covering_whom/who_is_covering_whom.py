# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Who is away, or about to be, and who is carrying their work.

One row per handover whose leave overlaps the dates asked for. The answer an HR
officer needs is who is covering and whether they agreed, so a handover still
waiting or declined sorts first: that is the leave with nobody behind it.
"""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today

_ORDER = {"Declined": 0, "Awaiting Acceptance": 1, "Accepted": 2, "Active": 3, "Handed Back": 4}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return _columns(), _rows(filters)


def _columns():
	return [
		{"label": _("Handover"), "fieldname": "name", "fieldtype": "Link", "options": "Task Assignment", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
		{"label": _("Away"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("From"), "fieldname": "leave_from", "fieldtype": "Date", "width": 100},
		{"label": _("Back"), "fieldname": "return_date", "fieldtype": "Date", "width": 100},
		{"label": _("Stand-in"), "fieldname": "task_assignee_name", "fieldtype": "Data", "width": 170},
		{"label": _("Others Covering"), "fieldname": "others", "fieldtype": "Data", "width": 200},
		{"label": _("Tasks"), "fieldname": "tasks", "fieldtype": "Int", "width": 70},
		{"label": _("Approvals Handed Over"), "fieldname": "approvals", "fieldtype": "Data", "width": 220},
	]


def _rows(filters):
	start = getdate(filters.from_date or today())
	end = getdate(filters.to_date or add_days(start, 30))
	conditions = [["docstatus", "=", 1], ["status", "in", list(_ORDER)],
	              ["leave_from", "<=", end], ["leave_to", ">=", start]]
	if filters.company:
		conditions.append(["company", "=", filters.company])
	if filters.status:
		conditions.append(["status", "=", filters.status])
	names = frappe.get_all("Task Assignment", filters=conditions, pluck="name")
	rows = []
	for name in names:
		doc = frappe.get_doc("Task Assignment", name)
		others = sorted({
			frappe.db.get_value("Employee", r.task_assignee, "employee_name") or r.task_assignee
			for r in [*doc.assignment_todos, *doc.get("authorities")]
			if r.task_assignee and r.task_assignee != doc.task_assignee
		})
		rows.append({
			"name": doc.name, "status": _(doc.status), "employee_name": doc.employee_name,
			"department": doc.department, "leave_from": doc.leave_from, "return_date": doc.return_date,
			"task_assignee_name": doc.task_assignee_name, "others": ", ".join(others),
			"tasks": len(doc.assignment_todos),
			"approvals": ", ".join(
				f"{r.authority_label or r.authority} ({_(r.acceptance or 'Pending')})" for r in doc.get("authorities")
			),
			"_order": (_ORDER.get(doc.status, 9), str(doc.leave_from)),
		})
	rows.sort(key=lambda r: r.pop("_order"))
	return rows
