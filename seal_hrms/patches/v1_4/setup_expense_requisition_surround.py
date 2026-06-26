# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Surround for Expense Requisition — Number Cards + a print format. Idempotent.

Number Cards are created with is_standard=0 (a standard card throws "Cannot edit Standard" on
import outside developer mode). The print format is a custom Jinja format.
"""

import frappe

DT = "Expense Requisition"

NUMBER_CARDS = [
	{
		"name": "Requisitions Awaiting Disbursement",
		"label": "Requisitions Awaiting Disbursement",
		"function": "Count",
		"filters_json": '[["Expense Requisition","status","=","Approved"]]',
		"color": "#2490ef",
	},
	{
		"name": "Requisitions Disbursed (Open)",
		"label": "Requisitions Disbursed (Open)",
		"function": "Count",
		"filters_json": '[["Expense Requisition","status","in",["Disbursed","Surrendered"]]]',
		"color": "#6e3fd6",
	},
	{
		"name": "Requisition Outstanding to Account For",
		"label": "Outstanding to Account For",
		"function": "Sum",
		"aggregate_function_based_on": "outstanding_amount",
		"filters_json": '[["Expense Requisition","outstanding_amount",">",0],["Expense Requisition","docstatus","=",1]]',
		"color": "#cb2929",
	},
	{
		"name": "Requisitions Closed",
		"label": "Requisitions Closed",
		"function": "Count",
		"filters_json": '[["Expense Requisition","status","=","Closed"]]',
		"color": "#28a745",
	},
]


def execute():
	_create_number_cards()
	_create_print_format()
	frappe.clear_cache()


def _create_number_cards():
	for card in NUMBER_CARDS:
		if frappe.db.exists("Number Card", card["name"]):
			continue
		doc = frappe.get_doc({
			"doctype": "Number Card",
			"name": card["name"],
			"label": card["label"],
			"document_type": DT,
			"type": "Document Type",
			"function": card["function"],
			"aggregate_function_based_on": card.get("aggregate_function_based_on"),
			"filters_json": card["filters_json"],
			"is_standard": 0,
			"show_percentage_stats": 1,
			"stats_time_interval": "Daily",
			"color": card.get("color"),
		})
		doc.insert(ignore_permissions=True)


def _create_print_format():
	if frappe.db.exists("Print Format", "Expense Requisition"):
		return
	frappe.get_doc({
		"doctype": "Print Format",
		"name": "Expense Requisition",
		"doc_type": DT,
		"module": "SEAL HRMS",
		"standard": "No",
		"custom_format": 1,
		"print_format_type": "Jinja",
		"html": _PRINT_HTML,
	}).insert(ignore_permissions=True)


_PRINT_HTML = """
<div class="print-heading"><h2>Expense Requisition<br><small>{{ doc.name }}</small></h2></div>
<table class="table table-bordered" style="font-size:12px">
  <tr>
    <td width="25%"><b>{{ _("Employee") }}</b></td><td>{{ doc.employee_name or doc.employee }}</td>
    <td width="25%"><b>{{ _("Posting Date") }}</b></td><td>{{ frappe.utils.formatdate(doc.posting_date) }}</td>
  </tr>
  <tr>
    <td><b>{{ _("Department") }}</b></td><td>{{ doc.department or "" }}</td>
    <td><b>{{ _("Company") }}</b></td><td>{{ doc.company }}</td>
  </tr>
  <tr>
    <td><b>{{ _("Status") }}</b></td><td>{{ doc.status }}</td>
    <td><b>{{ _("Title") }}</b></td><td>{{ doc.title or "" }}</td>
  </tr>
</table>

<table class="table table-bordered" style="font-size:11px">
  <thead><tr>
    <th>#</th><th>{{ _("Expense Type") }}</th><th>{{ _("Description") }}</th>
    <th class="text-right">{{ _("Requested") }}</th><th class="text-right">{{ _("Actual") }}</th>
    <th>{{ _("Cost Center") }}</th><th>{{ _("Funding Source") }}</th>
  </tr></thead>
  <tbody>
  {% for r in doc.items %}
    <tr>
      <td>{{ loop.index }}</td><td>{{ r.expense_type }}</td><td>{{ r.description }}</td>
      <td class="text-right">{{ frappe.utils.fmt_money(r.amount, currency=doc.currency) }}</td>
      <td class="text-right">{{ frappe.utils.fmt_money(r.actual_amount, currency=doc.currency) }}</td>
      <td>{{ r.cost_center or "" }}</td><td>{{ r.funding_source or "" }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>

<table class="table table-bordered" style="font-size:12px;width:50%;float:right">
  <tr><td><b>{{ _("Approved") }}</b></td><td class="text-right">{{ frappe.utils.fmt_money(doc.approved_amount, currency=doc.currency) }}</td></tr>
  <tr><td><b>{{ _("Disbursed") }}</b></td><td class="text-right">{{ frappe.utils.fmt_money(doc.disbursed_amount, currency=doc.currency) }}</td></tr>
  <tr><td><b>{{ _("Surrendered") }}</b></td><td class="text-right">{{ frappe.utils.fmt_money(doc.surrendered_amount, currency=doc.currency) }}</td></tr>
  <tr><td><b>{{ _("Returned") }}</b></td><td class="text-right">{{ frappe.utils.fmt_money(doc.returned_amount, currency=doc.currency) }}</td></tr>
  <tr><td><b>{{ _("Outstanding to Account For") }}</b></td><td class="text-right">{{ frappe.utils.fmt_money(doc.outstanding_amount, currency=doc.currency) }}</td></tr>
</table>
<div style="clear:both"></div>
{% if doc.purpose %}<p style="font-size:12px"><b>{{ _("Purpose") }}:</b> {{ doc.purpose }}</p>{% endif %}
"""
