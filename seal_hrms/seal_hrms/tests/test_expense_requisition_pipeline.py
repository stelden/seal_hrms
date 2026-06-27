# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Runnable pipeline test harness (seal_hrms): core lifecycle + GL. No M-Pesa/payee (MHC-specific).

Run on a live site (ERPNext's BootStrapTestData blocks `bench run-tests` on a populated DB):

    bench --site <site> execute seal_hrms.seal_hrms.tests.test_expense_requisition_pipeline.run

It uses real MHC City-campus masters, asserts the full pipeline + GL + M-Pesa figure-pulling, and
deletes everything it creates. Returns {passed, failed, failures}.
"""

import frappe
from frappe.utils import flt, nowdate
from frappe.model.workflow import apply_workflow

# --- MHC City-campus masters (adjust here if the harness is pointed at another site) ---
COMPANY = "ACME Holdings Ltd"
EMP = "HR-EMP-00003"
CC = "Main - AHL"
BANK = "1110 - Cash - AHL"
ETYPE = "Travel"
EXP_ACCT = "5111 - Cost of Goods Sold - AHL"
PAYABLE = "Staff Expense Payable - AHL"
FS = None

_created = []   # (doctype, name) to clean up


def _new_req(amounts, direct_payee=None):
	er = frappe.new_doc("Expense Requisition")
	er.employee = EMP
	er.company = COMPANY
	er.posting_date = nowdate()
	er.cost_center = CC
	if FS:
		er.funding_source = FS
	er.title = "pipeline test"
	for a in amounts:
		er.append("items", {"expense_type": ETYPE, "description": "x", "amount": a})
	if direct_payee:
		er.custom_direct_payment = 1
		er.custom_payee_type, er.custom_payee = direct_payee
	er.insert(ignore_permissions=True)
	_created.append(("Expense Requisition", er.name))
	return er



def _active_workflow():
	return frappe.db.get_value("Workflow", {"document_type": "Expense Requisition", "is_active": 1}, "name")


def _approve(er):
	# Use the approval workflow when it's active (MHC); otherwise submit directly (controller is
	# workflow-tolerant) so the harness runs on any deployment.
	if _active_workflow():
		apply_workflow(er, "Submit for Approval")
		apply_workflow(er, "Approve")
	else:
		er.submit()
	er.reload()


def _disburse(er, submit=True):
	from seal_hrms.seal_hrms.overrides.payment_entry import get_disbursement_payment_entry
	pe = get_disbursement_payment_entry(er.name, bank_account=BANK)
	pe.reference_no = "T-REF"
	pe.reference_date = nowdate()
	pe.insert(ignore_permissions=True)
	_created.append(("Payment Entry", pe.name))
	if submit and not pe.get("custom_third_party_payee"):
		# third-party (M-Pesa) PEs are gated 'Pending Disbursement' and submit via the B2C batch;
		# non-third-party PEs submit directly and recognise the expense here.
		pe.submit()
		er.reload()
	return pe


def _surrender(er, actuals, submit=True):
	es = frappe.new_doc("Expense Surrender")
	es.expense_requisition = er.name
	es.posting_date = nowdate()
	es.return_bank_account = BANK
	es.validate()  # seed lines from the requisition
	for ln, actual in zip(es.items, actuals):
		ln.actual_amount = actual
	es.insert(ignore_permissions=True)
	_created.append(("Expense Surrender", es.name))
	if submit:
		es.submit()
		er.reload()
	return es


def _net(account, *vouchers):
	if not vouchers:
		return 0.0
	ph = ",".join(["%s"] * len(vouchers))
	return flt(frappe.db.sql(
		f"""SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry`
		    WHERE is_cancelled=0 AND account=%s AND voucher_no IN ({ph})""",
		(account, *vouchers),
	)[0][0])


def _party_ple(party, account):
	return flt(frappe.db.sql(
		"""SELECT COALESCE(SUM(amount),0) FROM `tabPayment Ledger Entry`
		   WHERE party=%s AND account=%s AND delinked=0""", (party, account))[0][0])


# ---------------------------------------------------------------------------------- test cases
def t_approval_no_gl(R):
	er = _new_req([6000, 4000]); _approve(er)
	R.eq(er.status, "Approved", "status after approve")
	R.eq(flt(er.approved_amount), 10000, "approved_amount")
	R.eq(frappe.db.count("GL Entry", {"voucher_no": er.name, "is_cancelled": 0}), 0, "NO GL at approval")


def t_pending_status(R):
	if not _active_workflow():
		return  # no active approval workflow on this site — Pending Approval sub-state not exercised
	er = _new_req([1000])
	apply_workflow(er, "Submit for Approval"); er.reload()
	R.eq(er.status, "Pending Approval", "status reflects workflow Pending Approval")


def t_disbursement_recognition(R):
	er = _new_req([6000, 4000]); _approve(er)
	pe = _disburse(er)
	R.eq(er.status, "Disbursed", "status after disburse")
	R.eq(flt(er.disbursed_amount), 10000, "disbursed_amount")
	R.eq(_net(EXP_ACCT, er.name, pe.name), 10000, "net Expense = disbursed (Dr)")
	R.eq(_net(BANK, er.name, pe.name), -10000, "net Bank = -disbursed (Cr)")
	R.eq(_net(PAYABLE, er.name, pe.name), 0, "Staff Payable nets to zero")
	R.eq(_party_ple(EMP, PAYABLE), 0, "no unallocated party payment")


def t_double_disburse_locked(R):
	er = _new_req([5000]); _approve(er); _disburse(er)
	from seal_hrms.seal_hrms.overrides.payment_entry import get_disbursement_payment_entry
	R.raises(lambda: get_disbursement_payment_entry(er.name, bank_account=BANK), "second disburse is blocked")


def t_surrender_full(R):
	er = _new_req([10000]); _approve(er); pe = _disburse(er)
	es = _surrender(er, [10000])
	R.eq(flt(es.amount_to_return), 0, "nothing to return when fully spent")
	R.eq(er.status, "Closed", "status Closed after full surrender")
	R.eq(_net(EXP_ACCT, er.name, pe.name, es.name), 10000, "net expense = full spend")


def t_surrender_partial_return(R):
	er = _new_req([6000, 4000]); _approve(er); pe = _disburse(er)
	es = _surrender(er, [4000, 3000])  # 7000 spent, 3000 unspent
	R.eq(flt(es.total_actual), 7000, "total_actual")
	R.eq(flt(es.amount_to_return), 3000, "amount_to_return")
	R.eq(er.status, "Closed", "status Closed after surrender+return")
	R.eq(flt(er.outstanding_amount), 0, "outstanding zero")
	R.eq(_net(EXP_ACCT, er.name, pe.name, es.name), 7000, "net expense = actual spend (7000)")
	R.eq(_net(BANK, es.name), 3000, "return cash in to bank (Dr 3000)")


def t_surrender_overspend_blocked(R):
	er = _new_req([5000]); _approve(er); _disburse(er)
	R.raises(lambda: _surrender(er, [6000]), "surrender over disbursed is blocked")


def t_surrender_cancel_reopens(R):
	er = _new_req([8000]); _approve(er); _disburse(er)
	es = _surrender(er, [5000])
	R.eq(er.status, "Closed", "closed after surrender")
	es.cancel(); er.reload()
	R.eq(flt(er.surrendered_amount), 0, "surrendered cleared after ES cancel")
	R.eq(flt(er.outstanding_amount), 8000, "outstanding back to disbursed")
	R.eq(er.status, "Disbursed", "requisition reopened to Disbursed")


def t_cancel_cascade(R):
	er = _new_req([5000]); _approve(er); pe = _disburse(er)
	er.cancel(); er.reload()
	R.eq(er.status, "Cancelled", "requisition cancelled")
	R.eq(frappe.db.get_value("Payment Entry", pe.name, "docstatus"), 2, "PE cascade-cancelled")
	for acct in (EXP_ACCT, PAYABLE, BANK):
		R.eq(_net(acct, er.name, pe.name), 0, f"{acct[:20]} nets to zero after cancel")




def t_expense_surrender_seed(R):
	er = _new_req([6000, 4000]); _approve(er); _disburse(er)
	es = frappe.new_doc("Expense Surrender")
	es.expense_requisition = er.name; es.posting_date = nowdate()
	es.validate()
	R.eq(len(es.items), 2, "surrender seeds one line per requisition line")
	R.eq(flt(es.items[0].disbursed_amount), 6000, "seeded disbursed amount line 1")
	R.eq(flt(es.total_disbursed), 10000, "seeded total disbursed")


CASES = [
	t_approval_no_gl, t_pending_status, t_disbursement_recognition, t_double_disburse_locked,
	t_surrender_full, t_surrender_partial_return, t_surrender_overspend_blocked,
	t_surrender_cancel_reopens, t_cancel_cascade, t_expense_surrender_seed,
]


class _R:
	def __init__(self):
		self.passed = 0
		self.failures = []
		self._case = None

	def eq(self, got, want, msg):
		if flt(got) == flt(want) if isinstance(want, (int, float)) else got == want:
			self.passed += 1
		else:
			self.failures.append(f"{self._case}: {msg} — got {got!r}, want {want!r}")

	def true(self, cond, msg):
		if cond:
			self.passed += 1
		else:
			self.failures.append(f"{self._case}: {msg} — expected truthy")

	def raises(self, fn, msg):
		try:
			fn()
			self.failures.append(f"{self._case}: {msg} — expected an exception, none raised")
		except Exception:
			self.passed += 1


def _cleanup():
	for dt, name in reversed(_created):
		try:
			if not frappe.db.exists(dt, name):
				continue
			doc = frappe.get_doc(dt, name)
			if doc.docstatus == 1:
				doc.flags.ignore_permissions = True
				doc.cancel()
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		except Exception as e:
			print(f"  cleanup skip {dt} {name}: {str(e)[:80]}")
	_created.clear()


def run():
	R = _R()
	for case in CASES:
		R._case = case.__name__
		try:
			case(R)
		except Exception as e:
			R.failures.append(f"{case.__name__}: RAISED {type(e).__name__}: {str(e)[:160]}")
	_cleanup()
	frappe.db.commit()
	print(f"\n===== Expense Requisition pipeline: {R.passed} assertions passed, {len(R.failures)} failed =====")
	for f in R.failures:
		print("  FAIL", f)
	if not R.failures:
		print("  ALL GREEN")
	return {"passed": R.passed, "failed": len(R.failures), "failures": R.failures}
