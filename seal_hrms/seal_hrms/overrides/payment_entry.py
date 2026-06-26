# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Payment Entry integration for Expense Requisition.

The requisition books a party payable (Cr Staff Expense Payable, party=Employee, against the
requisition) at approval, so a Payment Entry can settle it invoice-style. ERPNext's Payment Entry
only allows Journal Entry as a reference for an Employee party, and its module-level
`get_reference_details` can't value a non-invoice doctype — so we extend both by monkeypatch
(hrms already overrides the Payment Entry *class*, so override_doctype_class is unavailable).

Three touch-points:
  * `get_valid_reference_doctypes`  — allow "Expense Requisition" for an Employee party.
  * `get_reference_details`         — value an Expense Requisition reference (total + outstanding
                                      + the payable account).
  * doc_events on Payment Entry     — recompute the requisition's amounts/status on submit/cancel.

Plus a builder (`get_disbursement_payment_entry`) for the form's "Disburse" button.
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

REQ_DT = "Expense Requisition"


# --------------------------------------------------------------------------- monkeypatches
def apply_patches():
	"""Idempotently extend ERPNext Payment Entry to understand Expense Requisition references."""
	import erpnext.accounts.doctype.payment_entry.payment_entry as pe_mod
	from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

	# Allow "Expense Requisition" as a reference for an Employee party. Different apps gate this in
	# different ways — hrms via get_valid_reference_doctypes, non_profit with a hardcoded list
	# *inline* in validate_reference_documents. Rather than chase each, wrap
	# validate_reference_documents to hide Expense Requisition rows during the app's own check and
	# restore them after. Patch the base, every imported subclass, and the resolved controller.
	classes = {PaymentEntry}
	try:
		classes.add(frappe.get_controller("Payment Entry"))
	except Exception:
		pass
	for cls in _iter_subclasses(PaymentEntry):
		classes.add(cls)
	for cls in classes:
		_patch_validate_reference_documents(cls)

	if not getattr(pe_mod.get_reference_details, "_seal_patched", False):
		_orig_details = pe_mod.get_reference_details

		def get_reference_details(reference_doctype, reference_name, party_account_currency, party_type=None, party=None):
			if reference_doctype == REQ_DT:
				return _expense_requisition_reference_details(reference_name)
			return _orig_details(reference_doctype, reference_name, party_account_currency, party_type, party)

		get_reference_details._seal_patched = True
		pe_mod.get_reference_details = get_reference_details
		# hrms's get_payment_reference_details routes non-employee doctypes (incl. Expense
		# Requisition) through its OWN import-bound `get_reference_details`. Rebind that name too,
		# otherwise a force=True revaluation during validate resets our outstanding to 0.
		try:
			import hrms.overrides.employee_payment_entry as hrms_pe
			if getattr(hrms_pe, "get_reference_details", None) is not None:
				hrms_pe.get_reference_details = get_reference_details
		except Exception:
			pass


def _iter_subclasses(cls):
	for sub in cls.__subclasses__():
		yield sub
		yield from _iter_subclasses(sub)


def ensure_patches(doc=None, method=None):
	"""before_validate hook on Payment Entry: apply the patches before validate_reference_documents
	runs, so the actually-resolved controller (which may differ per site / load late) is covered."""
	apply_patches()


def _patch_validate_reference_documents(cls):
	"""Wrap a class's validate_reference_documents to accept Expense Requisition references.

	Hides ER rows while the app's own validation runs (so its allowed-doctype gate, however it's
	written, skips them), then restores the exact original child list."""
	own = cls.__dict__.get("validate_reference_documents")
	if own is None or getattr(own, "_seal_patched", False):
		return
	orig = own

	def validate_reference_documents(self):
		all_refs = self.get("references") or []
		er_rows = [d for d in all_refs if d.reference_doctype == REQ_DT]
		if not er_rows:
			return orig(self)
		self.references = [d for d in all_refs if d.reference_doctype != REQ_DT]
		try:
			orig(self)
		finally:
			self.references = all_refs

	validate_reference_documents._seal_patched = True
	cls.validate_reference_documents = validate_reference_documents


def _expense_requisition_reference_details(reference_name):
	er = frappe.get_doc(REQ_DT, reference_name)
	total = flt(er.approved_amount) or flt(er.total_requested)
	outstanding = flt(er.approved_amount) - flt(er.disbursed_amount)
	return frappe._dict({
		"due_date": None,
		"total_amount": flt(total),
		"outstanding_amount": flt(outstanding),
		"exchange_rate": 1,
		"bill_no": None,
		"account": er.payable_account,
		"account_type": None,
		"payment_type": None,
	})


# --------------------------------------------------------------------------- disbursement builder
@frappe.whitelist()
def get_disbursement_payment_entry(requisition, bank_account=None):
	"""Build (not save) the disbursement Payment Entry: Dr Staff Payable / Cr Bank, referencing
	the requisition so the party ledger settles natively."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_bank_cash_account
	from erpnext.accounts.utils import get_account_currency

	er = frappe.get_doc(REQ_DT, requisition)
	if er.docstatus != 1:
		frappe.throw(_("Approve the requisition before disbursing."))
	# Pessimistic lock against a double-disbursement race (§3.3): the loser sees dispatched=1.
	if frappe.db.get_value(REQ_DT, er.name, "dispatched", for_update=True):
		frappe.throw(_("{0} has already been disbursed.").format(er.name))
	outstanding = flt(er.approved_amount) - flt(er.disbursed_amount)
	if outstanding <= 0:
		frappe.throw(_("Nothing left to disburse on {0}.").format(er.name))
	if not er.payable_account:
		frappe.throw(_("No Staff Expense Payable account on {0}.").format(er.name))

	bank = get_bank_cash_account(er, bank_account)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.company = er.company
	pe.posting_date = nowdate()
	pe.mode_of_payment = er.mode_of_payment
	pe.party_type = "Employee"
	pe.party = er.employee
	pe.paid_from = bank.account
	pe.paid_to = er.payable_account
	pe.paid_from_account_currency = bank.account_currency
	pe.paid_to_account_currency = get_account_currency(er.payable_account)
	pe.paid_amount = outstanding
	pe.received_amount = outstanding
	pe.cost_center = er.cost_center
	pe.project = er.project
	# Carry the requisition's funding source (some deployments require it on every Payment Entry).
	if er.get("funding_source"):
		pe.funding_source = er.funding_source
	pe.append("references", {
		"reference_doctype": REQ_DT,
		"reference_name": er.name,
		"total_amount": flt(er.approved_amount),
		"outstanding_amount": outstanding,
		"allocated_amount": outstanding,
	})
	pe.setup_party_account_field()
	pe.set_missing_values()
	return pe


# --------------------------------------------------------------------------- doc_events
def update_requisition_from_payment(doc, method=None):
	"""Payment Entry on_submit / on_cancel: recompute every referenced requisition's amounts."""
	names = {
		r.reference_name
		for r in (doc.get("references") or [])
		if r.reference_doctype == REQ_DT and r.reference_name
	}
	for name in names:
		er = frappe.get_doc(REQ_DT, name)
		if er.docstatus == 2:
			# The requisition itself is being cancelled; its on_cancel cascade handles teardown.
			continue
		er.update_amounts(update=True)
