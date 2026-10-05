# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Per company: whether leave needs an agreed stand-in before it can be approved."""

import frappe
from frappe.model.document import Document
from frappe.utils import flt

OFF = "Off"
WARN = "Warn"
REQUIRE_ON_APPROVAL = "Require on Approval"
REQUIRE_ON_SUBMISSION = "Require on Submission"
REQUIRE_ACCEPTANCE_BEFORE_SUBMISSION = "Require Acceptance before Submission"
REQUIRE = "Require"  # legacy alias for Require on Approval


class TaskAssignmentPolicy(Document):
	pass


def is_required_on_approval(policy) -> bool:
	return policy.requirement in (REQUIRE_ON_APPROVAL, REQUIRE)


def is_required_on_submission(policy) -> bool:
	return policy.requirement in (REQUIRE_ON_SUBMISSION, REQUIRE_ACCEPTANCE_BEFORE_SUBMISSION)


def is_acceptance_required_before_submission(policy) -> bool:
	return policy.requirement == REQUIRE_ACCEPTANCE_BEFORE_SUBMISSION


@frappe.whitelist()
def policy_for(company: str | None = None) -> dict:
	"""Fetch Leave Handover policy directly from HR Settings. Default is always 'Require on Submission'."""
	requirement = frappe.db.get_single_value("HR Settings", "custom_leave_handover_requirement")
	min_days = flt(frappe.db.get_single_value("HR Settings", "custom_leave_handover_min_days"))

	if not requirement:
		requirement = REQUIRE_ON_SUBMISSION

	return frappe._dict(
		name="HR Settings",
		requirement=requirement,
		min_days=min_days,
		leave_types=[],
	)


def applies_to(policy, leave_type: str, days) -> bool:
	"""Whether the handover rule bites on this leave: switched on, and the kind and length it covers."""
	if policy.requirement == OFF:
		return False
	return covers(policy, leave_type, days)


def covers(policy, leave_type: str, days) -> bool:
	"""Whether this leave is the kind, and length, the policy is about, whatever the approval/submission rule."""
	if policy.leave_types and leave_type not in policy.leave_types:
		return False
	return flt(days) >= flt(policy.min_days)

