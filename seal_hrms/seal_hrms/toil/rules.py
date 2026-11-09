# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What a time off claim must satisfy, and how its days are worked out.

Called from the claim's `validate`: it reads other records and throws, and sets
only the claim's own computed fields (SEAL_DEV_RULES §3.1).

Rules (WORKING_TIME_DESIGN.md §5.2, §5.6, §5.7):
  * the person's company banks extra hours, and their grade is one that does;
  * they are not paid by the hour (their timesheets are their pay already);
  * each date once, not in the future, at least the minimum hours;
  * not a day of approved leave, not claimed on another claim, and not paid as
    overtime: an hour is paid or banked, never both.
"""

import frappe
from frappe import _
from frappe.utils import add_days, formatdate, get_link_to_form, getdate, today

from seal_hrms.seal_hrms.toil import days as counting
from seal_hrms.seal_hrms.working_time.calendar import day_kinds
from seal_hrms.seal_hrms.working_time.policy import policy_for

CLAIM = "Time Off in Lieu Claim"
LINE = "Time Off in Lieu Claim Line"
# Statuses in which a claim's dates are taken. A draft holds them too, so the
# same person does not draft one date twice; paid overtime only yields to a
# claim that has been sent (`banked_dates`).
LIVE = ("Draft", "Returned", "Waiting for Approval", "Approved")
SENT = ("Waiting for Approval", "Approved")


def check(doc) -> None:
	"""Throw if the claim breaks a rule; otherwise work out each line and the totals."""
	policy = policy_for(doc.company)
	_check_policy(doc, policy)
	_check_person(doc, policy)
	dates = _check_lines(doc, policy)
	kinds = day_kinds(doc.employee, dates)
	_count(doc, policy, kinds)
	_check_conflicts(doc, dates)
	from seal_hrms.seal_hrms.toil import evidence

	evidence.annotate(doc, policy, kinds)


def _check_policy(doc, policy) -> None:
	if not policy.toil_enabled or not policy.leave_type:
		frappe.throw(
			_(
				"{0} does not bank extra hours as time off. HR can switch it on in its Working Time Policy."
			).format(doc.company or _("This company")),
			title=_("Time Off in Lieu Is Off"),
		)
	if not policy.hours_per_day or policy.hours_per_day <= 0:
		frappe.throw(
			_("{0}'s Working Time Policy needs the hours in a normal working day.").format(doc.company)
		)


def _check_person(doc, policy) -> None:
	grade = frappe.db.get_value("Employee", doc.employee, "grade")
	if grade not in policy.eligible_grades:
		frappe.throw(
			_("{0}'s grade ({1}) is paid for extra hours, not given time off for them.").format(
				doc.employee_name or doc.employee, grade or _("none set")
			),
			title=_("Not a Grade That Banks Hours"),
		)
	if _paid_by_the_hour(doc.employee):
		frappe.throw(
			_("{0} is paid by the hour from their timesheets, so extra hours are already paid.").format(
				doc.employee_name or doc.employee
			),
			title=_("Paid by the Hour"),
		)


def _paid_by_the_hour(employee: str) -> bool:
	structure = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1, "from_date": ["<=", today()]},
		fields=["salary_structure"],
		order_by="from_date desc",
		limit=1,
	)
	if not structure:
		return False
	return bool(
		frappe.db.get_value(
			"Salary Structure", structure[0].salary_structure, "salary_slip_based_on_timesheet"
		)
	)


def _check_lines(doc, policy) -> list:
	if not doc.get("lines"):
		frappe.throw(_("Add the days you worked extra."))
	seen, dates = set(), []
	counting_rules = counting.Counting.from_policy(policy)
	for line in doc.lines:
		day = getdate(line.work_date)
		if day in seen:
			frappe.throw(_("Row {0}: {1} is on this claim twice.").format(line.idx, formatdate(day)))
		seen.add(day)
		if day > getdate(today()):
			frappe.throw(_("Row {0}: {1} has not happened yet.").format(line.idx, formatdate(day)))
		if not line.hours or line.hours <= 0:
			frappe.throw(_("Row {0}: enter the extra hours worked.").format(line.idx))
		if counting.below_minimum(line.hours, counting_rules):
			frappe.throw(
				_("Row {0}: extra time under {1} hours on a day does not count.").format(
					line.idx, frappe.format_value(policy.minimum_hours, {"fieldtype": "Float"})
				)
			)
		dates.append(day)
	return dates


def _count(doc, policy, kinds) -> None:
	rules = counting.Counting.from_policy(policy)
	total = credited = 0.0
	for line in doc.lines:
		line.day_kind = kinds[getdate(line.work_date)]
		line.rate, line.credited_hours = counting.count_line(line.hours, line.day_kind, rules)
		total += line.hours
		credited += line.credited_hours
	doc.total_hours = counting.round2(total)
	doc.credited_hours = counting.round2(credited)
	doc.days = counting.to_days(credited, policy.hours_per_day)


def _check_conflicts(doc, dates) -> None:
	for day, leave in leave_dates(doc.employee, dates).items():
		frappe.throw(
			_("{0} was a day of approved leave ({1}).").format(
				formatdate(day), get_link_to_form("Leave Application", leave)
			),
			title=_("On Leave That Day"),
		)
	for day, claim in claimed_dates(doc.employee, dates, exclude=doc.name).items():
		frappe.throw(
			_("{0} is already claimed on {1}.").format(formatdate(day), get_link_to_form(CLAIM, claim)),
			title=_("Already Claimed"),
		)
	for day, slip in paid_dates(doc.employee, dates).items():
		frappe.throw(
			_("{0} was paid as overtime on {1}. A day is either paid or given as time off, not both.").format(
				formatdate(day), get_link_to_form("Overtime Slip", slip)
			),
			title=_("Paid as Overtime"),
		)


def leave_dates(employee: str, dates) -> dict:
	"""{date: leave application} for dates inside approved, submitted leave."""
	dates = [getdate(d) for d in dates]
	if not dates:
		return {}
	found = {}
	for leave in frappe.get_all(
		"Leave Application",
		filters=[
			["employee", "=", employee],
			["docstatus", "=", 1],
			["status", "=", "Approved"],
			["from_date", "<=", max(dates)],
			["to_date", ">=", min(dates)],
		],
		fields=["name", "from_date", "to_date"],
	):
		for day in dates:
			if getdate(leave.from_date) <= day <= getdate(leave.to_date):
				found.setdefault(day, leave.name)
	return found


def claimed_dates(employee: str, dates, exclude: str | None = None) -> dict:
	"""{date: claim} for dates on another live claim of this person (drafts included)."""
	dates = [getdate(d) for d in dates]
	if not dates or not frappe.db.table_exists(CLAIM):
		return {}
	rows = frappe.db.sql(
		f"""
		SELECT line.work_date, claim.name FROM `tab{LINE}` line
		INNER JOIN `tab{CLAIM}` claim ON claim.name = line.parent AND line.parenttype = %(claim)s
		WHERE claim.employee = %(employee)s AND claim.name != %(name)s AND claim.docstatus < 2
		  AND claim.status IN %(live)s AND line.work_date IN %(dates)s
		""",
		{"claim": CLAIM, "employee": employee, "name": exclude or "", "live": LIVE, "dates": dates},
		as_dict=True,
	)
	return {getdate(r.work_date): r.name for r in rows}


def paid_dates(employee: str, dates) -> dict:
	"""{date: overtime slip} for dates on a slip that has not been cancelled. Any slip, even a draft, holds its dates."""
	if not dates:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT d.date, s.name FROM `tabOvertime Details` d
		INNER JOIN `tabOvertime Slip` s ON s.name = d.parent AND d.parenttype = 'Overtime Slip'
		WHERE s.employee = %(employee)s AND s.docstatus < 2 AND d.date IN %(dates)s
		""",
		{"employee": employee, "dates": list(dates)},
		as_dict=True,
	)
	return {getdate(r.date): r.name for r in rows}


def banked_dates(employee: str, dates) -> dict:
	"""{date: claim} for dates on a claim that has been sent or approved."""
	if not dates or not frappe.db.table_exists(CLAIM):
		return {}
	rows = frappe.db.sql(
		f"""
		SELECT line.work_date, claim.name FROM `tab{LINE}` line
		INNER JOIN `tab{CLAIM}` claim ON claim.name = line.parent AND line.parenttype = %(claim)s
		WHERE claim.employee = %(employee)s AND claim.docstatus < 2 AND claim.status IN %(sent)s
		  AND line.work_date IN %(dates)s
		""",
		{"claim": CLAIM, "employee": employee, "sent": SENT, "dates": list(dates)},
		as_dict=True,
	)
	return {getdate(r.work_date): r.name for r in rows}


def check_claim_window(doc, policy) -> None:
	"""When sent: the oldest date is still within the company's claim window."""
	window = int(policy.claim_within_days or 0)
	if not window:
		return
	oldest = min(getdate(line.work_date) for line in doc.lines)
	if oldest < getdate(add_days(today(), -window)):
		frappe.throw(
			_("{0} is more than {1} days ago. Claims must be sent within {1} days of the work.").format(
				formatdate(oldest), window
			),
			title=_("Too Late to Claim"),
		)
