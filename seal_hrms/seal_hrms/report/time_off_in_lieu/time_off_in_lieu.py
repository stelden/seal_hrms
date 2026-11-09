# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Time off in lieu, per person: earned, used, lapsed unused, left, and what lapses soon.

Read from approved claims, whose figures `toil.lapse.reconcile` keeps current
(on every approval, cancellation and leave, and daily). Rows come through
`frappe.get_list`, so an approver sees their own staff and HR sees everyone,
by the same rules as the claims themselves.
"""

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

SOON_DAYS = 30


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
			"width": 130,
		},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Earned (days)"), "fieldname": "earned", "fieldtype": "Float", "width": 110},
		{"label": _("Used"), "fieldname": "used", "fieldtype": "Float", "width": 90},
		{"label": _("Lapsed Unused"), "fieldname": "lapsed", "fieldtype": "Float", "width": 120},
		{"label": _("Left"), "fieldname": "left", "fieldtype": "Float", "width": 90},
		{
			"label": _("Lapsing in {0} Days").format(SOON_DAYS),
			"fieldname": "lapsing_soon",
			"fieldtype": "Float",
			"width": 140,
		},
		{"label": _("Next Lapse"), "fieldname": "next_lapse", "fieldtype": "Date", "width": 110},
	]


def _rows(filters):
	conditions = [["docstatus", "=", 1], ["status", "=", "Approved"]]
	if filters.company:
		conditions.append(["company", "=", filters.company])
	if filters.employee:
		conditions.append(["employee", "=", filters.employee])
	claims = frappe.get_list(
		"Time Off in Lieu Claim",
		filters=conditions,
		fields=[
			"employee",
			"employee_name",
			"days_credited",
			"days_used",
			"days_lapsed",
			"days_left",
			"lapses_on",
		],
	)
	day, soon = getdate(today()), getdate(add_days(today(), SOON_DAYS))
	people = {}
	for claim in claims:
		row = people.setdefault(
			claim.employee,
			frappe._dict(
				employee=claim.employee,
				employee_name=claim.employee_name,
				earned=0.0,
				used=0.0,
				lapsed=0.0,
				left=0.0,
				lapsing_soon=0.0,
				next_lapse=None,
			),
		)
		row.earned += flt(claim.days_credited)
		row.used += flt(claim.days_used)
		row.lapsed += flt(claim.days_lapsed)
		row.left += flt(claim.days_left)
		lapses_on = getdate(claim.lapses_on) if claim.lapses_on else None
		if flt(claim.days_left) and lapses_on and lapses_on >= day:
			if lapses_on <= soon:
				row.lapsing_soon += flt(claim.days_left)
			if not row.next_lapse or lapses_on < row.next_lapse:
				row.next_lapse = lapses_on
	rows = sorted(
		people.values(), key=lambda r: (r.next_lapse or getdate("2999-12-31"), r.employee_name or "")
	)
	if filters.only_with_time_left:
		rows = [r for r in rows if r.left]
	for r in rows:
		for key in ("earned", "used", "lapsed", "left", "lapsing_soon"):
			r[key] = round(r[key], 2)
	return rows
