# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Expense Requisition Status — lifecycle + ageing of staff requisitions.

One row per submitted requisition: requested / approved / disbursed / surrendered / returned /
outstanding-to-account-for, plus the age since posting. Finance uses it to chase un-accounted
disbursements (Disbursed/Surrendered with an outstanding balance).
"""

import frappe
from frappe import _
from frappe.utils import date_diff, flt, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Requisition"), "fieldname": "name", "fieldtype": "Link", "options": "Expense Requisition", "width": 150},
		{"label": _("Employee"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 130},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 130},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Requested"), "fieldname": "total_requested", "fieldtype": "Currency", "options": "currency", "width": 110},
		{"label": _("Approved"), "fieldname": "approved_amount", "fieldtype": "Currency", "options": "currency", "width": 110},
		{"label": _("Disbursed"), "fieldname": "disbursed_amount", "fieldtype": "Currency", "options": "currency", "width": 110},
		{"label": _("Surrendered"), "fieldname": "surrendered_amount", "fieldtype": "Currency", "options": "currency", "width": 110},
		{"label": _("Returned"), "fieldname": "returned_amount", "fieldtype": "Currency", "options": "currency", "width": 100},
		{"label": _("Outstanding"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "options": "currency", "width": 120},
		{"label": _("Age (days)"), "fieldname": "age", "fieldtype": "Int", "width": 90},
		{"label": _("Currency"), "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
	]


def get_data(filters):
	conditions = {"docstatus": 1}
	if filters.get("company"):
		conditions["company"] = filters.company
	if filters.get("status"):
		conditions["status"] = filters.status
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	if filters.get("from_date") and filters.get("to_date"):
		conditions["posting_date"] = ["between", [filters.from_date, filters.to_date]]
	if filters.get("only_outstanding"):
		conditions["outstanding_amount"] = [">", 0]

	rows = frappe.get_all(
		"Expense Requisition",
		filters=conditions,
		fields=[
			"name", "employee_name", "department", "company", "posting_date", "status",
			"total_requested", "approved_amount", "disbursed_amount", "surrendered_amount",
			"returned_amount", "outstanding_amount", "currency",
		],
		order_by="posting_date asc, name asc",
	)
	for r in rows:
		r["age"] = date_diff(today(), r["posting_date"]) if r.get("posting_date") else 0
	return rows
