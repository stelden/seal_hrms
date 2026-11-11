# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Travel requests: staff ask, their line manager decides (Keith, 2026-11-11: Travel Request in Self Service).

Frappe HR's Travel Request has no status, no approver and, as shipped, permissions for
System Manager only. seal_hrms never changes Frappe HR, so what staff and managers need is
given to a site, never forced on it:

  * **A Frappe Workflow** "Travel Request" (SEAL_DEV_RULES §1.23): Draft, Pending Approval,
    Approved (submitted), Rejected (submitted), Cancelled. Created once after migrate when the
    site has no workflow for travel requests, then the site's to change; a site that already
    runs its own keeps it. The workflow keeps its state in its own `workflow_state` field.
  * **Permissions**, once each, never overwritten: Employee may read, write, create and delete
    (the workflow keeps a sent request out of their hands); Line Manager may read, write and
    submit, which is what deciding needs. HR keeps whatever the site gives it.
  * **Who sees what** (`has_permission`, `query_conditions`, SEAL_DEV_RULES §3.4): a person whose
    only way into travel requests is Employee, Employee Self Service or Line Manager sees their
    own requests and those of the people who report to them (`Employee.reports_to`), nothing
    else. Anyone the site lets in another way (HR, a travel desk) is not narrowed.
    Frappe HR gives every member of staff a User Permission on their own Employee record, which
    would hide a report's request from their manager however the rules above read; so the
    request's Employee field ignores User Permissions (a Property Setter, created once) and these
    two rules do the scoping instead. A Company User Permission still applies.
  * **The decider** (`validate`): never the person travelling. The line manager is the one the
    phone names (EM-3); HR may decide any from the desk.

The phone's screens are `seal_hrms.my_desk.api.travel_*`.
"""

from __future__ import annotations

import frappe
from frappe import _

DOCTYPE = "Travel Request"
WORKFLOW = "Travel Request"
STATE_FIELD = "workflow_state"

DRAFT, WAITING, APPROVED, REJECTED, CANCELLED = "Draft", "Pending Approval", "Approved", "Rejected", "Cancelled"
SEND, APPROVE, REJECT, CANCEL = "Send for Approval", "Approve", "Reject", "Cancel"
DECIDED = (APPROVED, REJECTED)

LINE_MANAGER = "Line Manager"
SENDERS = ("Employee", "Employee Self Service", "HR User", "HR Manager")
DECIDERS = (LINE_MANAGER, "HR User", "HR Manager")
#: Roles whose way into travel requests is only their own (and their team's): narrowed by `has_permission`.
NARROW = frozenset({"Employee", "Employee Self Service", LINE_MANAGER})

#: (state, doc_status, who may edit in it, style)
STATES = (
	(DRAFT, "0", "Employee", ""),
	(WAITING, "0", "HR Manager", "Primary"),
	(APPROVED, "1", "HR Manager", "Success"),
	(REJECTED, "1", "HR Manager", "Danger"),
	(CANCELLED, "2", "HR Manager", "Inverse"),
)

#: (from, action, to, roles, self approval)
TRANSITIONS = (
	(DRAFT, SEND, WAITING, SENDERS, 1),
	(WAITING, APPROVE, APPROVED, DECIDERS, 0),
	(WAITING, REJECT, REJECTED, DECIDERS, 0),
	(APPROVED, CANCEL, CANCELLED, ("HR User", "HR Manager"), 1),
)

#: role -> rights given once on a site (Custom DocPerm, permission level 0)
PERMISSIONS = {
	"Employee": ("read", "write", "create", "delete", "print"),
	LINE_MANAGER: ("read", "write", "submit", "print"),
}
#: what a line manager may do with a direct report's request (never create or delete it)
MANAGER_RIGHTS = frozenset({"read", "select", "print", "email", "write", "submit"})


# ---------------------------------------------------------------- set-up (after migrate, after_sync)


def ensure_setup() -> None:
	"""Create the workflow and the permissions where the site has none. Never changes what exists."""
	try:
		if not frappe.db.table_exists(DOCTYPE):
			return
		ensure_permissions()
		ensure_workflow()
	except Exception:
		# Optional work: a failure must not stop the migrate; App Health reports what is missing.
		frappe.log_error(title="Travel requests: set-up not finished", message=frappe.get_traceback())


def ensure_permissions() -> None:
	"""Give Employee and Line Manager their rights on travel requests, once (a site's later edits stand)."""
	from frappe.permissions import setup_custom_perms

	if not frappe.db.exists("Role", LINE_MANAGER):
		from seal_hrms.seal_hrms.line_manager import ensure_role

		ensure_role()
	setup_custom_perms(DOCTYPE)  # the shipped rules first, or a new rule would replace them all
	added = False
	if not frappe.db.exists(
		"Property Setter", {"doc_type": DOCTYPE, "field_name": "employee", "property": "ignore_user_permissions"}
	):
		from frappe.custom.doctype.property_setter.property_setter import make_property_setter

		# Who may see whose request is `has_permission`'s rule; the manager's own Employee
		# User Permission must not hide their team's requests (see the module docstring).
		make_property_setter(
			DOCTYPE, "employee", "ignore_user_permissions", 1, "Check", validate_fields_for_doctype=False, is_system_generated=False
		)
		added = True
	for role, rights in PERMISSIONS.items():
		if frappe.db.exists("Custom DocPerm", {"parent": DOCTYPE, "role": role, "permlevel": 0}):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": DOCTYPE,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": role,
				"permlevel": 0,
				**{right: 1 for right in rights},
			}
		).insert(ignore_permissions=True)
		added = True
	if added:
		frappe.clear_cache(doctype=DOCTYPE)


def ensure_workflow() -> None:
	"""The states, actions and workflow, if the site has no workflow for travel requests."""
	for state, _status, _edit, style in STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": style}).insert(
				ignore_permissions=True
			)
	for action in {t[1] for t in TRANSITIONS}:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)
	if frappe.db.exists("Workflow", {"document_type": DOCTYPE}):
		return
	workflow = frappe.new_doc("Workflow")
	workflow.update(
		{
			"workflow_name": WORKFLOW,
			"document_type": DOCTYPE,
			"workflow_state_field": STATE_FIELD,
			"is_active": 1,
			"send_email_alert": 1,  # the line manager is told a request waits for them
		}
	)
	for state, doc_status, allow_edit, _style in STATES:
		workflow.append("states", {"state": state, "doc_status": doc_status, "allow_edit": allow_edit})
	for state, action, next_state, roles, self_approval in TRANSITIONS:
		for role in roles:
			workflow.append(
				"transitions",
				{"state": state, "action": action, "next_state": next_state, "allowed": role, "allow_self_approval": self_approval},
			)
	workflow.insert(ignore_permissions=True)


def problems() -> list[str]:
	"""What stops travel requests being sent or decided on the phone."""
	from frappe.model.workflow import get_workflow_name

	if not frappe.db.table_exists(DOCTYPE):
		return []
	out = []
	name = get_workflow_name(DOCTYPE)
	if not name:
		out.append(_("There is no active approval workflow for travel requests, so staff cannot send one."))
	else:
		workflow = frappe.get_cached_doc("Workflow", name)
		states = {row.state for row in workflow.states}
		actions = {row.action for row in workflow.transitions}
		if WAITING not in states or SEND not in actions:
			out.append(_("The travel request workflow has no \"{0}\" step, so the phone cannot send requests.").format(WAITING))
	if not frappe.db.exists("Custom DocPerm", {"parent": DOCTYPE, "role": "Employee", "read": 1}) and not frappe.db.exists(
		"DocPerm", {"parent": DOCTYPE, "role": "Employee", "read": 1}
	):
		out.append(_("Staff cannot open travel requests: the Employee role has no access to them."))
	if not frappe.db.exists("Custom DocPerm", {"parent": DOCTYPE, "role": LINE_MANAGER, "submit": 1}):
		out.append(_("Line managers cannot decide travel requests: the Line Manager role has no right to approve them."))
	return out


# ---------------------------------------------------------------- who is who


def user_of(employee: str | None) -> str | None:
	return frappe.db.get_value("Employee", employee, "user_id") if employee else None


def manager_user_of(employee: str | None) -> str | None:
	"""The user of the person `employee` reports to: the one who decides their travel (EM-3)."""
	manager = frappe.db.get_value("Employee", employee, "reports_to") if employee else None
	return user_of(manager)


def is_narrowed(user: str) -> bool:
	"""Whether `user` reaches travel requests only as staff or line manager (then: own and team only)."""
	if user == "Administrator":
		return False
	roles = set(frappe.get_roles(user))
	wide = {p.role for p in frappe.get_meta(DOCTYPE).permissions if p.permlevel == 0 and p.read and p.role not in NARROW}
	return not (roles & wide)


# ---------------------------------------------------------------- who sees what (SEAL_DEV_RULES §3.4)


def has_permission(doc, ptype=None, user=None) -> bool:
	"""Own requests, and a direct report's (to read and decide); everything for anyone not narrowed."""
	user = user or frappe.session.user
	if not is_narrowed(user):
		return True
	employee = doc.get("employee")
	if not employee:
		return True  # a new request: the controller requires the employee, and it is checked again then
	if user_of(employee) == user:
		return True
	if manager_user_of(employee) == user:
		return (ptype or "read") in MANAGER_RIGHTS
	return False


def query_conditions(user: str | None = None) -> str:
	"""Lists: own requests and direct reports' requests, for narrowed users; nothing more."""
	user = user or frappe.session.user
	if not is_narrowed(user):
		return ""
	u = frappe.db.escape(user)
	return (
		f"`tab{DOCTYPE}`.`employee` in (select e.name from `tabEmployee` e where e.user_id = {u} "
		f"or e.reports_to in (select m.name from `tabEmployee` m where m.user_id = {u}))"
	)


# ---------------------------------------------------------------- the decider (validate)


def validate(doc, method=None) -> None:
	"""Refuse a decision by the person travelling, whoever else the workflow lets decide."""
	if not doc.meta.has_field(STATE_FIELD):
		return
	before = doc.get_doc_before_save()
	state = doc.get(STATE_FIELD)
	if not before or before.get(STATE_FIELD) == state or state not in DECIDED:
		return
	if frappe.session.user != "Administrator" and user_of(doc.employee) == frappe.session.user:
		frappe.throw(_("This is your own travel request. Someone else must decide it."), frappe.PermissionError)
