# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""HR approvals that are not plain Frappe Workflow steps, for My Desk's Approvals inbox.

Four kinds (HR_ON_MY_DESK.md §2.1, SECTIONS_CONTRACT.md §4):

  * leave, decided by the employee's leave approver (Frappe HR: no workflow);
  * expense claims, decided by the expense approver (likewise);
  * time off in lieu claims (a Frappe Workflow, but only the named approver or
    their stand-in may decide, which the workflow cannot say);
  * timesheets, where the company asks for approval (`timesheets.approval`).

Each lists what waits for the person **and** for anyone whose approvals they hold
while that person is on leave (`acting`), never the person's own requests. Items are
plain records; `seal_hrms.desk.providers` turns them into seal_desk's types.

Each `act_on_*` is what the inbox calls. It trusts nothing about the item having been
offered: it loads the document, checks the person may read it and decide it, that it
is still waiting, that a refusal has a reason and that a money decision had a fresh
check, then takes the same server path the desk form takes, so Frappe HR's own rules
and ours (self-approval, cover before approval, stand-ins) all run again.

Leave and expense claims stand down where the site runs its own Frappe Workflow on
them: that workflow's steps are then the approval, and seal_desk lists them itself.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, formatdate

from seal_hrms.seal_hrms import acting, step_up
from seal_hrms.seal_hrms.handover import user_for_employee

LEAVE, EXPENSE = "Leave Application", "Expense Claim"
CLAIM, TIMESHEET = "Time Off in Lieu Claim", "Timesheet"
APPROVE, REJECT, RETURN = "Approve", "Reject", "Return"
#: Words that make an action a refusal, which needs a reason (as seal_desk's inbox reads them).
REFUSING = ("reject", "return", "decline", "send back")
APPROVING = ("approve", "authorise", "authorize", "accept")


# ---------------------------------------------------------------- shared


def _action(key: str, label: str | None = None, verify: bool = False) -> frappe._dict:
	words = key.lower()
	refusing = any(w in words for w in REFUSING)
	tone = "destructive" if refusing else "primary" if any(w in words for w in APPROVING) else "neutral"
	return frappe._dict(key=key, label=label or _(key), tone=tone, needs_reason=refusing, verify=verify)


def _item(doctype, name, title, meta="", sender=None, since=None, amount=None, currency=None, on_behalf_of=None, actions=()):
	return frappe._dict(
		doctype=doctype,
		name=name,
		title=title,
		meta=meta,
		sender=sender,
		since=since,
		amount=amount,
		currency=currency,
		on_behalf_of=on_behalf_of,
		actions=list(actions),
	)


def approvers_for(user: str, authority: str) -> list[str]:
	"""`user` and everyone whose `authority` approvals they hold right now (a Head of Department line counts)."""
	kinds = acting.kinds_answering(authority)
	principals = [r.principal for r in acting.acting_for(user) if r.authority in kinds and r.principal]
	return list(dict.fromkeys([user, *principals]))


def _own_employee(user: str) -> str | None:
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


def _has_workflow(doctype: str) -> bool:
	from frappe.model.workflow import get_workflow_name

	return bool(get_workflow_name(doctype))


def _on_behalf(named: str | None, user: str) -> str | None:
	return named if named and named != user else None


def _require(condition, message, exc=frappe.ValidationError) -> None:
	if not condition:
		frappe.throw(message, exc)


def _reason(action: str, reason: str | None) -> str | None:
	reason = (reason or "").strip() or None
	if any(w in action.lower() for w in REFUSING) and not reason:
		frappe.throw(_("Say why, so the person knows what to change."))
	return reason


def _may_decide(named: str | None, authority: str, user: str) -> bool:
	"""The named approver, or whoever approves in their place now. HR included only as named."""
	return bool(named) and (named == user or acting.acting_stand_in(named, authority) == user)


def _load(doctype: str, name: str):
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return doc


def _done(message: str) -> dict:
	return {"ok": True, "message": message, "next": None}


# ---------------------------------------------------------------- leave


def leave_items(user: str) -> list[frappe._dict]:
	"""Open leave applications waiting for `user` as leave approver, or for someone they approve for."""
	if _has_workflow(LEAVE):
		return []
	me = _own_employee(user)
	out = []
	for la in frappe.get_all(
		LEAVE,
		filters=[["leave_approver", "in", approvers_for(user, "leave_approval")], ["docstatus", "=", 0], ["status", "=", "Open"]],
		fields=["name", "employee", "employee_name", "leave_type", "from_date", "to_date", "total_leave_days", "leave_approver", "creation"],
		order_by="creation asc",
	):
		if me and la.employee == me:
			continue
		out.append(_item(
			LEAVE, la.name,
			_("Leave for {0}").format(la.employee_name),
			_("{0}: {1} days, {2} to {3}").format(
				_(la.leave_type), f"{flt(la.total_leave_days):g}", formatdate(la.from_date), formatdate(la.to_date)
			),
			sender=user_for_employee(la.employee), since=la.creation,
			on_behalf_of=_on_behalf(la.leave_approver, user),
			actions=[_action(APPROVE), _action(REJECT)],
		))
	return out


@frappe.whitelist(methods=["POST"])
def act_on_leave(name: str, action: str, reason: str | None = None) -> dict:
	"""Approve or reject a leave application from the Approvals inbox, as the session user."""
	user = frappe.session.user
	_require(action in (APPROVE, REJECT), _("Leave can only be approved or rejected here."))
	_require(not _has_workflow(LEAVE), _("Leave on this site moves by its approval steps. Open the application."))
	doc = _load(LEAVE, name)
	_require(doc.docstatus == 0 and doc.status == "Open", _("This leave application is no longer waiting for a decision."))
	_require(user_for_employee(doc.employee) != user, _("This is your own leave. Someone else must decide it."), frappe.PermissionError)
	_require(
		_may_decide(doc.leave_approver, "leave_approval", user),
		_("Only {0}, or whoever approves in their place, can decide this leave.").format(doc.leave_approver_name or doc.leave_approver or _("the leave approver")),
		frappe.PermissionError,
	)
	reason = _reason(action, reason)
	doc.status = "Approved" if action == APPROVE else "Rejected"
	doc.submit()  # Frappe HR's checks, permission to submit, and ours (self-approval, cover)
	if reason:
		doc.add_comment("Comment", reason)
	return _done(_("Leave approved.") if action == APPROVE else _("Leave rejected."))


# ---------------------------------------------------------------- expense claims


def expense_items(user: str) -> list[frappe._dict]:
	"""Draft expense claims waiting for `user` as expense approver, or for someone they approve for."""
	if _has_workflow(EXPENSE):
		return []
	me = _own_employee(user)
	out = []
	for ec in frappe.get_all(
		EXPENSE,
		filters=[["expense_approver", "in", approvers_for(user, "expense_approval")], ["docstatus", "=", 0], ["approval_status", "=", "Draft"]],
		fields=["name", "employee", "employee_name", "grand_total", "total_claimed_amount", "posting_date", "company", "currency", "expense_approver", "creation"],
		order_by="creation asc",
	):
		if me and ec.employee == me:
			continue
		out.append(_item(
			EXPENSE, ec.name,
			_("Expense claim from {0}").format(ec.employee_name),
			_("Claimed on {0}").format(formatdate(ec.posting_date)),
			sender=user_for_employee(ec.employee), since=ec.creation,
			amount=flt(ec.grand_total or ec.total_claimed_amount),
			currency=ec.currency or (frappe.get_cached_value("Company", ec.company, "default_currency") if ec.company else None),
			on_behalf_of=_on_behalf(ec.expense_approver, user),
			# Money leaves the company on approval: the phone asks for a fresh check first (P4-2).
			actions=[_action(APPROVE, verify=True), _action(REJECT)],
		))
	return out


@frappe.whitelist(methods=["POST"])
def act_on_expense(name: str, action: str, reason: str | None = None) -> dict:
	"""Approve or reject an expense claim from the Approvals inbox, as the session user."""
	user = frappe.session.user
	_require(action in (APPROVE, REJECT), _("An expense claim can only be approved or rejected here."))
	_require(not _has_workflow(EXPENSE), _("Expense claims on this site move by their approval steps. Open the claim."))
	doc = _load(EXPENSE, name)
	_require(doc.docstatus == 0 and doc.approval_status == "Draft", _("This expense claim is no longer waiting for a decision."))
	_require(user_for_employee(doc.employee) != user, _("This is your own claim. Someone else must decide it."), frappe.PermissionError)
	_require(
		_may_decide(doc.expense_approver, "expense_approval", user),
		_("Only {0}, or whoever approves in their place, can decide this claim.").format(doc.expense_approver or _("the expense approver")),
		frappe.PermissionError,
	)
	reason = _reason(action, reason)
	if action == APPROVE:
		step_up.require_fresh_check()
	doc.approval_status = "Approved" if action == APPROVE else "Rejected"
	doc.submit()
	if reason:
		doc.add_comment("Comment", reason)
	return _done(_("Expense claim approved.") if action == APPROVE else _("Expense claim rejected."))


# ---------------------------------------------------------------- time off in lieu


def toil_items(user: str) -> list[frappe._dict]:
	"""Time off claims waiting for `user`'s authorisation or approval, or for someone they approve for."""
	from frappe.model.workflow import get_transitions

	from seal_hrms.seal_hrms.toil import access, workflow
	from seal_hrms.seal_hrms.toil.stage import days

	if not frappe.db.table_exists(CLAIM):
		return []
	me = access.employee_for_user(user)
	out = []
	for claim in frappe.get_all(
		CLAIM,
		filters=[["approver", "in", approvers_for(user, access.AUTHORITY)], ["docstatus", "=", 0], ["status", "in", list(workflow.WAITING_STATES)]],
		fields=["name", "employee", "employee_name", "status", "days", "sent_on", "approver"],
		order_by="sent_on asc",
	):
		if me and claim.employee == me:
			continue
		try:
			steps = [t.action for t in get_transitions(frappe.get_doc(CLAIM, claim.name))]
		except Exception:
			frappe.clear_last_message()
			steps = []
		actions = [_action(a) for a in dict.fromkeys(steps) if a != workflow.CANCEL]
		out.append(_item(
			CLAIM, claim.name,
			_("Time off claim from {0}").format(claim.employee_name),
			_("Extra work to authorise") if claim.status == workflow.WAITING_AUTH else _("{0} to approve").format(days(claim.days)),
			sender=user_for_employee(claim.employee), since=claim.sent_on,
			on_behalf_of=_on_behalf(claim.approver, user),
			actions=actions,
		))
	return out


@frappe.whitelist(methods=["POST"])
def act_on_toil(name: str, action: str, reason: str | None = None) -> dict:
	"""Take one of a time off claim's workflow steps from the Approvals inbox, as the session user."""
	from seal_hrms.seal_hrms.toil import access, workflow

	doc = _load(CLAIM, name)
	_require(doc.docstatus == 0 and doc.status in workflow.WAITING_STATES, _("This claim is no longer waiting for a decision."))
	access.require_decider(doc)  # never their own; the named approver, their stand-in, or HR
	reason = _reason(action, reason)
	status = workflow.act(name, action, reason).status  # Frappe's apply_workflow: the step must be open to them
	return _done(_("{0}: {1}").format(_(action), _(status)))


# ---------------------------------------------------------------- timesheets


def timesheet_items(user: str) -> list[frappe._dict]:
	"""Timesheets waiting for `user`'s approval, or for someone they approve for."""
	from seal_hrms.seal_hrms.timesheets import approval

	if not frappe.get_meta(TIMESHEET).has_field("custom_approval_state") or approval.site_workflow():
		return []
	me = _own_employee(user)
	out = []
	for ts in frappe.get_all(
		TIMESHEET,
		filters=[["custom_approver", "in", approvers_for(user, approval.AUTHORITY)], ["docstatus", "=", 0], ["custom_approval_state", "=", approval.WAITING]],
		fields=["name", "employee", "employee_name", "start_date", "end_date", "total_hours", "custom_sent_on", "custom_approver"],
		order_by="custom_sent_on asc",
	):
		if me and ts.employee == me:
			continue
		out.append(_item(
			TIMESHEET, ts.name,
			_("Timesheet from {0}").format(ts.employee_name),
			_("{0} hours, {1} to {2}").format(f"{flt(ts.total_hours):g}", formatdate(ts.start_date), formatdate(ts.end_date)),
			sender=user_for_employee(ts.employee), since=ts.custom_sent_on,
			on_behalf_of=_on_behalf(ts.custom_approver, user),
			actions=[_action(APPROVE), _action(RETURN)],
		))
	return out


@frappe.whitelist(methods=["POST"])
def act_on_timesheet(name: str, action: str, reason: str | None = None) -> dict:
	"""Approve or return a timesheet from the Approvals inbox, as the session user."""
	from seal_hrms.seal_hrms.timesheets import approval

	_require(action in (APPROVE, RETURN), _("A timesheet can only be approved or returned here."))
	reason = _reason(action, reason)
	# Both check everything themselves: approval on, the decider, still waiting, a reason to return.
	if action == APPROVE:
		approval.approve(name)
		return _done(_("Timesheet approved."))
	approval.return_timesheet(name, reason)
	return _done(_("Timesheet returned."))
