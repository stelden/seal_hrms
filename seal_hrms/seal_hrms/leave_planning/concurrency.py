# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Leave Concurrency Rule evaluator.

Pure read functions — no DB writes. Called from Leave Plan's before_submit
gate. Implements SPEC §4.6 evaluation algorithm.

Aggregation modes:
  - "Any Day": current implementation. Checks plain date-range overlap.
  - "Calendar Week": NOT IMPLEMENTED YET — falls back to "Any Day". TODO Phase 3.
"""

from math import ceil

import frappe
from frappe.utils import getdate, today


def evaluate_slot(slot_doc, plan_doc) -> list[dict]:
	"""Evaluate all applicable Leave Concurrency Rules against the proposed slot.

	Returns a list of violations. Empty list = no violation.
	Each violation is a dict: rule, rule_name, scope_label, current, proposed, max, message.
	"""
	rules = _get_applicable_rules(plan_doc.company, slot_doc.leave_type)
	violations = []

	for rule in rules:
		scope_emp_set = _resolve_scope_employees(rule)
		if not scope_emp_set or plan_doc.employee not in scope_emp_set:
			continue

		overlapping_emps = _find_overlapping_employees(
			leave_type=slot_doc.leave_type,
			from_date=slot_doc.from_date,
			to_date=slot_doc.to_date,
			scope_emp_set=scope_emp_set,
			exclude_plan=plan_doc.name,
		)
		proposed_count = len(overlapping_emps) + 1

		effective_max = _compute_effective_max(rule, len(scope_emp_set))

		if proposed_count > effective_max:
			scope_label = _rule_scope_label(rule)
			violations.append({
				"rule": rule.name,
				"rule_name": rule.rule_name,
				"scope_label": scope_label,
				"current": len(overlapping_emps),
				"proposed": proposed_count,
				"max": effective_max,
				"message": (
					f"Slot {slot_doc.from_date} to {slot_doc.to_date} ({slot_doc.leave_type}) "
					f"would exceed concurrency cap '{rule.rule_name}' for {scope_label}: "
					f"{proposed_count} planned vs cap of {effective_max}."
				),
			})

	return violations


def _get_applicable_rules(company: str, leave_type: str):
	today_d = today()
	rules = frappe.db.sql(
		"""
		SELECT * FROM `tabLeave Concurrency Rule`
		WHERE company = %(company)s
		  AND enabled = 1
		  AND (leave_type = %(leave_type)s OR leave_type IS NULL OR leave_type = '')
		  AND effective_from <= %(today)s
		  AND (effective_to IS NULL OR effective_to >= %(today)s)
		ORDER BY priority ASC
		""",
		{"company": company, "leave_type": leave_type, "today": today_d},
		as_dict=True,
	)
	return rules


def _resolve_scope_employees(rule) -> set[str]:
	"""Set of employee names in the rule's scope, restricted to Active employees in the rule's company."""
	filters = {"status": "Active", "company": rule.company}

	if rule.scope_type == "Company":
		pass
	elif rule.scope_type == "Department" and rule.department:
		filters["department"] = rule.department
	elif rule.scope_type == "Branch" and rule.branch:
		filters["branch"] = rule.branch
	elif rule.scope_type == "Designation" and rule.designation:
		filters["designation"] = rule.designation
	elif rule.scope_type == "Employee Group" and rule.employee_group:
		group_emps = frappe.get_all(
			"Employee Group Table",
			filters={"parent": rule.employee_group},
			pluck="employee",
		)
		if not group_emps:
			return set()
		filters["name"] = ["in", group_emps]
	else:
		return set()

	emps = frappe.get_all("Employee", filters=filters, pluck="name")
	return set(emps)


def _find_overlapping_employees(
	leave_type: str, from_date, to_date, scope_emp_set: set[str], exclude_plan: str | None
) -> set[str]:
	"""Distinct employees in scope_emp_set with submitted plan slots of leave_type
	whose date range overlaps [from_date, to_date], excluding the given plan.
	"""
	if not scope_emp_set:
		return set()

	conditions = ["lp.docstatus = 1", "lps.leave_type = %(leave_type)s", "lps.slot_status != 'Cancelled'"]
	params = {
		"leave_type": leave_type,
		"from_date": getdate(from_date),
		"to_date": getdate(to_date),
		"emps": tuple(scope_emp_set),
	}

	conditions.append("lp.employee IN %(emps)s")
	conditions.append("lps.from_date <= %(to_date)s AND lps.to_date >= %(from_date)s")

	if exclude_plan:
		conditions.append("lp.name != %(exclude_plan)s")
		params["exclude_plan"] = exclude_plan

	rows = frappe.db.sql(
		f"""
		SELECT DISTINCT lp.employee
		FROM `tabLeave Plan Slot` lps
		JOIN `tabLeave Plan` lp ON lp.name = lps.parent
		WHERE {' AND '.join(conditions)}
		""",
		params,
	)
	return {r[0] for r in rows}


def _compute_effective_max(rule, scope_size: int) -> float:
	"""The smaller of absolute and percent caps applies. If neither set, no cap (inf)."""
	abs_max = float(rule.max_concurrent_absolute or 0)
	pct = float(rule.max_concurrent_percent or 0)

	pct_limit = 0
	if pct > 0 and scope_size > 0:
		pct_limit = max(1, ceil(scope_size * pct / 100.0))

	if abs_max and pct_limit:
		return min(abs_max, pct_limit)
	if abs_max:
		return abs_max
	if pct_limit:
		return pct_limit
	return float("inf")


def _rule_scope_label(rule) -> str:
	if rule.scope_type == "Company":
		return f"Company {rule.company}"
	if rule.scope_type == "Department":
		return f"Department {rule.department}"
	if rule.scope_type == "Branch":
		return f"Branch {rule.branch}"
	if rule.scope_type == "Designation":
		return f"Designation {rule.designation}"
	if rule.scope_type == "Employee Group":
		return f"Employee Group {rule.employee_group}"
	return rule.scope_type or "Unknown scope"
