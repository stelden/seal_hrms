# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Expense Requisition — staff request funds to execute a task (disbursement-recognition).

Lifecycle:
    Approve (submit):  no GL — just an authorised, costed request.
    Disburse:          on the Payment Entry's submit the expense is RECOGNISED:
                         Dr Expense (per line)    / Cr Staff Expense Payable (party = payee)   ← this doc
                         Dr Staff Expense Payable / Cr Bank                                    ← the Payment Entry
                       (net = Dr Expense / Cr Bank; the payable nets to zero for the payee)
    Surrender/Return:  accounted for on the separate Expense Surrender doc (receipts + return of
                       any unspent balance: Dr Bank / Cr Expense).
    Cancel:            reverse this doc's expense GL + cascade-cancel the Payment Entry.

The requisition is the expense voucher (subclasses AccountsController, posts via make_gl_entries),
but the GL fires at disbursement, not approval. The disbursement Payment Entry is a third-party
payment linked by `custom_requisition` (NOT an invoice reference), so it doubles as the M-Pesa /
bank disbursement instruction.
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

# Company custom field naming the payable the requisition credits.
PAYABLE_ACCOUNT_FIELD = "custom_staff_requisition_payable_account"


class ExpenseRequisition(AccountsController):
	# Invoice-shaped totals so any Payment Entry reference-detail helper can value the doc safely.
	@property
	def grand_total(self):
		return flt(self.approved_amount) or flt(self.total_requested)

	@property
	def base_grand_total(self):
		return self.grand_total

	@property
	def advance_paid(self):
		return flt(self.disbursed_amount)

	# ------------------------------------------------------------------ validate
	def validate(self):
		self._set_defaults()
		self._resolve_line_accounts()
		self._compute_total()
		self.set_status()

	def _set_defaults(self):
		if not self.posting_date:
			self.posting_date = nowdate()
		if not self.currency:
			self.currency = frappe.get_cached_value("Company", self.company, "default_currency")
		self.conversion_rate = 1
		if not self.payable_account:
			self.payable_account = staff_payable_account(self.company)
		for ln in self.get("items"):
			ln.cost_center = ln.cost_center or self.cost_center
			ln.project = ln.project or self.project
			ln.funding_source = ln.funding_source or self.funding_source

	def _resolve_line_accounts(self):
		for ln in self.get("items"):
			if ln.expense_type and not ln.account:
				ln.account = expense_type_account(ln.expense_type, self.company)

	def _compute_total(self):
		self.total_requested = flt(sum(flt(ln.amount) for ln in self.get("items")))

	# ------------------------------------------------------------------ submit / cancel
	def before_submit(self):
		if not self.payable_account:
			frappe.throw(_("No Staff Expense Payable account configured for {0}.").format(self.company))
		if flt(self.total_requested) <= 0:
			frappe.throw(_("Add at least one requisition line with an amount before approving."))
		for ln in self.get("items"):
			if not ln.account:
				frappe.throw(_("Row {0}: no expense account — set a default account on Expense Claim Type {1} for {2}.").format(
					ln.idx, ln.expense_type, self.company))

	def on_submit(self):
		"""Approved — NO GL yet. The expense is recognised at disbursement (recognise_disbursement)."""
		self.db_set("approved_amount", flt(self.total_requested))
		self.set_status(update=True)

	def before_cancel(self):
		self.ignore_linked_doctypes = [
			"GL Entry", "Payment Ledger Entry", "Payment Entry", "Expense Surrender",
		]

	def on_cancel(self):
		"""Cascade-cancel the disbursement payment(s), then reverse this doc's own GL."""
		self._cancel_linked_payment_entries()
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
		self.db_set("status", "Cancelled")

	def _cancel_linked_payment_entries(self):
		for name in frappe.get_all(
			"Payment Entry",
			filters={"custom_requisition": self.name, "docstatus": 1},
			pluck="name",
		):
			pe = frappe.get_doc("Payment Entry", name)
			pe.flags.ignore_permissions = True
			pe.cancel()

	# ------------------------------------------------------------------ disbursement GL (recognition)
	def _payee_party(self):
		"""(party_type, party) of who is paid — the requesting employee, or a chosen payee."""
		if self.get("custom_direct_payment") and self.get("custom_payee_type") and self.get("custom_payee"):
			return self.custom_payee_type, self.custom_payee
		return "Employee", self.employee

	def recognise_disbursement(self, payment_entry, amount):
		"""Book the expense when the disbursement Payment Entry is submitted:
		Dr Expense (per line, scaled to `amount`) / Cr Staff Payable (party=payee, against the PE)."""
		party_type, party = self._payee_party()
		lines = [ln for ln in self.get("items") if flt(ln.amount) > 0]
		total = sum(flt(ln.amount) for ln in lines) or 1
		gl, remaining = [], flt(amount)
		for i, ln in enumerate(lines):
			amt = round(remaining, 2) if i == len(lines) - 1 else round(amount * flt(ln.amount) / total, 2)
			remaining = round(remaining - amt, 2)
			if amt <= 0:
				continue
			gl.append(self.get_gl_dict({
				"account": ln.account,
				"debit": amt,
				"debit_in_account_currency": amt,
				"cost_center": ln.cost_center or self.cost_center,
				"project": ln.project or self.project,
				"against": party,
			}, item=ln))
		gl.append(self.get_gl_dict({
			"account": self.payable_account,
			"credit": flt(amount),
			"credit_in_account_currency": flt(amount),
			"party_type": party_type,
			"party": party,
			"against_voucher_type": "Payment Entry",
			"against_voucher": payment_entry,
			"cost_center": self.cost_center,
		}, item=self))
		make_gl_entries(gl, update_outstanding="No", merge_entries=False)

	def reverse_disbursement(self):
		"""Reverse the recognised expense GL (when the disbursement is cancelled standalone)."""
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	# ------------------------------------------------------------------ amounts / status
	def update_amounts(self, update=True):
		"""disbursed = sum of submitted Pay Payment Entries linked via custom_requisition;
		surrendered/returned come from the Expense Surrender doc(s)."""
		disbursed = 0.0
		pe_link = None
		for pe in frappe.get_all(
			"Payment Entry",
			filters={"custom_requisition": self.name, "payment_type": "Pay", "docstatus": 1},
			fields=["name", "paid_amount"],
			order_by="creation",
		):
			disbursed += flt(pe.paid_amount)
			pe_link = pe_link or pe.name

		surrendered = returned = 0.0
		if frappe.db.exists("DocType", "Expense Surrender"):
			rows = frappe.get_all(
				"Expense Surrender",
				filters={"expense_requisition": self.name, "docstatus": 1},
				fields=["total_actual", "amount_to_return"],
			)
			surrendered = flt(sum(flt(r.total_actual) for r in rows))
			returned = flt(sum(flt(r.amount_to_return) for r in rows))

		outstanding = flt(disbursed) - flt(surrendered) - flt(returned)
		vals = {
			"disbursed_amount": disbursed,
			"surrendered_amount": surrendered,
			"returned_amount": returned,
			"outstanding_amount": outstanding,
			"payment_entry": pe_link,
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
			ws = self.get("workflow_state")
			return ws if ws in ("Pending Approval", "Rejected") else "Draft"
		disbursed = flt(self.disbursed_amount)
		accounted = flt(self.surrendered_amount) + flt(self.returned_amount)
		if disbursed <= 0:
			return "Approved"
		if accounted + 0.01 >= disbursed:
			if flt(self.returned_amount) and not flt(self.surrendered_amount):
				return "Returned"
			return "Closed"
		if flt(self.surrendered_amount) > 0:
			return "Surrendered"
		return "Disbursed"


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------

def staff_payable_account(company):
	if not company:
		return None
	if frappe.db.has_column("Company", PAYABLE_ACCOUNT_FIELD):
		return frappe.get_cached_value("Company", company, PAYABLE_ACCOUNT_FIELD)
	return None


def expense_type_account(expense_type, company):
	if not expense_type or not company:
		return None
	return frappe.db.get_value(
		"Expense Claim Account",
		{"parent": expense_type, "company": company},
		"default_account",
	)
