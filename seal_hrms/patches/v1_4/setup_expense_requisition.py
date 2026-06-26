# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Scaffolding for the Expense Requisition doctype — additive, idempotent.

1. Company custom field `custom_staff_requisition_payable_account` — the payable the requisition
   credits when it books the accrual (Dr Expense / Cr Staff Expense Payable) at approval.
2. A `Staff Expense Payable` leaf account per company (under Accounts Payable) if missing, and
   point the field at it.

Companies that already carry the field/account are left untouched.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

PAYABLE_ACCOUNT_NAME = "Staff Expense Payable"
FIELD = "custom_staff_requisition_payable_account"


def execute():
	create_custom_fields(
		{
			"Company": [
				{
					"fieldname": FIELD,
					"label": "Staff Requisition Payable Account",
					"fieldtype": "Link",
					"options": "Account",
					"insert_after": "default_employee_advance_account",
					"description": "Payable credited when an Expense Requisition books its accrual "
					"(Dr Expense / Cr Staff Expense Payable) at approval.",
				},
			],
		},
		ignore_validate=True,
	)

	created = 0
	for company in frappe.get_all("Company", pluck="name"):
		if frappe.get_cached_value("Company", company, FIELD):
			continue
		abbr = frappe.get_cached_value("Company", company, "abbr")
		acc_name = f"{PAYABLE_ACCOUNT_NAME} - {abbr}"
		if not frappe.db.exists("Account", acc_name):
			parent = frappe.db.get_value(
				"Account", {"company": company, "account_name": "Accounts Payable", "is_group": 1}
			)
			if not parent:
				continue
			acc = frappe.new_doc("Account")
			acc.account_name = PAYABLE_ACCOUNT_NAME
			acc.company = company
			acc.parent_account = parent
			acc.account_type = "Payable"
			acc.account_currency = frappe.get_cached_value("Company", company, "default_currency")
			acc.insert(ignore_permissions=True)
			created += 1
		frappe.db.set_value("Company", company, FIELD, acc_name, update_modified=False)

	frappe.clear_cache()
	print(f"[setup_expense_requisition] field ready; {created} Staff Expense Payable account(s) created")
