# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Expense Surrender — liquidate a disbursed Expense Requisition.

Captures the actual spend (receipts) against a requisition and returns any unspent balance in one
step. Under disbursement-recognition the full disbursed amount was booked as expense at
disbursement, so this only needs to REVERSE the over-booked expense for the unspent portion:

    Return unspent:  Dr Bank/Cash  / Cr Expense (proportional to each line's unspent)

so the net expense ends at the actual spend. On submit it also rolls the requisition's
surrendered / returned / outstanding amounts + status forward.
"""

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries


class ExpenseSurrender(AccountsController):
	def validate(self):
		self.conversion_rate = 1
		req = self._requisition()
		if not self.cost_center:
			self.cost_center = req.cost_center
		if not self.company:
			self.company = req.company
		if not self.get("items"):
			self._seed_from_requisition(req)
		self._resolve_line_accounts()
		self.total_disbursed = flt(req.disbursed_amount)
		self.total_actual = flt(sum(flt(ln.actual_amount) for ln in self.get("items")))
		self.amount_to_return = max(flt(self.total_disbursed) - flt(self.total_actual), 0.0)
		self.status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(self.docstatus, "Draft")

	def _requisition(self):
		return frappe.get_doc("Expense Requisition", self.expense_requisition)

	def _seed_from_requisition(self, req):
		for ln in req.get("items"):
			self.append("items", {
				"expense_type": ln.expense_type,
				"description": ln.description,
				"account": ln.account,
				"disbursed_amount": flt(ln.amount),
				"actual_amount": flt(ln.amount),
			})

	def _resolve_line_accounts(self):
		from seal_hrms.seal_hrms.doctype.expense_requisition.expense_requisition import expense_type_account
		for ln in self.get("items"):
			if ln.expense_type and not ln.account:
				ln.account = expense_type_account(ln.expense_type, self.company)

	def before_submit(self):
		req = self._requisition()
		if req.docstatus != 1 or flt(req.disbursed_amount) <= 0:
			frappe.throw(_("The Expense Requisition must be disbursed before it can be surrendered."))
		if flt(self.total_actual) > flt(self.total_disbursed) + 0.01:
			frappe.throw(_("Actual spend ({0}) exceeds the disbursed amount ({1}).").format(
				self.total_actual, self.total_disbursed))
		if flt(self.amount_to_return) > 0.01 and not self.return_bank_account:
			frappe.throw(_("Select the bank/cash account the unspent funds ({0}) are returned to.").format(
				self.amount_to_return))

	def on_submit(self):
		if flt(self.amount_to_return) > 0.01:
			self._post_return_gl()
		self.db_set("status", "Submitted")
		self._requisition().update_amounts(update=True)

	def before_cancel(self):
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry"]

	def on_cancel(self):
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
		self.db_set("status", "Cancelled")
		self._requisition().update_amounts(update=True)

	def _post_return_gl(self):
		"""Dr Bank / Cr Expense for the unspent amount, allocated by each line's unspent share."""
		from erpnext.accounts.utils import get_account_currency

		amount = flt(self.amount_to_return)
		lines = [ln for ln in self.get("items") if flt(ln.disbursed_amount) - flt(ln.actual_amount) > 0]
		total_unspent = sum(flt(ln.disbursed_amount) - flt(ln.actual_amount) for ln in lines) or 1
		gl, remaining = [], amount
		for i, ln in enumerate(lines):
			share = flt(ln.disbursed_amount) - flt(ln.actual_amount)
			amt = round(remaining, 2) if i == len(lines) - 1 else round(amount * share / total_unspent, 2)
			remaining = round(remaining - amt, 2)
			if amt <= 0:
				continue
			gl.append(self.get_gl_dict({
				"account": ln.account,
				"credit": amt,
				"credit_in_account_currency": amt,
				"cost_center": self.cost_center,
				"against": self.return_bank_account,
			}, item=ln))
		gl.append(self.get_gl_dict({
			"account": self.return_bank_account,
			"debit": amount,
			"debit_in_account_currency": amount,
			"cost_center": self.cost_center,
			"against": self.employee,
		}, account_currency=get_account_currency(self.return_bank_account), item=self))
		make_gl_entries(gl, update_outstanding="No", merge_entries=False)
