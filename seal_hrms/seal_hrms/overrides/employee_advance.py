# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import add_years, add_days, cint, get_link_to_form, getdate, flt, nowdate, now_datetime, nowtime, today, time_diff_in_hours
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.payment_entry.payment_entry import (
	PaymentEntry,
	get_bank_cash_account,
	get_reference_details,
)
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_employee_currency

def validate(doc, method=None):
	max_advance_days, block_new_advances = frappe.db.get_value("Company", doc.company, ["custom_max_advance_days", "custom_block_new_advances"])

	if block_new_advances:
		advances =  frappe.get_list(
			"Employee Advance",
			fields=["*"],
			filters=[
				["docstatus", "=", '1'],
				["employee", "=", doc.employee],
				["status", "in", ['Paid','Partly Claimed and Returned'] ],
				#["advance_amount", "=", "claimed_amount"], #Sanity check: Don't rely on status only
				["posting_date", "<=", add_days(today(), -max_advance_days)]
			]
		)

		if advances:
			advances_info = ""
			for advance in advances:
				link = get_link_to_form("Employee Advance", advance.name)
				advances_info += f"\n- {link}"

			employee = frappe.db.get_value("Employee", doc.employee, ["first_name", "last_name"], as_dict=1)
			frappe.throw(
				_(f"<b>{employee.first_name} {employee.last_name}</b> has {len(advances)} Unclaimed Advances that are <b>older than {max_advance_days} day(s)</b>. Make sure to claim outstanding advances before requesting a new advance.\n{advances_info}")
			)


#TODO Test this function
@frappe.whitelist()
def recover_overdue_advances():
	companies = frappe.get_list("Company", fields=["name","custom_max_advance_days", "custom_auto_recover_advances_from_salary", "custom_salary_component_for_recovery"])

	for company in companies:
		auto_recover_advances_from_salary = company.custom_auto_recover_advances_from_salary 
		salary_component_for_recovery = company.custom_salary_component_for_recovery
		max_advance_days = company.custom_max_advance_days

		if auto_recover_advances_from_salary == 0:
			continue

		if not salary_component_for_recovery:
			frappe.log_error(f"Cannot create Additional Salary (Deduction) to recover Employee Advances because Salary Component for Advance Recovery in Company Settings for {company.name} has not been set.", "Overdue Employee Advance Recovery")
			continue

		#get list of advances in company where status is Paid and posting date is older than max_advance_days
		advances =  frappe.get_list("Employee Advance", fields=["*"], filters=[["company", "=", company.name], ["docstatus", "=", '1'], ["status", "=", 'Paid'], ["posting_date", "<", add_days(today(), -max_advance_days)]])

		if advances:
			for advance in advances:
				if not frappe.db.exists("Salary Structure Assignment", {"employee": advance.employee}):
					frappe.log_error(f"Cannot create Additional Salary (Deduction) to recover {advance.name} for {advance.employee} in {advance.company} because there is no Salary Structure assigned.")
					continue
				
				additional_salary = frappe.db.exists({"doctype": "Additional Salary", "company": advance.company, "ref_doctype": "Employee Advance", "ref_docname": advance.name})

				if not additional_salary:
					additional_salary = frappe.new_doc("Additional Salary")

					additional_salary.employee = advance.employee
					additional_salary.company = advance.company
					additional_salary.is_recurring = 0
					additional_salary.salary_component = salary_component_for_recovery
					additional_salary.amount = advance.advance_amount
					additional_salary.currency = get_employee_currency(advance.employee);
					additional_salary.ref_doctype = "Employee Advance"
					additional_salary.ref_docname = advance.name
					additional_salary.payroll_date = add_days(advance.posting_date, max_advance_days)
					additional_salary.posting_date = today()

					additional_salary.insert()
					additional_salary.submit()


@frappe.whitelist()
def get_expense_claim(
	dt, dn, claim_type, employee_name, company, employee_advance_name, posting_date, paid_amount, claimed_amount, expense_items 
):
	doc = frappe.get_doc(dt, dn)

	default_payable_account = frappe.get_value(
		"Company", company, "default_expense_claim_payable_account"
	)
	#default_cost_center = frappe.get_value("Company", company, "cost_center")

	expense_claim = frappe.new_doc("Expense Claim")
	expense_claim.company = company
	expense_claim.employee = employee_name
	expense_claim.department = doc.department
	expense_claim.cost_center = doc.custom_cost_center
	expense_claim.project = doc.custom_project
	expense_claim.payable_account = default_payable_account
	expense_claim.custom_claim_type = claim_type

	if doc.mode_of_payment:
		expense_claim.mode_of_payment = doc.mode_of_payment
	else:
		default_mop = frappe.get_value('Company', company,
				'custom_default_expense_claim_mode_of_payment')
		if default_mop:
			expense_claim.mode_of_payment = default_mop

	expense_claim.is_paid = 1 if flt(paid_amount) else 0

	expense_claim.append(
		"advances",
		{
			"employee_advance": employee_advance_name,
			"posting_date": posting_date,
			"advance_paid": flt(paid_amount),
			"unclaimed_amount": flt(paid_amount) - flt(claimed_amount),
			"allocated_amount": flt(paid_amount) - flt(claimed_amount),
		},
	) 

	expense_claim_details = json.loads(expense_items)

	for item in expense_claim_details: 
		expense_claim.append(
			"expenses",
			{
			"expense_date": item['expense_date'] if 'expense_date' in item else None,
			"expense_type": item['expense_type'],
			"description": item['description'] if 'description' in item else None,
			"amount": item['amount'], 
			"cost_center": item['cost_center'] if 'cost_center' in item else None,
			"project": item['project'] if 'project' in item else None,
			"sanctioned_amount": item['sanctioned_amount'] if 'sanctioned_amount' in item else None,

			"custom_receipt_amount": item['amount'],
			"custom_receipt_date": item['expense_date'],   
			},				  
		)

	return expense_claim

@frappe.whitelist()
def get_payment_entry_for_employee(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	"""Function to make Payment Entry for Employee Advance, Gratuity, Expense Claim"""
	doc = frappe.get_doc(dt, dn)

	party_account = get_party_account(doc)
	party_account_currency = get_account_currency(party_account)
	payment_type = "Pay"
	grand_total, outstanding_amount = get_grand_total_and_outstanding_amount(
		doc, party_amount, party_account_currency
	)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = get_paid_amount_and_received_amount(
		doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
	)

	#TODO Find a way to set the title to Employee Name
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = "Employee"
	pe.party = doc.get("employee")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.letter_head = doc.get("letter_head")
	pe.paid_from = bank.account
	pe.paid_to = party_account
	pe.paid_from_account_currency = bank.account_currency
	pe.paid_to_account_currency = party_account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.project =  doc.custom_project
	pe.cost_center = doc.custom_cost_center

	# if (doc.custom_direct_payment):
	pe.custom_third_party_payee = 1
	pe.custom_payee_type = doc.custom_payee_type
	pe.custom_account_name = doc.custom_account_name
	pe.custom_account_no = doc.custom_account_no
	pe.custom_payment_method = doc.custom_payment_method

	pe.custom_remarks = 1
	pe.remarks = doc.purpose

	pe.append(
		"references",
		{
			"reference_doctype": dt,
			"reference_name": dn,
			"bill_no": doc.get("bill_no"),
			"due_date": doc.get("due_date"),
			"total_amount": grand_total,
			"outstanding_amount": outstanding_amount,
			"allocated_amount": outstanding_amount,
		},
	)

	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.set_missing_ref_details()

	if party_account and bank:
		reference_doc = None
		if dt == "Employee Advance":
			reference_doc = doc
		pe.set_exchange_rate(ref_doc=reference_doc)
		pe.set_amounts()

	return pe


def get_party_account(doc):
	party_account = None

	if doc.doctype == "Employee Advance":
		party_account = doc.advance_account
	elif doc.doctype in ("Expense Claim", "Gratuity"):
		party_account = doc.payable_account

	return party_account


def get_grand_total_and_outstanding_amount(doc, party_amount, party_account_currency):
	grand_total = outstanding_amount = 0

	if party_amount:
		grand_total = outstanding_amount = party_amount

	elif doc.doctype == "Expense Claim":
		grand_total = flt(doc.total_sanctioned_amount) + flt(doc.total_taxes_and_charges)
		outstanding_amount = flt(doc.grand_total) - flt(doc.total_amount_reimbursed)

	elif doc.doctype == "Employee Advance":
		grand_total = flt(doc.advance_amount)
		outstanding_amount = flt(doc.advance_amount) - flt(doc.paid_amount)
		if party_account_currency != doc.currency:
			grand_total = flt(doc.advance_amount) * flt(doc.exchange_rate)
			outstanding_amount = (flt(doc.advance_amount) - flt(doc.paid_amount)) * flt(doc.exchange_rate)

	elif doc.doctype == "Gratuity":
		grand_total = doc.amount
		outstanding_amount = flt(doc.amount) - flt(doc.paid_amount)

	else:
		if party_account_currency == doc.company_currency:
			grand_total = flt(doc.get("base_rounded_total") or doc.base_grand_total)
		else:
			grand_total = flt(doc.get("rounded_total") or doc.grand_total)
		outstanding_amount = grand_total - flt(doc.advance_paid)

	return grand_total, outstanding_amount


def get_paid_amount_and_received_amount(
	doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
):
	paid_amount = received_amount = 0

	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)

	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get("conversion_rate", 1)
			if doc.doctype == "Employee Advance":
				received_amount = paid_amount * doc.get("exchange_rate", 1)

	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			paid_amount = received_amount * doc.get("conversion_rate", 1)
			if doc.doctype == "Employee Advance":
				paid_amount = received_amount * doc.get("exchange_rate", 1)

	return paid_amount, received_amount