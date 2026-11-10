# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Balances, cover and headlines for My Desk, as plain records (HR_ON_MY_DESK.md §2.3–§2.5).

Every answer is about the person asking, counted with their own Employee record
(their own id is a filter value, read directly as `self_service_status` does).
Nothing here imports seal_desk; `seal_hrms.desk.providers` turns these into figures,
list rows and headlines.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, formatdate, getdate, today

from seal_hrms.seal_hrms.self_service_status import employee_of

#: At most this many leave types get a figure (HR_ON_MY_DESK §2.3).
LEAVE_TYPES_SHOWN = 4
#: Time off lapsing within this many days is counted on the balance figure ...
LAPSE_FIGURE_DAYS = 30
#: ... and within this many becomes a headline.
LAPSE_HEADLINE_DAYS = 14
CLAIM = "Time Off in Lieu Claim"
ASSIGNMENT = "Task Assignment"


def _days(value: float) -> str:
	return f"{flt(value, 2):g}"


# ---------------------------------------------------------------- balances


def balances(user: str, readable=None, on_date=None) -> list[frappe._dict]:
	"""Leave left per leave type (most used first), time off in lieu left, and time off lapsing soon.

	Each record: key, caption, value, target (kind, name, filters). A figure on a DocType the
	person cannot read is left out rather than shown as nought (seal_desk §5.1)."""
	employee = employee_of(user)
	if not employee:
		return []
	on_date = getdate(on_date or today())
	out = []
	if readable is None or "Leave Application" in readable:
		out += _leave_left(employee, on_date)
	if readable is None or CLAIM in readable:
		out += _toil(employee, on_date)
	return out


def _toil_policy(employee: str):
	"""The person's company's Working Time Policy, if it banks their grade's extra hours; else None."""
	from seal_hrms.seal_hrms.working_time.policy import policy_for

	company, grade = frappe.db.get_value("Employee", employee, ["company", "grade"])
	policy = policy_for(company)
	if not (policy.toil_enabled and policy.leave_type and grade in policy.eligible_grades):
		return None
	return policy


def _leave_left(employee: str, on_date) -> list[frappe._dict]:
	from hrms.hr.doctype.leave_application import leave_application as la

	from seal_hrms.seal_hrms.working_time.policy import toil_leave_types

	banked = toil_leave_types()
	rows = []
	for leave_type, alloc in (la.get_leave_allocation_records(employee, on_date) or {}).items():
		if leave_type in banked:
			continue  # time off in lieu has its own figure
		left = la.get_leave_balance_on(
			employee, leave_type, on_date, to_date=alloc.to_date, consider_all_leaves_in_the_allocation_period=True
		)
		used = -flt(la.get_leaves_for_period(employee, leave_type, alloc.from_date, alloc.to_date))
		rows.append((used, leave_type, flt(left)))
	rows.sort(key=lambda r: (-r[0], r[1]))
	return [
		frappe._dict(
			key=f"leave_left:{leave_type}",
			caption=_("{0} left").format(_(leave_type)),
			value=left,
			target=frappe._dict(kind="Report", name="Employee Leave Balance", filters={"employee": employee}),
		)
		for _used, leave_type, left in rows[:LEAVE_TYPES_SHOWN]
	]


def _toil(employee: str, on_date) -> list[frappe._dict]:
	from seal_hrms.seal_hrms.toil.ledger import held

	if not frappe.db.table_exists(CLAIM):
		return []
	policy = _toil_policy(employee)
	if not policy:
		return []
	target = frappe._dict(kind="Report", name="Time Off in Lieu", filters={"employee": employee})
	return [
		frappe._dict(key="toil_left", caption=_("Time off in lieu left"), value=flt(held(employee, policy.leave_type), 2), target=target),
		frappe._dict(
			key="toil_lapsing",
			caption=_("Time off lapsing in {0} days").format(LAPSE_FIGURE_DAYS),
			value=lapsing(employee, on_date, LAPSE_FIGURE_DAYS)[0],
			target=target,
		),
	]


def lapsing(employee: str, on_date, within: int) -> tuple[float, object]:
	"""(days of approved time off that lapse within `within` days, the first date one lapses)."""
	rows = frappe.get_all(
		CLAIM,
		filters=[
			["employee", "=", employee],
			["docstatus", "=", 1],
			["status", "=", "Approved"],
			["days_left", ">", 0],
			["lapses_on", "is", "set"],  # a blank date would match "<=" (SEAL_DEV_RULES §2.19)
			["lapses_on", ">=", on_date],
			["lapses_on", "<=", add_days(on_date, within)],
		],
		fields=["days_left", "lapses_on"],
		order_by="lapses_on asc",
	)
	return flt(sum(flt(r.days_left) for r in rows), 2), (rows[0].lapses_on if rows else None)


# ---------------------------------------------------------------- cover


def cover(user: str) -> list[frappe._dict]:
	"""Who covers the person, whom they cover, and whose approvals they give. Records: title, meta, doctype, name."""
	from seal_hrms.seal_hrms import acting
	from seal_hrms.seal_hrms.handover import Status, covered_by

	me = employee_of(user)
	if not me:
		return []
	out = []
	for ta in frappe.get_all(
		ASSIGNMENT,
		filters=[["employee", "=", me], ["docstatus", "=", 1], ["status", "in", [Status.ACCEPTED, Status.ACTIVE]]],
		fields=["name", "task_assignee_name", "leave_from", "leave_to"],
		order_by="leave_from asc",
	):
		out.append(_row(
			_("{0} is covering your work, {1} to {2}").format(ta.task_assignee_name, formatdate(ta.leave_from), formatdate(ta.leave_to)),
			"", ta.name,
		))
	for name in frappe.get_all(ASSIGNMENT, filters={"docstatus": 1, "status": Status.ACTIVE}, pluck="name"):
		doc = frappe.get_doc(ASSIGNMENT, name)
		if doc.employee == me:
			continue
		tasks = [r for r in doc.assignment_todos if covered_by(doc, r) == me]
		if tasks or doc.task_assignee == me:
			out.append(_row(
				_("You are covering {0} until {1}").format(doc.employee_name, formatdate(doc.return_date or doc.leave_to)),
				_("{0} task(s)").format(len(tasks)), name,
			))
	kinds = acting.registry()
	for row in acting.acting_for(user):
		until = frappe.db.get_value(ASSIGNMENT, row.assignment, ["return_date", "leave_to"], as_dict=True) or {}
		spec = kinds.get(row.authority)
		out.append(_row(
			_("You approve for {0} until {1}").format(frappe.utils.get_fullname(row.principal), formatdate(until.get("return_date") or until.get("leave_to"))),
			_(spec.label) if spec else "", row.assignment,
		))
	return out


def _row(title: str, meta: str, name: str) -> frappe._dict:
	return frappe._dict(title=title, meta=meta, doctype=ASSIGNMENT, name=name, route=f"/app/task-assignment/{name}")


# ---------------------------------------------------------------- headlines


def headlines(user: str, on_date=None) -> list[frappe._dict]:
	"""At most three lines, in this order, each only when true: approving in someone's place; time off
	lapsing within two weeks; last week's timesheet not sent. Records: text, emphasize, doctype, name/route."""
	on_date = getdate(on_date or today())
	out = []
	acting_line = _acting_headline(user)
	if acting_line:
		out.append(acting_line)
	employee = employee_of(user)
	if employee:
		for line in (_lapse_headline(employee, on_date), _timesheet_headline(employee, on_date)):
			if line:
				out.append(line)
	return out[:3]


def _acting_headline(user: str):
	from seal_hrms.seal_hrms import acting

	rows = acting.acting_for(user)
	if not rows:
		return None
	principals = list(dict.fromkeys(r.principal for r in rows if r.principal))
	if not principals:
		return None
	names = [frappe.utils.get_fullname(p) for p in principals]
	until = frappe.db.get_value(ASSIGNMENT, rows[0].assignment, ["return_date", "leave_to"], as_dict=True) or {}
	day = until.get("return_date") or until.get("leave_to")
	who = names[0] if len(names) == 1 else _("{0} and {1} others").format(names[0], len(names) - 1)
	text = (
		_("You're approving for {0} until {1}").format(who, formatdate(day))
		if day and len(names) == 1
		else _("You're approving for {0}").format(who)
	)
	return frappe._dict(text=text, emphasize=[names[0]], route=f"/app/task-assignment/{rows[0].assignment}")


def _lapse_headline(employee: str, on_date):
	if not frappe.db.table_exists(CLAIM):
		return None
	total, first = lapsing(employee, on_date, LAPSE_HEADLINE_DAYS)
	if not total:
		return None
	text = _("{0} days of time off in lieu lapse on {1}").format(_days(total), formatdate(first)) if total != 1 else _(
		"1 day of time off in lieu lapses on {0}"
	).format(formatdate(first))
	return frappe._dict(text=text, emphasize=[formatdate(first)], route="/app/query-report/Time%20Off%20in%20Lieu")


def _timesheet_headline(employee: str, on_date):
	"""Last week's timesheet not yet sent, where the company asks for weekly timesheets and approval (P4-9)."""
	from seal_hrms.seal_hrms.timesheets import approval
	from seal_hrms.seal_hrms.timesheets.week import monday_of
	from seal_hrms.seal_hrms.working_time.policy import policy_for

	company = frappe.db.get_value("Employee", employee, "company")
	policy = policy_for(company)
	if not (policy.weekly_timesheets and policy.timesheet_approval) or approval.site_workflow():
		return None
	if not frappe.get_meta("Timesheet").has_field("custom_approval_state"):
		return None
	start = add_days(monday_of(on_date), -7)
	end = add_days(start, 6)
	sent = frappe.get_all(
		"Timesheet",
		filters=[
			["employee", "=", employee],
			["docstatus", "<", 2],
			["start_date", "<=", end],
			["end_date", ">=", start],
		],
		or_filters=[["docstatus", "=", 1], ["custom_approval_state", "=", approval.WAITING]],
		pluck="name",
		limit=1,
	)
	if sent:
		return None
	week = _("{0} to {1}").format(formatdate(start), formatdate(end))
	return frappe._dict(text=_("Your timesheet for {0} isn't sent yet").format(week), emphasize=[week], route="/app/timesheet")
