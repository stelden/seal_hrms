# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Create the Leave Plan Approval workflow as a template (INACTIVE by default).

Per SPEC §5.2: ships as a Frappe Workflow record with all states and
transitions wired up, but `is_active = 0`. Clients enable it via the
Workflow Builder when ready, or override the transitions with their own.

Why inactive: the LeavePlan controller is workflow-tolerant. With the
workflow inactive, plans submit normally (Draft -> Approved via direct
submit). Activating the workflow forces submissions through Manager + HR.

Idempotent: if the workflow already exists, no changes are made.

Reference: dev_notes/seal_hrms/LEAVE_PLANNING_SPEC.md §5.2
"""

import frappe


_WORKFLOW_NAME = "Leave Plan Approval"
_DOCTYPE = "Leave Plan"

_STATES = [
	("Draft",            "Primary",   "0", "Employee Self Service"),
	("Pending Manager",  "Warning",   "0", "Leave Approver"),
	("Pending HR",       "Warning",   "0", "HR User"),
	("Returned",         "Danger",    "0", "Employee Self Service"),
	("Approved",         "Success",   "1", "HR User"),
	("Cancelled",        "Inverse",   "2", "HR User"),
]

_ACTIONS = [
	"Submit for Manager Approval",
	"Approve as Manager",
	"Return to Employee",
	"Approve as HR",
	"Resubmit",
	"Cancel",
]

_TRANSITIONS = [
	("Draft",           "Submit for Manager Approval", "Pending Manager", "Employee Self Service", None),
	("Pending Manager", "Approve as Manager",          "Pending HR",      "Leave Approver",        "doc.leave_approver == frappe.session.user"),
	("Pending Manager", "Return to Employee",          "Returned",        "Leave Approver",        "doc.leave_approver == frappe.session.user"),
	("Pending HR",      "Approve as HR",               "Approved",        "HR User",               None),
	("Pending HR",      "Return to Employee",          "Returned",        "HR User",               None),
	("Returned",        "Resubmit",                    "Pending Manager", "Employee Self Service", None),
]


def execute():
	if frappe.db.exists("Workflow", _WORKFLOW_NAME):
		frappe.logger().info(f"[seal_hrms.v1_3] {_WORKFLOW_NAME} already exists; skipping")
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
	frappe.logger().info(
		f"[seal_hrms.v1_3] created {_WORKFLOW_NAME} workflow (inactive). "
		f"Enable via the Workflow Builder when ready."
	)
