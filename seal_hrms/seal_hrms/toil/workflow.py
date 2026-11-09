# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""The Frappe Workflow that moves a time off claim, and the little it needs from code.

The states, the actions (the form's Actions menu), which role may take each, the
company's "authorise first" branch (conditions on `doc.mode`), submitting on
Approve or Reject and cancelling on Cancel all live in a Frappe Workflow named
"Time Off in Lieu Claim" (decision 2026-11-10, WORKING_TIME_DESIGN.md §9i). It is
created once after migrate and never overwritten, so a site can add a step or
reword an action; App Health reports one that no longer has what the code needs.

What a workflow cannot do stays in code: the claim's named approver (or their
stand-in) decides, never the claimant (the controller's validate); the reason on
Return or Reject, saved before the action because Frappe reloads the claim first
(`set_decision_note`, as seal_iam does); the lock while waiting; and the side
effects (toil.ledger, toil.lapse, toil.notifications).
"""

import frappe
from frappe import _

from seal_hrms.seal_hrms.toil import access
from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST

CLAIM = "Time Off in Lieu Claim"
WORKFLOW = "Time Off in Lieu Claim"

DRAFT, RETURNED, WAITING = "Draft", "Returned", "Waiting for Approval"
WAITING_AUTH, AUTHORISED = "Waiting for Authorisation", "Authorised"
APPROVED, REJECTED, CANCELLED = "Approved", "Rejected", "Cancelled"
WAITING_STATES = (WAITING, WAITING_AUTH)

SEND, SEND_AUTH, AUTHORISE, APPROVE, RETURN, REJECT, CANCEL = (
	"Send for Approval",
	"Send for Authorisation",
	"Authorise",
	"Approve",
	"Return",
	"Reject",
	"Cancel",
)

FIRST = f'doc.mode == "{AUTHORISE_FIRST}"'
AFTER = f'doc.mode != "{AUTHORISE_FIRST}"'
SENDERS = ("Employee", "HR User", "HR Manager")
DECIDERS = ("Leave Approver", "HR User", "HR Manager")

#: (state, doc_status, who may edit in it, style)
STATES = (
	(DRAFT, "0", "Employee", ""),
	(WAITING_AUTH, "0", "HR Manager", "Primary"),
	(AUTHORISED, "0", "Employee", "Info"),
	(WAITING, "0", "HR Manager", "Primary"),
	(RETURNED, "0", "Employee", "Warning"),
	(APPROVED, "1", "HR Manager", "Success"),
	(REJECTED, "1", "HR Manager", "Danger"),
	(CANCELLED, "2", "HR Manager", "Inverse"),
)

#: (from, action, to, roles, condition, self approval)
TRANSITIONS = (
	(DRAFT, SEND, WAITING, SENDERS, AFTER, 1),
	(RETURNED, SEND, WAITING, SENDERS, AFTER, 1),
	(DRAFT, SEND_AUTH, WAITING_AUTH, SENDERS, FIRST, 1),
	(RETURNED, SEND_AUTH, WAITING_AUTH, SENDERS, FIRST, 1),
	(WAITING_AUTH, AUTHORISE, AUTHORISED, DECIDERS, None, 0),
	(WAITING_AUTH, RETURN, RETURNED, DECIDERS, None, 0),
	(WAITING_AUTH, REJECT, REJECTED, DECIDERS, None, 0),
	(AUTHORISED, SEND, WAITING, SENDERS, FIRST, 1),
	(WAITING, APPROVE, APPROVED, DECIDERS, None, 0),
	(WAITING, RETURN, RETURNED, DECIDERS, AFTER, 0),
	(WAITING, RETURN, AUTHORISED, DECIDERS, FIRST, 0),
	(WAITING, REJECT, REJECTED, DECIDERS, None, 0),
	(APPROVED, CANCEL, CANCELLED, ("HR User", "HR Manager"), None, 1),
)

#: States the code moves claims through; a site's workflow must keep them.
NEEDED = {DRAFT, WAITING, RETURNED, APPROVED, REJECTED, CANCELLED, WAITING_AUTH, AUTHORISED}


def ensure_workflow() -> None:
	"""after_migrate: create the states, actions and the workflow if the site has none for claims.

	An existing workflow is the site's, and is left as it is.
	"""
	try:
		if not frappe.db.table_exists(CLAIM):
			return
		styles = {state: style for state, _status, _edit, style in STATES}
		for state, style in styles.items():
			if not frappe.db.exists("Workflow State", state):
				frappe.get_doc(
					{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
				).insert(ignore_permissions=True)
		for action in {t[1] for t in TRANSITIONS}:
			if not frappe.db.exists("Workflow Action Master", action):
				frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
					ignore_permissions=True
				)
		if frappe.db.exists("Workflow", {"document_type": CLAIM}):
			return
		workflow = frappe.new_doc("Workflow")
		workflow.update(
			{
				"workflow_name": WORKFLOW,
				"document_type": CLAIM,
				"workflow_state_field": "status",
				"is_active": 1,
				"send_email_alert": 0,  # ours go to the named approver only (toil.notifications)
			}
		)
		for state, doc_status, allow_edit, _style in STATES:
			workflow.append("states", {"state": state, "doc_status": doc_status, "allow_edit": allow_edit})
		for state, action, next_state, roles, condition, self_approval in TRANSITIONS:
			for role in roles:
				workflow.append(
					"transitions",
					{
						"state": state,
						"action": action,
						"next_state": next_state,
						"allowed": role,
						"condition": condition,
						"allow_self_approval": self_approval,
					},
				)
		workflow.insert(ignore_permissions=True)
	except Exception:
		# Optional work: a failure must not stop the migrate; App Health reports a missing workflow.
		frappe.log_error(title="Time off in lieu: workflow not created", message=frappe.get_traceback())


def problems() -> list[str]:
	"""What stops claims moving: no active workflow, or one without a state the code relies on."""
	from frappe.model.workflow import get_workflow_name

	name = get_workflow_name(CLAIM)
	if not name:
		return [_("There is no active workflow for time off claims, so none can be sent or decided.")]
	workflow = frappe.get_cached_doc("Workflow", name)
	if workflow.workflow_state_field != "status":
		return [
			_("The claims workflow keeps its state in {0}, not in the claim's status.").format(
				workflow.workflow_state_field
			)
		]
	missing = NEEDED - {row.state for row in workflow.states}
	return [_("The claims workflow has no state {0}.").format(state) for state in sorted(missing)]


# ---------------------------------------------------------------- the reason


@frappe.whitelist(methods=["POST"])
def set_decision_note(name: str, note: str | None = None) -> None:
	"""The approver's reason, saved before Return or Reject (Frappe reloads the claim before acting)."""
	doc = frappe.get_doc(CLAIM, name)
	doc.check_permission("read")
	access.require_decider(doc)
	if doc.docstatus != 0 or doc.status not in WAITING_STATES:
		frappe.throw(_("This claim is not waiting for a decision."))
	doc.db_set("decision_note", (note or "").strip() or None, update_modified=False)


# ---------------------------------------------------------------- acting from code


def act(name: str, action: str, reason: str | None = None):
	"""Take a workflow action on a claim as the session user, as the form's Actions menu does.

	For tests, My Desk and other code; people use the form. A reason, where given,
	is saved first, as the form does.
	"""
	from frappe.model.workflow import apply_workflow, get_transitions

	doc = frappe.get_doc(CLAIM, name)
	doc.check_permission("read")
	if action not in {t.action for t in get_transitions(doc)}:
		frappe.throw(_("You cannot {0} this claim at this stage.").format(_(action)), frappe.PermissionError)
	if reason is not None:
		set_decision_note(name, reason)
	return apply_workflow(doc.as_dict(), action)
