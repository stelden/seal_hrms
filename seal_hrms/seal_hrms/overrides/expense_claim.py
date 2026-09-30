# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Expense Claim: approval in an absent approver's place (see `seal_hrms.acting`)."""

import frappe

from seal_hrms.seal_hrms import acting

AUTHORITY = "expense_approval"


def _is_being_approved(doc) -> bool:
    if doc.approval_status != "Approved":
        return False
    if doc.is_new() or getattr(doc, "_action", None) == "submit":
        return True
    before = doc.get_doc_before_save()
    return bool(before) and before.approval_status != "Approved"


def validate(doc, method=None):
    if _is_being_approved(doc):
        acting.refuse_self_approval(doc, doc.employee, doc.expense_approver, AUTHORITY)


def on_update(doc, method=None):
    acting.share_new_document(doc, doc.expense_approver, AUTHORITY)


def on_submit(doc, method=None):
    acting.record_acting_approval(doc, doc.expense_approver, AUTHORITY)
