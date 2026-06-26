# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Create the Expense Requisition Approval workflow as a template (INACTIVE by default).

Staff raise a requisition (Draft), submit it for approval (Pending Approval); an approver
approves it (Approved = submitted, docstatus 1) which books the accrual, or rejects it back.

Ships inactive: the controller is workflow-tolerant, so with the workflow off a requisition
submits directly (Draft -> Approved). Clients enable + tailor roles via the Workflow Builder.

Idempotent: if the workflow already exists, nothing changes.
"""

import frappe

_WORKFLOW_NAME = "Expense Requisition Approval"
_DOCTYPE = "Expense Requisition"

_STATES = [
	("Draft",            "Primary", "0", "Employee Self Service"),
	("Pending Approval", "Warning", "0", "Expense Approver"),
	("Rejected",         "Danger",  "0", "Employee Self Service"),
	("Approved",         "Success", "1", "Expense Approver"),
	("Cancelled",        "Inverse", "2", "Expense Approver"),
]

_ACTIONS = ["Submit for Approval", "Approve", "Reject", "Resubmit"]

_TRANSITIONS = [
	("Draft",            "Submit for Approval", "Pending Approval", "Employee Self Service", None),
	("Pending Approval", "Approve",             "Approved",         "Expense Approver",      None),
	("Pending Approval", "Reject",              "Rejected",         "Expense Approver",      None),
	("Rejected",         "Resubmit",            "Pending Approval", "Employee Self Service", None),
]


def execute():
	if frappe.db.exists("Workflow", _WORKFLOW_NAME):
		frappe.logger().info(f"[seal_hrms.v1_4] {_WORKFLOW_NAME} already exists; skipping")
		return

	for state, style, _doc_status, _allow in _STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({
				"doctype": "Workflow State",
				"workflow_state_name": state,
				"style": style,
			}).insert(ignore_permissions=True)

	for action in _ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({
				"doctype": "Workflow Action Master",
				"workflow_action_name": action,
			}).insert(ignore_permissions=True)

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = _WORKFLOW_NAME
	workflow.document_type = _DOCTYPE
	workflow.workflow_state_field = "workflow_state"
	workflow.is_active = 0
	workflow.send_email_alert = 0

	for state, _style, doc_status, allow_edit in _STATES:
		workflow.append("states", {
			"state": state,
			"doc_status": doc_status,
			"allow_edit": allow_edit,
		})

	for state, action, next_state, allowed, condition in _TRANSITIONS:
		row = workflow.append("transitions", {
			"state": state,
			"action": action,
			"next_state": next_state,
			"allowed": allowed,
			"allow_self_approval": 0,
		})
		if condition:
			row.condition = condition

	workflow.flags.ignore_permissions = True
	workflow.insert(ignore_permissions=True)
	frappe.logger().info(f"[seal_hrms.v1_4] created {_WORKFLOW_NAME} workflow (inactive).")
