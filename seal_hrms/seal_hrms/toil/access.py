# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Who may see, change and decide a Time Off in Lieu Claim.

  * the member of staff sees and edits their own;
  * the approver (their leave approver, set by the server) sees it and decides;
  * whoever approves in the approver's place during their leave (a handover's
    "Approving time off in lieu" line, or a Head of Department's) does too;
  * HR User, HR Manager and System Manager see everything.

Nobody decides their own claim, HR included. Both permission hooks return a
plain bool (SEAL_DEV_RULES §2.9) and ship together (§3.4). Shares still grant
access on top (Frappe checks them before asking these hooks), which is how a
stand-in reaches a claim they were not named on.
"""

import frappe
from frappe import _

from seal_hrms.seal_hrms.handover import user_for_employee

CLAIM = "Time Off in Lieu Claim"
AUTHORITY = "toil_approval"
BACKOFFICE_ROLES = {"HR User", "HR Manager", "System Manager"}
WAITING = "Waiting for Approval"


def is_backoffice(user: str) -> bool:
	return user == "Administrator" or bool(set(frappe.get_roles(user)) & BACKOFFICE_ROLES)


def employee_for_user(user: str) -> str | None:
	return frappe.db.get_value("Employee", {"user_id": user}, "name") or None


def _principals_for(user: str) -> list[str]:
	"""Approvers `user` is approving time off for right now."""
	from seal_hrms.seal_hrms import acting

	kinds = acting.kinds_answering(AUTHORITY)
	return [row.principal for row in acting.acting_for(user) if row.authority in kinds and row.principal]


def can_decide(doc, user: str | None = None) -> bool:
	"""Whether `user` may approve, return or reject this claim. Never their own."""
	from seal_hrms.seal_hrms import acting

	user = user or frappe.session.user
	if user_for_employee(doc.employee) == user:
		return False
	if is_backoffice(user) or (doc.approver and doc.approver == user):
		return True
	return bool(doc.approver) and acting.acting_stand_in(doc.approver, AUTHORITY) == user


def has_permission(doc, ptype=None, user=None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if is_backoffice(user):
		return True
	me = employee_for_user(user)
	if ptype == "create" and not doc.get("employee"):
		return True  # a new, empty claim: the role decides
	if me and doc.get("employee") == me:
		# Their own: anything but deleting a claim already sent.
		return ptype != "delete" or doc.get("status") in (None, "", "Draft", "Returned")
	if doc.get("approver") and doc.approver == user:
		return ptype != "delete"
	if doc.get("approver") and doc.approver in _principals_for(user):
		return ptype != "delete"
	return False


def query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if is_backoffice(user):
		return ""
	table = f"`tab{CLAIM}`"
	clauses = [f"{table}.approver = {frappe.db.escape(user)}"]
	me = employee_for_user(user)
	if me:
		clauses.append(f"{table}.employee = {frappe.db.escape(me)}")
	principals = _principals_for(user)
	if principals:
		clauses.append(f"{table}.approver in ({', '.join(frappe.db.escape(p) for p in principals)})")
	return "(" + " or ".join(clauses) + ")"


def can_send(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	return is_backoffice(user) or bool(doc.employee and employee_for_user(user) == doc.employee)


def require_self_or_hr(employee: str) -> None:
	user = frappe.session.user
	if is_backoffice(user) or (employee and employee_for_user(user) == employee):
		return
	frappe.throw(_("You can only send your own claims."), frappe.PermissionError)


def can_see_time(employee: str, user: str | None = None) -> bool:
	"""The person themselves, whoever approves their leave (or acts for that approver), and HR."""
	from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

	from seal_hrms.seal_hrms import acting

	user = user or frappe.session.user
	if is_backoffice(user) or (employee and employee_for_user(user) == employee):
		return True
	approver = get_employee_leave_approver(employee) if employee else None
	return bool(approver) and (approver == user or acting.acting_stand_in(approver, AUTHORITY) == user)


def require_can_see_time(employee: str) -> None:
	if not can_see_time(employee):
		frappe.throw(
			_("You can only see your own time, or the time of staff whose leave you approve."),
			frappe.PermissionError,
		)


def require_decider(doc) -> None:
	if user_for_employee(doc.employee) == frappe.session.user:
		frappe.throw(_("This is your own claim. Someone else must decide it."), frappe.PermissionError)
	if not can_decide(doc):
		frappe.throw(
			_("Only {0}, or whoever approves in their place, can decide this claim.").format(
				doc.approver_name or doc.approver or _("the approver")
			),
			frappe.PermissionError,
		)


# ---------------------------------------------------------------- handover kind


def holds_toil_approval(user: str) -> bool:
	"""Approves time off claims: a leave approver at a company that banks extra hours."""
	from seal_hrms.seal_hrms import acting
	from seal_hrms.seal_hrms.working_time.policy import toil_companies

	companies = toil_companies()
	if not companies:
		return False
	return acting.holds_leave_approval(user) and bool(
		frappe.db.exists(
			"Employee", {"leave_approver": user, "status": "Active", "company": ["in", companies]}
		)
		or frappe.db.exists("Department Approver", {"approver": user, "parentfield": "leave_approvers"})
	)


def pending_toil_approvals(user: str) -> list[tuple[str, str]]:
	if not frappe.db.table_exists(CLAIM):
		return []
	return [
		(CLAIM, name)
		for name in frappe.get_all(
			CLAIM, filters={"approver": user, "docstatus": 0, "status": WAITING}, pluck="name"
		)
	]
