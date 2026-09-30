# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Approving on someone's behalf while they are on leave.

A Task Assignment can hand over approvals as well as work: "while I am away,
Otieno approves my team's leave". Each row of its Approvals table names one
kind of approval and who gives it. The stand-in accepts that row separately,
because approving for someone is not the same promise as covering their tasks
(decision T2).

How approval is routed decides how it is delegated. HRMS never compares the
approver field with the person approving: a Leave Application or Expense Claim
is approved by whoever holds the approver role AND can open that document, which
HRMS arranges by sharing it with the named approver (`share_doc_with_approver`).
So for the leave window this module:

  * gives the stand-in the approver role if they lack it, recording that it was
    added, so it is never stripped from someone who already held it;
  * shares the principal's pending documents with them (read, write, submit);
  * shares anything raised for the principal while they are away as well;
  * adds a timeline comment on each approval the stand-in gives, naming both
    people and the handover;
  * refuses the stand-in approving their OWN request while acting, since they
    would otherwise be their own approver.

On return, the role and shares it added are taken away again.

KINDS OF APPROVAL come from the hook `task_assignment_authorities`, read from
each installed app's hooks module rather than `frappe.get_hooks`, because the
value is a nested dict and `get_hooks` reshapes those lossily (SEAL_DEV_RULES
§2.17):

    task_assignment_authorities = {
        "leave_approval": {
            "label": "Approving leave",
            "role": "Leave Approver",                     # optional; or "roles": [...]
            "holds": "dotted.path.fn",                    # fn(user) -> bool
            "pending": "dotted.path.fn",                  # fn(user) -> [(doctype, name)]
            "covers": ["other_kind"],                     # optional: kinds this one includes
            "enabled": True,                              # optional
        },
    }

A kind that `covers` others answers for them too. A Head of Department hands over
"their department's approvals" as one line, and anyone asking who approves leave
for them gets that stand-in. When it is offered, the kinds it covers are not
offered separately.

There is NO CHAINING. If the stand-in goes on leave too, what they approve for
someone else does not pass on to their own stand-in; a health check reports it.
"""

import json

import frappe
from frappe import _

from seal_hrms.seal_hrms.handover import ASSIGNMENT, Answer, Status, user_for_employee

REGISTRY_HOOK = "task_assignment_authorities"
AUTHORITY_ROW = "Task Assignment Authority"


# ---------------------------------------------------------------- registry


def registry() -> dict[str, frappe._dict]:
	"""Every enabled kind of approval declared by an installed app. First declaration of a key wins."""
	kinds = {}
	for app in frappe.get_installed_apps():
		try:
			module = frappe.get_module(f"{app}.hooks")
		except ImportError:
			continue
		declared = getattr(module, REGISTRY_HOOK, None)
		if not isinstance(declared, dict):
			continue
		for key, spec in declared.items():
			if isinstance(spec, dict) and spec.get("enabled", True) and key not in kinds:
				kinds[key] = frappe._dict(spec, key=key, app=app)
	return kinds


def _run(spec, hook: str, *args, default=None):
	"""Call one of a kind's functions. A broken subscriber must not break the handover."""
	path = spec.get(hook)
	if not path:
		return default
	try:
		return frappe.get_attr(path)(*args)
	except Exception:
		frappe.log_error(
			title=f"Task Assignment: approval kind {spec.key} failed",
			message=f"{spec.app} {hook} = {path}\n\n{frappe.get_traceback()}",
		)
		return default


def what_they_approve(user: str) -> list[frappe._dict]:
	"""The kinds of approval `user` gives, leaving out any a broader kind they hold already covers."""
	held = [spec for spec in registry().values() if _run(spec, "holds", user, default=False)]
	covered = {key for spec in held for key in (spec.get("covers") or [])}
	return [spec for spec in held if spec.key not in covered]


def kinds_answering(capacity: str) -> list[str]:
	"""The kinds whose stand-in acts in `capacity`: the kind itself, and any kind covering it."""
	return [key for key, spec in registry().items() if key == capacity or capacity in (spec.get("covers") or [])] or [capacity]


def roles_of(spec) -> list[str]:
	return list(spec.get("roles") or ([spec.role] if spec.get("role") else []))


@frappe.whitelist()
def suggest_authorities(employee: str) -> list[dict]:
	"""The approvals this member of staff gives, to fill a handover's Approvals table."""
	from seal_hrms.seal_hrms.task_assignment_access import can_prepare_for

	if not can_prepare_for(employee):
		frappe.throw(_("You can only prepare a handover for yourself."), frappe.PermissionError)
	user = user_for_employee(employee)
	if not user:
		return []
	return [{"authority": spec.key, "authority_label": _(spec.label)} for spec in what_they_approve(user)]


# ---------------------------------------------------------------- who is acting


def _active_rows(**where) -> list[frappe._dict]:
	"""Accepted approval rows on handovers in effect, with both people's logins."""
	conditions, values = [], {}
	for key, value in where.items():
		if key == "r.authority":
			# A broader kind (Head of Department) answers for the kinds it covers.
			conditions.append("r.authority in %(kinds)s")
			values["kinds"] = kinds_answering(value)
			continue
		conditions.append(f"{key} = %({key.replace('.', '_')})s")
		values[key.replace(".", "_")] = value
	extra = (" AND " + " AND ".join(conditions)) if conditions else ""
	return frappe.db.sql(
		f"""
		SELECT r.name AS row, r.authority, a.name AS assignment,
		       owner.user_id AS principal, stand_in.user_id AS stand_in
		FROM `tab{AUTHORITY_ROW}` r
		INNER JOIN `tab{ASSIGNMENT}` a ON a.name = r.parent AND r.parenttype = '{ASSIGNMENT}'
		INNER JOIN `tabEmployee` owner ON owner.name = a.employee
		INNER JOIN `tabEmployee` stand_in ON stand_in.name = IFNULL(NULLIF(r.task_assignee, ''), a.task_assignee)
		WHERE a.docstatus = 1 AND a.status = %(active)s AND r.acceptance = %(accepted)s{extra}
		""",
		{"active": Status.ACTIVE, "accepted": Answer.ACCEPTED, **values},
		as_dict=True,
	)


def acting_for(user: str) -> list[frappe._dict]:
	"""Whom `user` is approving for right now, and what: [{principal, authority, assignment, row}]."""
	return _active_rows(**{"stand_in.user_id": user})


def delegations(capacity: str) -> list[tuple[str, str]]:
	"""seal_common's `acting_delegation_providers` hook: (principal, stand-in) in force for a capacity.

	The capacity is the key of a kind of approval, so seal_buying's
	"accounting_officer" kind is answered here without seal_hrms knowing what an
	Accounting Officer is.
	"""
	return [(r.principal, r.stand_in) for r in _active_rows(**{"r.authority": capacity}) if r.principal and r.stand_in]


def _announce(capacity: str, principal: str, stand_in: str, started: bool) -> None:
	"""Tell other apps that someone started or stopped acting.

	seal_common is optional for seal_hrms, so it is imported here, only where
	installed. That is how an app that stamped the principal onto documents in
	flight gets to re-stamp them.
	"""
	if "seal_common" not in frappe.get_installed_apps():
		return
	from seal_common.delegation import announce

	announce(capacity, principal, stand_in, started)


def acting_stand_in(principal_user: str | None, authority: str) -> str | None:
	"""Who approves `authority` for `principal_user` right now. Direct stand-in only: no chaining."""
	if not principal_user:
		return None
	rows = _active_rows(**{"owner.user_id": principal_user, "r.authority": authority})
	return rows[0].stand_in if rows else None


# ---------------------------------------------------------------- grant and revoke


def _stand_in_user(assignment, row) -> str | None:
	return user_for_employee(row.task_assignee or assignment.task_assignee)


def _share(doctype: str, name: str, user: str) -> str | None:
	"""Share a document for approval. Returns the new share's name, or None if they already had one."""
	if frappe.db.exists("DocShare", {"share_doctype": doctype, "share_name": name, "user": user}):
		return None
	share = frappe.share.add_docshare(
		doctype, name, user, read=1, write=1, submit=1, flags={"ignore_share_permission": True}
	)
	return share.name if share else None


def _give_role(user: str, role: str) -> bool:
	"""Add a role for the leave window. Returns False if they already had it.

	Adds the Has Role row itself rather than saving the User: a User save can be
	refused by site governance, or reset roles to a role profile, neither of
	which is this handover's business.
	"""
	if role in frappe.get_roles(user):
		return False
	frappe.get_doc({
		"doctype": "Has Role", "parent": user, "parenttype": "User", "parentfield": "roles", "role": role,
	}).insert(ignore_permissions=True)
	frappe.clear_cache(user=user)
	return True


def _take_role(user: str, role: str) -> None:
	frappe.db.delete("Has Role", {"parent": user, "parenttype": "User", "role": role})
	frappe.clear_cache(user=user)


def grant_for(assignment) -> None:
	"""The handover has taken effect: give each accepted approval to its stand-in."""
	kinds = registry()
	for row in assignment.get("authorities") or []:
		if row.acceptance != Answer.ACCEPTED:
			continue
		spec = kinds.get(row.authority)
		stand_in = _stand_in_user(assignment, row)
		principal = user_for_employee(assignment.employee)
		if not (spec and stand_in and principal):
			continue
		added = [role for role in roles_of(spec) if _give_role(stand_in, role)]
		shares = [s for s in (_share(dt, dn, stand_in) for dt, dn in _run(spec, "pending", principal, default=[]) or []) if s]
		row.db_set({
			# Only the roles this handover added, so only those are taken back.
			"role_granted": ", ".join(added),
			"role_added_by_assignment": 1 if added else 0,
			"shares": json.dumps(shares),
		}, update_modified=False)
		assignment.add_comment("Info", _("{0} now approves {1} for {2}, until they are back.").format(
			frappe.utils.get_fullname(stand_in), _(spec.label).lower(), assignment.employee_name,
		))
		for capacity in [row.authority, *(spec.get("covers") or [])]:
			_announce(capacity, principal, stand_in, started=True)


def revoke_for(assignment) -> None:
	"""The owner is back: take away what the handover gave, and nothing it did not.

	Called once the handover is no longer Active, so anyone asking "who acts for
	this officer?" while re-stamping already gets the officer back.
	"""
	principal = user_for_employee(assignment.employee)
	for row in assignment.get("authorities") or []:
		stand_in = _stand_in_user(assignment, row)
		if not stand_in:
			continue
		if row.acceptance == Answer.ACCEPTED and principal:
			spec = registry().get(row.authority) or frappe._dict()
			for capacity in [row.authority, *(spec.get("covers") or [])]:
				_announce(capacity, principal, stand_in, started=False)
		for share in json.loads(row.shares or "[]"):
			if frappe.db.exists("DocShare", share):
				frappe.delete_doc("DocShare", share, ignore_permissions=True, flags={"ignore_share_permission": True})
		if row.role_added_by_assignment:
			for role in [r.strip() for r in (row.role_granted or "").split(",") if r.strip()]:
				if not _still_needed(stand_in, role, assignment.name):
					_take_role(stand_in, role)
		row.db_set({"shares": "[]", "role_added_by_assignment": 0}, update_modified=False)


def _still_needed(user: str, role: str, returning: str) -> bool:
	"""Another handover still in effect gave this person the same role."""
	return bool(frappe.db.sql(
		f"""
		SELECT 1 FROM `tab{AUTHORITY_ROW}` r
		INNER JOIN `tab{ASSIGNMENT}` a ON a.name = r.parent
		INNER JOIN `tabEmployee` s ON s.name = IFNULL(NULLIF(r.task_assignee, ''), a.task_assignee)
		WHERE a.status = %s AND a.name != %s AND s.user_id = %s
		  AND CONCAT(', ', r.role_granted, ',') LIKE %s AND r.role_added_by_assignment = 1
		LIMIT 1
		""",
		(Status.ACTIVE, returning, user, f"%, {role},%"),
	))


# ---------------------------------------------------------------- document events


def share_new_document(doc, approver_user: str | None, authority: str) -> None:
	"""Something raised for an absent approver reaches whoever approves in their place."""
	if doc.docstatus != 0:
		return
	rows = _active_rows(**{"owner.user_id": approver_user or "", "r.authority": authority})
	if not rows:
		return
	row = rows[0]
	share = _share(doc.doctype, doc.name, row.stand_in)
	if share:
		existing = json.loads(frappe.db.get_value(AUTHORITY_ROW, row.row, "shares") or "[]")
		frappe.db.set_value(AUTHORITY_ROW, row.row, "shares", json.dumps(existing + [share]), update_modified=False)


def refuse_self_approval(doc, applicant_employee: str, approver_user: str | None, authority: str) -> None:
	"""Whoever approves in someone's place may not approve their own request."""
	me = frappe.session.user
	if not approver_user or me == approver_user:
		return
	if acting_stand_in(approver_user, authority) != me:
		return
	if user_for_employee(applicant_employee) == me:
		frappe.throw(
			_("You are approving for {0} while they are away, but this request is your own. Someone else must approve it.").format(
				frappe.utils.get_fullname(approver_user)
			),
			title=_("Your Own Request"),
		)


def record_acting_approval(doc, approver_user: str | None, authority: str) -> None:
	"""Leave a timeline note when the approval came from someone acting for the approver."""
	me = frappe.session.user
	if not approver_user or me == approver_user:
		return
	rows = [r for r in _active_rows(**{"owner.user_id": approver_user, "r.authority": authority}) if r.stand_in == me]
	if not rows:
		return
	doc.add_comment("Info", _("Approved by {0}, acting for {1} during their leave ({2}).").format(
		frappe.utils.get_fullname(me), frappe.utils.get_fullname(approver_user), rows[0].assignment,
	))


# ---------------------------------------------------------------- HRMS kinds of approval


def holds_leave_approval(user: str) -> bool:
	return bool(
		frappe.db.exists("Employee", {"leave_approver": user, "status": "Active"})
		or frappe.db.exists("Department Approver", {"approver": user, "parentfield": "leave_approvers"})
	)


def pending_leave_approvals(user: str) -> list[tuple[str, str]]:
	return [("Leave Application", n) for n in frappe.get_all(
		"Leave Application", filters={"leave_approver": user, "docstatus": 0, "status": "Open"}, pluck="name"
	)]


def holds_expense_approval(user: str) -> bool:
	return bool(
		frappe.db.exists("Employee", {"expense_approver": user, "status": "Active"})
		or frappe.db.exists("Department Approver", {"approver": user, "parentfield": "expense_approvers"})
	)


def pending_expense_approvals(user: str) -> list[tuple[str, str]]:
	return [("Expense Claim", n) for n in frappe.get_all(
		"Expense Claim", filters={"expense_approver": user, "docstatus": 0, "approval_status": "Draft"}, pluck="name"
	)]


def holds_head_of_department(user: str) -> bool:
	"""Named on a department's own approver lists: the department head, not a line manager."""
	return bool(frappe.db.exists(
		"Department Approver", {"approver": user, "parentfield": ["in", ["leave_approvers", "expense_approvers"]]}
	))


def pending_head_of_department(user: str) -> list[tuple[str, str]]:
	return pending_leave_approvals(user) + pending_expense_approvals(user)
