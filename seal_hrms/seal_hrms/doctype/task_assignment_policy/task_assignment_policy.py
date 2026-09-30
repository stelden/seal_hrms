# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Per company: whether leave needs an agreed stand-in before it can be approved."""

import frappe
from frappe.model.document import Document
from frappe.utils import flt

OFF, WARN, REQUIRE = "Off", "Warn", "Require"


class TaskAssignmentPolicy(Document):
	pass


def policy_for(company: str | None) -> frappe._dict:
	"""The company's policy, or Off when it has none. Never raises."""
	row = frappe.db.get_value(
		"Task Assignment Policy",
		{"company": company} if company else {"name": ""},
		["name", "requirement", "min_days", "prep_reminder_days", "email_prep_reminder"],
		as_dict=True,
	)
	if not row:
		return frappe._dict(
			name=None, requirement=OFF, min_days=0, prep_reminder_days=7, email_prep_reminder=0, leave_types=set()
		)
	row.leave_types = set(
		frappe.get_all(
			"Task Assignment Policy Leave Type",
			filters={"parent": row.name, "parenttype": "Task Assignment Policy"},
			pluck="leave_type",
		)
	)
	row.min_days = flt(row.min_days)
	return row


def applies_to(policy, leave_type: str, days) -> bool:
	"""Whether the approval rule bites on this leave: switched on, and the kind and length it covers."""
	if policy.requirement == OFF:
		return False
	return covers(policy, leave_type, days)


def covers(policy, leave_type: str, days) -> bool:
	"""Whether this leave is the kind, and length, the policy is about, whatever the approval rule."""
	if policy.leave_types and leave_type not in policy.leave_types:
		return False
	return flt(days) >= flt(policy.min_days)
