# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Integration tests for the Expense Requisition lifecycle (recognise-at-approval).

Covers: approval posts the accrual GL against the requisition; a disbursement Payment Entry
references + settles it (no "Allocated > outstanding"); surrender records receipts; return of
unspent funds corrects the expense; cancellation cascades to the payment and reverses everything.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, nowdate

from seal_hrms.seal_hrms.overrides.payment_entry import apply_patches, get_disbursement_payment_entry

COMPANY = "_Test Company"
EMPLOYEE = "_T-Employee-00001"
COST_CENTER = "Main - _TC"
EXPENSE_ACCOUNT = "_Test Account Cost for Goods Sold - _TC"
PAYABLE = "Staff Expense Payable - _TC"
CASH = "_Test Cash - _TC"
EXPENSE_TYPE = "Travel"


def _ensure_expense_claim_account():
	if not frappe.db.get_value("Expense Claim Account", {"parent": EXPENSE_TYPE, "company": COMPANY}, "name"):
		ect = frappe.get_doc("Expense Claim Type", EXPENSE_TYPE)
		ect.append("accounts", {"company": COMPANY, "default_account": EXPENSE_ACCOUNT})
		ect.save(ignore_permissions=True)


def _make_requisition(amounts=(4000, 6000)):
	er = frappe.new_doc("Expense Requisition")
	er.employee = EMPLOYEE
	er.company = COMPANY
	er.posting_date = nowdate()
	er.cost_center = COST_CENTER
	er.title = "Diani youth camp transport"
	for amount in amounts:
		er.append("items", {"expense_type": EXPENSE_TYPE, "description": "Field cost", "amount": amount})
	er.insert(ignore_permissions=True)
	return er


def _disburse(er):
	pe = get_disbursement_payment_entry(er.name, bank_account=CASH)
	pe.insert(ignore_permissions=True)
	pe.submit()
	er.reload()
	return pe


class TestExpenseRequisition(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		apply_patches()
		_ensure_expense_claim_account()

	def test_approval_posts_accrual_gl(self):
		er = _make_requisition()
		er.submit()
		er.reload()
		self.assertEqual(er.status, "Approved")
		self.assertEqual(flt(er.approved_amount), 10000)
		gl = frappe.get_all(
			"GL Entry",
			filters={"voucher_type": "Expense Requisition", "voucher_no": er.name, "is_cancelled": 0},
			fields=["account", "debit", "credit", "party", "against_voucher"],
		)
		self.assertEqual(sum(flt(g.debit) for g in gl), sum(flt(g.credit) for g in gl))
		self.assertEqual(sum(flt(g.debit) for g in gl), 10000)
		payable_legs = [g for g in gl if g.account == PAYABLE]
		self.assertEqual(len(payable_legs), 1)
		self.assertEqual(payable_legs[0].party, EMPLOYEE)
		self.assertEqual(payable_legs[0].against_voucher, er.name)

	def test_disbursement_references_requisition(self):
		er = _make_requisition()
		er.submit()
		pe = _disburse(er)  # must NOT raise "Allocated Amount cannot be greater than outstanding"
		self.assertEqual(er.status, "Disbursed")
		self.assertEqual(flt(er.disbursed_amount), 10000)
		self.assertTrue(er.dispatched)
		refs = [r for r in pe.references if r.reference_doctype == "Expense Requisition" and r.reference_name == er.name]
		self.assertEqual(len(refs), 1)

	def test_surrender_and_return_close_with_correct_expense(self):
		er = _make_requisition()
		er.submit()
		_disburse(er)
		for line, actual in zip(er.items, (3000, 4000)):
			line.actual_amount = actual
		er.save(ignore_permissions=True)
		er.surrender()
		er.reload()
		self.assertEqual(er.status, "Surrendered")
		self.assertEqual(flt(er.surrendered_amount), 7000)
		self.assertEqual(flt(er.outstanding_amount), 3000)

		er.return_funds(3000, CASH)
		er.reload()
		self.assertEqual(er.status, "Closed")
		self.assertEqual(flt(er.returned_amount), 3000)
		self.assertEqual(flt(er.outstanding_amount), 0)

		net_expense = frappe.db.sql(
			"""SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry`
			   WHERE voucher_type='Expense Requisition' AND voucher_no=%s AND is_cancelled=0 AND account=%s""",
			(er.name, EXPENSE_ACCOUNT),
		)[0][0]
		self.assertEqual(flt(net_expense), 7000)

	def test_cancel_cascades_and_reverses(self):
		er = _make_requisition((5000,))
		er.submit()
		pe = _disburse(er)
		er.cancel()
		self.assertEqual(frappe.db.get_value("Payment Entry", pe.name, "docstatus"), 2)
		for account in (PAYABLE, EXPENSE_ACCOUNT, CASH):
			net = frappe.db.sql(
				"""SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry`
				   WHERE is_cancelled=0 AND account=%s AND voucher_no IN (%s,%s)""",
				(account, er.name, pe.name),
			)[0][0]
			self.assertEqual(flt(net), 0)

	def test_overspend_blocked_at_surrender(self):
		er = _make_requisition((5000,))
		er.submit()
		_disburse(er)
		er.items[0].actual_amount = 6000  # more than disbursed
		er.save(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, er.surrender)
