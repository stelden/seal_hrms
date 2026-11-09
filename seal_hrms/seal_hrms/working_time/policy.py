# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Read a company's Working Time Policy, with defaults where there is none.

One policy per company, named after it. Callers never read the doctype
directly, so a company without a policy behaves as "nothing switched on" and
every number has one default.
"""

import frappe

POLICY = "Working Time Policy"
LAST_DAY_WORKED = "The last day worked"
DAY_APPROVED = "The day the claim is approved"

DEFAULTS = {
	"hours_per_day": 8.0,
	"toil_enabled": 0,
	"leave_type": None,
	"after_hours_rate": 1.0,
	"rest_day_rate": 1.0,
	"public_holiday_rate": 1.0,
	"minimum_hours": 1.0,
	"daily_cap": 0.0,
	"validity_days": 90,
	"lapse_counted_from": LAST_DAY_WORKED,
	"claim_within_days": 30,
	"balance_cap": 0.0,
	"evidence_attendance": 1,
	"evidence_timesheets": 1,
}


def policy_for(company: str | None) -> frappe._dict:
	"""The company's rules as a plain dict; a missing policy means defaults, with time off switched off."""
	policy = frappe._dict(DEFAULTS, company=company, eligible_grades=[], exists=False)
	if not company or not frappe.db.exists(POLICY, company):
		return policy
	# Read fresh: a cached copy outlives a rolled-back save of the policy.
	doc = frappe.get_doc(POLICY, company)
	for field in DEFAULTS:
		value = doc.get(field)
		if value is not None:
			policy[field] = value
	policy.eligible_grades = [row.grade for row in doc.get("eligible_grades") or [] if row.grade]
	policy.exists = True
	return policy


def toil_leave_types() -> set[str]:
	"""Leave types that some company banks time off in lieu into."""
	if not frappe.db.table_exists(POLICY):
		return set()  # before the migrate that brings the doctype
	return set(
		frappe.get_all(POLICY, filters={"toil_enabled": 1, "leave_type": ["is", "set"]}, pluck="leave_type")
	)


def toil_companies() -> list[str]:
	if not frappe.db.table_exists(POLICY):
		return []
	return frappe.get_all(POLICY, filters={"toil_enabled": 1}, pluck="company")
