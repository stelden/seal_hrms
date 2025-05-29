# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils import add_years, add_days, cint, get_link_to_form, getdate, flt, nowdate, now_datetime, nowtime, today, time_diff_in_hours

class BatchEmployeeAdvance(Document):
	def before_save(self):
		validate_distribution(self)
		validate_outstanding_advances(self)

	def on_submit(self):
		# Fetch company settings
		auto_recover_advances_from_salary, default_currency = frappe.db.get_value(
			"Company", self.company, 
			["custom_auto_recover_advances_from_salary", "default_currency"]
		)

		expense_count = len(self.get("expenses"))

		# Start a transaction to ensure all-or-nothing execution
		#try:
			#frappe.db.transaction()
			
		# Create Employee Advance for each employee
		for row in self.get('employees'):
			advance = frappe.new_doc("Employee Advance")
			advance.employee = row.employee
			advance.custom_advance_type = "Imprest"
			advance.posting_date = today()
			advance.company = self.company
			advance.custom_cost_center = self.cost_center or None
			advance.custom_project = self.project or None
			advance.purpose = self.purpose or "Advance for employee"
			advance.advance_account = self.advance_account
			advance.mode_of_payment = self.mode_of_payment
			advance.repay_unclaimed_amount_from_salary = auto_recover_advances_from_salary
			advance.currency = default_currency
			advance.exchange_rate = 1  # Update if exchange rate calculation is required

			advance.custom_direct_disbursement = 1
			
			advance.custom_payee_type = 'Employee'
			advance.custom_payee = row.employee
			
			advance.custom_account_name = row.account_name
			advance.custom_account_no = row.account_no
			advance.custom_account_provider = row.account_provider

			advance.advance_amount = row.amount
			advance.sanctioned_amount = row.amount

			advance.custom_batch_employee_advance = self.name

			purpose = f"From Batch {self.name}\n"
			# Add expense details
			for expense in self.get("expenses"):
				if not all([expense.expense_date, expense.expense_type, expense.description, expense.amount]):
					frappe.throw("All expense details (date, type, description, amount) must be provided.")
				
				advance.append("custom_expenses", {
					"expense_date": expense.expense_date,
					"expense_type": expense.expense_type,
					"description": expense.description,
					"amount": row.amount / expense_count, # Distribute expense amount equally regardless of original amounts
					"sanctioned_amount": row.amount / expense_count,
					"cost_center": expense.cost_center or self.cost_center,
					"project": expense.project or self.project,
				})
				purpose += f"\n- {expense.expense_type}: {expense.description} ({row.amount / expense_count:.2f})"
			
			advance.purpose = purpose
			# Save the Employee Advance document
			advance.submit()

	def on_cancel(self):
		# Cancel all Employee Advances created by this Bulk Employee Advance
		advances = frappe.get_list(
			"Employee Advance",
			filters={"custom_batch_employee_advance": self.name},
			fields=["name"]
		)

		for advance in advances:
			advance = frappe.get_doc("Employee Advance", advance.name)
			advance.cancel()

		# Commit the transaction
		frappe.db.commit()

def validate_distribution(self):
	# Calculate total advance amount
	total_advance_amount = sum(row.amount for row in self.get('expenses'))
	self.total_advance_amount = total_advance_amount

	# Validate and distribute advance amounts equally, if applicable
	employees = self.get('employees')
	total_employees = len(employees)

	if total_employees == 0:
		frappe.throw("No employees available for disbursement.")

	total_disbursement_amount = 0

	if self.distribute_equally:
		for row in employees:
			row.amount = flt(total_advance_amount) / total_employees
			total_disbursement_amount += row.amount
	else:
		no_amount_specified = []
		for row in employees:
			if not row.amount:
				no_amount_specified.append(row.account_name)
				
		if no_amount_specified:
			frappe.throw(
				f"Amount must be specified for the following: {', '.join(no_amount_specified)}"
			)
		else:
			total_disbursement_amount = sum(row.amount for row in employees)

	self.total_disbursement_amount = total_disbursement_amount

	# Validate equality of advance and disbursement amounts
	if not flt(self.total_advance_amount) == flt(self.total_disbursement_amount):
		frappe.throw(
			f"Total Advance Amount ({self.total_advance_amount}) must be equal to "
			f"Total Disbursement Amount ({self.total_disbursement_amount})."
		)

def validate_outstanding_advances(self):
	max_advance_days, block_new_advances = frappe.db.get_value(
		"Company", 
		self.company, 
		["custom_max_advance_days", "custom_block_new_advances"]
	)
	
	if block_new_advances:
		outstanding_advances = []
		outstanding_advance_info = []

		for employee in self.get('employees'):
			# Initialize amount for the current employee
			amount = 0

			advances = frappe.get_list(
				"Employee Advance",
				fields=["advance_amount", "claimed_amount"],
				filters=[
					["docstatus", "=", 1],
					["employee", "=", employee],
					["status", "in", ["Paid", "Partly Claimed and Returned"]],
					["posting_date", "<=", add_days(today(), -max_advance_days)]
				]
			)

			if advances:
				outstanding_advances.append(employee)
				for advance in advances:
					amount += advance.advance_amount

				outstanding_advance_info.append(f"\n- <b>{employee}</b>: {amount}")

		if outstanding_advances:
			advances_info = ''.join(outstanding_advance_info)
			frappe.throw(
				f"The following recipients have unclaimed advances that are "
				f"older than <b>{max_advance_days} day(s)</b>: {advances_info}"
			)
