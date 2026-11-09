# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Sending, authorising, approving, returning and rejecting a time off claim.

The claim's status moves only through these endpoints (SEAL_DEV_RULES §3.2):
each sets an in-process flag naming the claim, which the controller checks, so
a status sent over HTTP in a plain save is refused. Every endpoint checks the
caller first (§2.15) and writes through `save()` / `submit()`.

Claim afterwards (the default):

    Draft / Returned --send--> Waiting for Approval --approve--> Approved (submitted, time added)
                                                    --reject---> Rejected (submitted, nothing added)
                                                    --return---> Returned (the person corrects and resends)

Authorise first, then confirm the hours (a company's choice, stamped on the claim as `mode`):

    Draft / Returned --send_for_authorisation--> Waiting for Authorisation --authorise--> Authorised
                                                                           --return-----> Returned
                                                                           --reject-----> Rejected
    Authorised --send_for_approval (with the hours worked)--> Waiting for Approval
                                                               --approve--> Approved
                                                               --return---> Authorised
                                                               --reject---> Rejected

Approvers do not change hours: they return the claim with a reason (decision
D14, 2026-11-09). Each move sends its email (`toil.notifications`), which never
fails the move.
"""

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import now_datetime

from seal_hrms.seal_hrms.toil import access, notifications, rules
from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST, policy_for

CLAIM = "Time Off in Lieu Claim"
TRANSITION = "seal_toil_transition"
DRAFT, RETURNED, WAITING = "Draft", "Returned", "Waiting for Approval"
WAITING_AUTH, AUTHORISED = "Waiting for Authorisation", "Authorised"
APPROVED, REJECTED, CANCELLED = "Approved", "Rejected", "Cancelled"


@contextmanager
def transition(name: str):
	previous = frappe.flags.get(TRANSITION)
	frappe.flags[TRANSITION] = name
	try:
		yield
	finally:
		frappe.flags[TRANSITION] = previous


def in_transition(doc) -> bool:
	return bool(doc.name) and frappe.flags.get(TRANSITION) == doc.name


def authorise_first(doc) -> bool:
	return doc.get("mode") == AUTHORISE_FIRST


def _load(name: str):
	doc = frappe.get_doc(CLAIM, name)
	doc.check_permission("read")
	return doc


def _share_with(doc, user: str | None) -> None:
	if not user or frappe.db.exists(
		"DocShare", {"share_doctype": CLAIM, "share_name": doc.name, "user": user}
	):
		return
	frappe.share.add_docshare(
		CLAIM, doc.name, user, read=1, write=1, submit=1, flags={"ignore_share_permission": True}
	)


def _need_reason(reason: str | None) -> str:
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("Say what the person needs to change or know: they read this to put it right."))
	return reason


def _need_approver(doc) -> None:
	if not doc.approver:
		frappe.throw(
			_(
				"Nobody approves leave for {0}, so nobody can decide this claim. Ask HR to set a leave approver."
			).format(doc.employee_name),
			title=_("No Approver"),
		)


@frappe.whitelist(methods=["POST"])
def send_for_authorisation(name: str) -> str:
	"""Authorise-first: the person asks their approver to agree the extra work before doing it."""
	doc = _load(name)
	access.require_self_or_hr(doc.employee)
	if not authorise_first(doc):
		frappe.throw(_("This company does not authorise extra work first: send the claim for approval."))
	if doc.docstatus != 0 or doc.status not in (DRAFT, RETURNED):
		frappe.throw(_("Only a draft or returned claim can be sent."))
	_need_approver(doc)
	doc.status = WAITING_AUTH
	doc.sent_on = now_datetime()
	doc.decision_note = None
	with transition(doc.name):
		doc.save()
	_share_with(doc, doc.approver)
	notifications.sent(doc)
	return doc.status


@frappe.whitelist(methods=["POST"])
def authorise(name: str) -> str:
	"""Authorise-first: the approver agrees the planned extra work."""
	doc = _load(name)
	access.require_decider(doc)
	if doc.docstatus != 0 or doc.status != WAITING_AUTH:
		frappe.throw(_("This claim is not waiting to be authorised."))
	for line in doc.lines:
		line.authorised = 1
	doc.status = AUTHORISED
	doc.authorised_by = frappe.session.user
	doc.authorised_on = now_datetime()
	with transition(doc.name):
		doc.save()
	notifications.decided(doc, "authorised")
	return doc.status


@frappe.whitelist(methods=["POST"])
def send_for_approval(name: str) -> str:
	"""The person sends their claim (or, authorise-first, the hours they worked) to their leave approver."""
	doc = _load(name)
	access.require_self_or_hr(doc.employee)
	ready = (AUTHORISED,) if authorise_first(doc) else (DRAFT, RETURNED)
	if doc.docstatus != 0 or doc.status not in ready:
		frappe.throw(
			_("Send it to be authorised first.")
			if authorise_first(doc) and doc.status in (DRAFT, RETURNED)
			else _("Only a draft or returned claim can be sent.")
		)
	_need_approver(doc)
	rules.check_claim_window(doc, policy_for(doc.company))
	doc.status = WAITING
	doc.sent_on = now_datetime()
	doc.decision_note = None
	with transition(doc.name):
		doc.save()
	_share_with(doc, doc.approver)
	notifications.sent(doc)
	return doc.status


@frappe.whitelist(methods=["POST"])
def approve(name: str) -> str:
	"""The approver accepts the hours; the time is added to the person's balance."""
	doc = _load(name)
	access.require_decider(doc)
	if doc.docstatus != 0 or doc.status != WAITING:
		frappe.throw(_("This claim is not waiting for approval."))
	doc.status = APPROVED
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	with transition(doc.name):
		doc.submit()
	notifications.decided(doc, "approved")
	return doc.status


@frappe.whitelist(methods=["POST"])
def reject(name: str, reason: str | None = None) -> str:
	"""The approver turns the claim down; nothing is added."""
	doc = _load(name)
	access.require_decider(doc)
	_require_waiting(doc)
	doc.decision_note = _need_reason(reason)
	doc.status = REJECTED
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	with transition(doc.name):
		doc.submit()
	notifications.decided(doc, "rejected")
	return doc.status


@frappe.whitelist(methods=["POST"])
def return_claim(name: str, reason: str | None = None) -> str:
	"""The approver sends the claim back a step for the person to correct.

	Before authorisation it goes back to Returned; after it, to Authorised, so the
	person corrects the hours worked without asking for authorisation again.
	"""
	doc = _load(name)
	access.require_decider(doc)
	_require_waiting(doc)
	doc.decision_note = _need_reason(reason)
	doc.status = AUTHORISED if authorise_first(doc) and doc.status == WAITING else RETURNED
	doc.approved_by = frappe.session.user
	with transition(doc.name):
		doc.save()
	notifications.decided(doc, "returned")
	return doc.status


def _require_waiting(doc) -> None:
	if doc.docstatus != 0 or doc.status not in (WAITING, WAITING_AUTH):
		frappe.throw(_("This claim is not waiting for a decision."))


@frappe.whitelist()
def mode_for(employee: str) -> str:
	"""How extra work is agreed at this person's company, for a claim not yet saved. Reads only."""
	access.require_self_or_hr(employee)
	return policy_for(frappe.db.get_value("Employee", employee, "company")).prior_authorisation
