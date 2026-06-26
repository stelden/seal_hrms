# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Expense Requisition — staff request funds to execute a task, on the accrual model.

Lifecycle (recognise expense at approval):
    Approve (submit):  Dr Expense (per line) / Cr Staff Expense Payable (party=Employee)
    Disburse:          Dr Staff Expense Payable / Cr Bank   (Payment Entry references this doc)
    Surrender:         account for actual spend with receipts (Expense Claim); true-up any variance
    Return:            push unspent funds back (Payment Entry Receive) + reverse the unspent expense
    Cancel:            reverse the GL (the requisition owns its ledger — no orphan JV)

The requisition IS the accounting voucher: it subclasses AccountsController and posts GL directly
via erpnext.accounts.general_ledger.make_gl_entries, with the payable leg carrying
against_voucher = this document, so a Payment Entry can settle it natively (registered as an
`invoice_doctype`, never an advance doctype — that asymmetry is what broke Employee Advance).
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

# Company custom field (added by seal_hrms setup patch) naming the payable the requisition credits.
PAYABLE_ACCOUNT_FIELD = "custom_staff_requisition_payable_account"


class ExpenseRequisition(AccountsController):
	# ------------------------------------------------------------------ validate
	def validate(self):
		# Deliberately NOT calling AccountsController.validate() — its invoice-shaped machinery
		# (taxes, item rates, etc.) does not apply. We set only what get_gl_dict / GL posting need.
		self._set_defaults()
		self._resolve_line_accounts()
		self._compute_total()
		self.set_status()

	def _set_defaults(self):
		if not self.posting_date:
			self.posting_date = nowdate()
		if not self.currency:
			self.currency = frappe.get_cached_value("Company", self.company, "default_currency")
		# Single-currency for now; the payable + bank are company-currency accounts.
		self.conversion_rate = 1
		if not self.payable_account:
			self.payable_account = staff_payable_account(self.company)
		# Propagate header dimensions to any line that left them blank.
		for ln in self.get("items"):
			ln.cost_center = ln.cost_center or self.cost_center
			ln.project = ln.project or self.project
			ln.funding_source = ln.funding_source or self.funding_source

	def _resolve_line_accounts(self):
		"""Each line's expense account comes from the Expense Claim Type's per-company default."""
		for ln in self.get("items"):
			if ln.expense_type and not ln.account:
				ln.account = expense_type_account(ln.expense_type, self.company)

	def _compute_total(self):
		self.total_requested = flt(sum(flt(ln.amount) for ln in self.get("items")))

	# ------------------------------------------------------------------ submit / cancel
	def before_submit(self):
		"""Approval gate: the requisition must be fully costed before it books the accrual."""
		if not self.payable_account:
			frappe.throw(_("No Staff Expense Payable account configured for {0}. Set it in Seal HRMS Settings / Company.").format(self.company))
		if flt(self.total_requested) <= 0:
			frappe.throw(_("Add at least one requisition line with an amount before approving."))
		for ln in self.get("items"):
			if not ln.account:
				frappe.throw(_("Row {0}: no expense account — set a default account on Expense Claim Type {1} for {2}.").format(
					ln.idx, ln.expense_type, self.company))

	def on_submit(self):
		"""Approved → recognise the expense (accrual)."""
		self.db_set("approved_amount", flt(self.total_requested))
		self.make_gl_entries()
		self.set_status(update=True)

	def before_cancel(self):
		# Let cancellation proceed even though a disbursement Payment Entry / surrender Expense
		# Claim references this doc — the cascade is handled in on_cancel.
		self.ignore_linked_doctypes = [
			"GL Entry", "Payment Ledger Entry", "Payment Entry", "Expense Claim",
		]

	def on_cancel(self):
		"""Reverse the accrual GL. The requisition owns its ledger, so this is the only reversal."""
		self.make_gl_entries(cancel=True)
		self.db_set("status", "Cancelled")

	# ------------------------------------------------------------------ GL posting
	def get_gl_entries(self):
		gl = []
		for ln in self.get("items"):
			if flt(ln.amount) <= 0:
				continue
			gl.append(self.get_gl_dict({
				"account": ln.account,
				"debit": flt(ln.amount),
				"debit_in_account_currency": flt(ln.amount),
				"cost_center": ln.cost_center or self.cost_center,
				"project": ln.project or self.project,
				"against": self.employee,
			}, item=ln))
		gl.append(self.get_gl_dict({
			"account": self.payable_account,
			"credit": flt(self.total_requested),
			"credit_in_account_currency": flt(self.total_requested),
			"party_type": "Employee",
			"party": self.employee,
			"against_voucher_type": self.doctype,
			"against_voucher": self.name,
			"cost_center": self.cost_center,
		}, item=self))
		return gl

	def make_gl_entries(self, cancel=False):
		if cancel:
			make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
			return
		gl = self.get_gl_entries()
		if gl:
			# update_outstanding="No": we track outstanding on the document ourselves; the party
			# GL leg still creates Payment Ledger Entries so a Payment Entry can settle it.
			make_gl_entries(gl, update_outstanding="No", merge_entries=False)

	# ------------------------------------------------------------------ amounts / status
	def update_amounts(self, update=True):
		"""Recompute disbursed / surrendered / returned / outstanding from linked documents.

		Disbursed/returned are summed from submitted Payment Entry Reference rows pointing at this
		requisition (Pay = disbursement, Receive = return); surrendered from the linked Expense
		Claim. Called by the Payment Entry + Expense Claim hooks (B3/B4); safe to call anytime.
		"""
		disbursed = returned = 0.0
		pe_link = ret_link = None
		for r in frappe.get_all(
			"Payment Entry Reference",
			filters={"reference_doctype": self.doctype, "reference_name": self.name, "docstatus": 1},
			fields=["parent", "allocated_amount"],
			order_by="creation",
		):
			ptype = frappe.db.get_value("Payment Entry", r.parent, "payment_type")
			if ptype == "Pay":
				disbursed += flt(r.allocated_amount)
				pe_link = pe_link or r.parent
			elif ptype == "Receive":
				returned += flt(r.allocated_amount)
				ret_link = ret_link or r.parent

		surrendered = 0.0
		if self.expense_claim:
			surrendered = flt(frappe.db.get_value(
				"Expense Claim", {"name": self.expense_claim, "docstatus": 1}, "total_sanctioned_amount"
			))

		outstanding = flt(disbursed) - flt(surrendered) - flt(returned)
		vals = {
			"disbursed_amount": disbursed,
			"returned_amount": returned,
			"surrendered_amount": surrendered,
			"outstanding_amount": outstanding,
			"payment_entry": pe_link,
			"return_payment_entry": ret_link,
			"dispatched": 1 if pe_link else 0,
		}
		if update:
			self.db_set(vals, update_modified=False)
		else:
			for k, v in vals.items():
				setattr(self, k, v)
		self.set_status(update=update)

	def set_status(self, update=False):
		status = self._derive_status()
		if update:
			self.db_set("status", status, update_modified=False)
		else:
			self.status = status

	def _derive_status(self):
		if self.docstatus == 2:
			return "Cancelled"
		if self.docstatus == 0:
			return "Draft"
		disbursed = flt(self.disbursed_amount)
		accounted = flt(self.surrendered_amount) + flt(self.returned_amount)
		if disbursed <= 0:
			return "Approved"
		if accounted <= 0:
			return "Disbursed"
		if accounted + 0.01 < disbursed:
			return "Disbursed"  # partially accounted for
		# fully accounted
		if flt(self.returned_amount) and not flt(self.surrendered_amount):
			return "Returned"
		return "Closed"


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------

def staff_payable_account(company):
	"""The Staff Expense Payable account the requisition credits (per company)."""
	if not company:
		return None
	if frappe.db.has_column("Company", PAYABLE_ACCOUNT_FIELD):
		return frappe.get_cached_value("Company", company, PAYABLE_ACCOUNT_FIELD)
	return None


def expense_type_account(expense_type, company):
	"""Resolve an Expense Claim Type's default account for a company (Expense Claim Account child)."""
	if not expense_type or not company:
		return None
	return frappe.db.get_value(
		"Expense Claim Account",
		{"parent": expense_type, "company": company},
		"default_account",
	)
