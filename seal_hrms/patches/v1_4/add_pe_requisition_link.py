# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Add the Payment Entry → Expense Requisition link used by disbursement-recognition. Idempotent."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Payment Entry": [
				{
					"fieldname": "custom_requisition",
					"label": "Expense Requisition",
					"fieldtype": "Link",
					"options": "Expense Requisition",
					"insert_after": "cost_center",
					"read_only": 1,
					"no_copy": 1,
					"print_hide": 1,
					"description": "The Expense Requisition this payment disburses (recognises its expense on submit).",
				}
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Payment Entry")
