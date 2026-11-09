# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""How a time off claim is agreed: names, the company's mode, and actions taken from code.

A claim moves by Frappe Workflow (`toil.workflow`, decision 2026-11-10): people
use the form's Actions menu. The functions below take the same actions from
code (tests, My Desk) through `toil.workflow.act`, which runs Frappe's own
`apply_workflow`; none is whitelisted, because the form does not need them.

Claim afterwards (the default):

    Draft / Returned --Send for Approval--> Waiting for Approval --Approve--> Approved (time added)
                                                                 --Reject---> Rejected
                                                                 --Return---> Returned

Authorise first, then confirm the hours (a company's choice, stamped on the claim as `mode`):

    Draft / Returned --Send for Authorisation--> Waiting for Authorisation --Authorise--> Authorised
                                                                            --Return / Reject
    Authorised --Send for Approval--> Waiting for Approval --Approve--> Approved
                                                            --Return---> Authorised
                                                            --Reject---> Rejected

Approvers do not change hours: they return the claim with a reason (decision D14).
"""

import frappe

from seal_hrms.seal_hrms.toil import access
from seal_hrms.seal_hrms.toil import workflow as wf
from seal_hrms.seal_hrms.toil.workflow import (  # noqa: F401  the names other modules use
	APPROVED,
	AUTHORISED,
	CANCELLED,
	DRAFT,
	REJECTED,
	RETURNED,
	WAITING,
	WAITING_AUTH,
	WAITING_STATES,
)
from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST, policy_for

CLAIM = "Time Off in Lieu Claim"


def authorise_first(doc) -> bool:
	return doc.get("mode") == AUTHORISE_FIRST


@frappe.whitelist()
def mode_for(employee: str) -> str:
	"""How extra work is agreed at this person's company, for a claim not yet saved. Reads only."""
	access.require_self_or_hr(employee)
	return policy_for(frappe.db.get_value("Employee", employee, "company")).prior_authorisation


def send_for_authorisation(name: str) -> str:
	return wf.act(name, wf.SEND_AUTH).status


def authorise(name: str) -> str:
	return wf.act(name, wf.AUTHORISE).status


def send_for_approval(name: str) -> str:
	return wf.act(name, wf.SEND).status


def approve(name: str) -> str:
	return wf.act(name, wf.APPROVE).status


def reject(name: str, reason: str | None = None) -> str:
	return wf.act(name, wf.REJECT, reason or "").status


def return_claim(name: str, reason: str | None = None) -> str:
	return wf.act(name, wf.RETURN, reason or "").status
