# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Payment Entry ⟷ Expense Requisition (disbursement-recognition).

The disbursement is a third-party Payment Entry linked to the requisition via `custom_requisition`
(NOT an invoice reference). On the PE's submit the requisition RECOGNISES the expense
(Dr Expense / Cr Staff Payable, party=payee, against the PE), so net of the PE's
Dr Staff Payable / Cr Bank the books read Dr Expense / Cr Bank. The PE also carries the M-Pesa /
bank payee fields so frappe_mpsa_payments' B2C batch can disburse it.
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

REQ_DT = "Expense Requisition"


# --------------------------------------------------------------------------- disbursement builder
@frappe.whitelist()
def get_disbursement_payment_entry(requisition, bank_account=None):
	"""Build (not save) the disbursement Payment Entry: Dr Staff Payable (party=payee) / Cr Bank,
	linked to the requisition, carrying the payee's M-Pesa / bank details for disbursement."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_bank_cash_account
	from erpnext.accounts.utils import get_account_currency

	if not frappe.has_permission("Payment Entry", "create"):
		frappe.throw(_("You do not have permission to disburse (create a Payment Entry)."), frappe.PermissionError)

	er = frappe.get_doc(REQ_DT, requisition)
	if er.docstatus != 1:
		frappe.throw(_("Approve the requisition before disbursing."))
	if frappe.db.get_value(REQ_DT, er.name, "dispatched", for_update=True):
		frappe.throw(_("{0} has already been disbursed.").format(er.name))
	amount = flt(er.approved_amount) - flt(er.disbursed_amount)
	if amount <= 0:
		frappe.throw(_("Nothing left to disburse on {0}.").format(er.name))
	if not er.payable_account:
		frappe.throw(_("No Staff Expense Payable account on {0}.").format(er.name))

	party_type, party = (er.custom_payee_type, er.custom_payee) if (
		er.get("custom_direct_payment") and er.get("custom_payee_type") and er.get("custom_payee")
	) else ("Employee", er.employee)

	bank = get_bank_cash_account(er, bank_account)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.company = er.company
	pe.posting_date = nowdate()
	pe.mode_of_payment = er.mode_of_payment
	pe.party_type = party_type
	pe.party = party
	pe.paid_from = bank.account
	pe.paid_to = er.payable_account
	pe.paid_from_account_currency = bank.account_currency
	pe.paid_to_account_currency = get_account_currency(er.payable_account)
	pe.paid_amount = amount
	pe.received_amount = amount
	pe.cost_center = er.cost_center
	pe.project = er.project
	if er.get("funding_source"):
		pe.funding_source = er.funding_source
	pe.custom_requisition = er.name

	# M-Pesa / bank payee handoff (so frappe_mpsa_payments' B2C batch can disburse).
	if er.get("custom_payment_method"):
		pe.custom_third_party_payee = 1
		pe.custom_payee_type = er.get("custom_payee_type") or "Employee"
		pe.custom_payment_method = er.custom_payment_method
		pe.custom_account_name = er.get("custom_account_name")
		pe.custom_account_no = er.get("custom_account_no")
		if frappe.get_meta("Payment Entry").has_field("custom_disbursement_status"):
			pe.custom_disbursement_status = "Pending Disbursement"

	pe.setup_party_account_field()
	pe.set_missing_values()
	return pe


# --------------------------------------------------------------------------- doc_events
def update_requisition_from_payment(doc, method=None):
	"""Payment Entry on_submit/on_cancel: recognise / reverse the requisition's expense GL + amounts."""
	if not doc.get("custom_requisition"):
		return
	er = frappe.get_doc(REQ_DT, doc.custom_requisition)

	if method == "on_submit" and doc.payment_type == "Pay":
		er.recognise_disbursement(doc.name, flt(doc.paid_amount))
		er.update_amounts(update=True)
	elif method == "on_cancel":
		if er.docstatus != 2:  # standalone PE cancel — the requisition stays open
			er.reverse_disbursement()
			er.update_amounts(update=True)
