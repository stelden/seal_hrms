# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Daily Leave Planning scheduler jobs.

Two functions registered in hooks.scheduler_events.daily:
  - send_planning_reminders: nudge non-compliant employees + manager digests
  - close_due_cycles: flip cycles past their submission_deadline to Closed

Per SEAL_DEV_RULES:
  - §3.7 — first-detection guard: each (cycle, member, threshold) gets at most
           one nudge per day; persistent breach is logged outside the guard.
  - §3.8 — business-day-aware filter: weekend offsets evaluate against today AND
           next business day so a Mon-deadline reminder lands at the right offset.
  - §2.10 — audit-field writes use update_modified=False.
  - §3.6 — capacity-based recipient resolution for "Leave Approver of doc.X"
           (the leave_approver field is the contractual recipient — not whoever
           happens to have the role).
"""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_datetime, get_link_to_form, getdate, now_datetime, today


def send_planning_reminders() -> None:
	"""Daily — process every Open cycle's reminder cadence."""
	today_d = getdate(today())
	open_cycles = frappe.get_all(
		"Leave Planning Cycle",
		filters={"status": "Open"},
		pluck="name",
	)
	for cycle_name in open_cycles:
		try:
			_process_cycle_reminders(cycle_name, today_d)
		except Exception:
			frappe.log_error(
				title=f"[seal_hrms] reminder dispatch failed for cycle {cycle_name}",
				message=frappe.get_traceback(),
			)
		finally:
			frappe.db.commit()


def close_due_cycles() -> None:
	"""Daily — close cycles whose submission_deadline is in the past."""
	today_d = getdate(today())
	cycles = frappe.get_all(
		"Leave Planning Cycle",
		filters={"status": "Open", "submission_deadline": ["<", today_d]},
		fields=["name", "submission_deadline"],
	)
	for cycle in cycles:
		try:
			frappe.db.set_value(
				"Leave Planning Cycle", cycle.name,
				{"status": "Closed", "close_date": today_d},
				update_modified=False,
			)
			frappe.logger().info(
				f"[seal_hrms] closed cycle {cycle.name} (deadline {cycle.submission_deadline} passed)"
			)
			_send_cycle_closed_email(cycle.name)
		except Exception:
			frappe.log_error(
				title=f"[seal_hrms] cycle close failed for {cycle.name}",
				message=frappe.get_traceback(),
			)
		finally:
			frappe.db.commit()


def _process_cycle_reminders(cycle_name: str, today_d) -> None:
	cycle = frappe.get_doc("Leave Planning Cycle", cycle_name)
	deadline = getdate(cycle.submission_deadline)

	emp_offsets = _parse_offsets(cycle.reminder_offsets_employee)
	mgr_offsets = _parse_offsets(cycle.reminder_offsets_manager)

	candidate_offsets = _business_day_aware_offsets(today_d, deadline)
	emp_due = candidate_offsets & emp_offsets
	mgr_due = candidate_offsets & mgr_offsets

	if emp_due:
		_dispatch_employee_reminders(cycle, today_d, max(emp_due))

	if mgr_due:
		_dispatch_manager_digests(cycle, today_d, max(mgr_due))

	frappe.db.set_value(
		"Leave Planning Cycle", cycle.name,
		"last_reminder_run_at", now_datetime(),
		update_modified=False,
	)
	frappe.logger().info(
		f"[seal_hrms] cycle {cycle.name}: ran reminders (emp_due={emp_due}, mgr_due={mgr_due})"
	)


def _parse_offsets(raw: str | None) -> set[int]:
	if not raw:
		return set()
	out: set[int] = set()
	for token in raw.split(","):
		token = token.strip()
		if not token:
			continue
		try:
			n = int(token)
			if n >= 0:
				out.add(n)
		except ValueError:
			continue
	return out


def _business_day_aware_offsets(today_d, deadline) -> set[int]:
	"""Per §3.8 — Friday runs evaluate today's offset AND Monday's offset.

	For each of today and the next business day, compute days_to_deadline.
	If either matches a configured offset, fire that batch.
	"""
	candidates = {today_d}
	next_bday = today_d + timedelta(days=1)
	while next_bday.weekday() >= 5:
		next_bday += timedelta(days=1)
	candidates.add(next_bday)

	return {
		(getdate(deadline) - getdate(d)).days for d in candidates
	}


def _dispatch_employee_reminders(cycle, today_d, days_to_deadline: int) -> None:
	"""Per §3.7 first-detection guard: one nudge per member per day."""
	members = frappe.get_all(
		"Leave Planning Cycle Member",
		filters={
			"cycle": cycle.name,
			"exempt": 0,
			"plan_status": ["in", ["Not Started", "Draft", "Returned"]],
		},
		fields=["name", "employee", "last_nudge_at", "nudges_sent"],
	)

	for member in members:
		if member.last_nudge_at and getdate(get_datetime(member.last_nudge_at)) >= today_d:
			frappe.logger().info(
				f"[seal_hrms] cycle {cycle.name}: {member.employee} already nudged today; skipping"
			)
			continue

		try:
			_send_employee_reminder_email(cycle, member, days_to_deadline)
			frappe.db.set_value(
				"Leave Planning Cycle Member", member.name,
				{
					"nudges_sent": int(member.nudges_sent or 0) + 1,
					"last_nudge_at": now_datetime(),
				},
				update_modified=False,
			)
		except Exception:
			frappe.log_error(
				title=f"[seal_hrms] employee reminder failed for {member.name}",
				message=frappe.get_traceback(),
			)


def _dispatch_manager_digests(cycle, today_d, days_to_deadline: int) -> None:
	"""Group non-compliant members by leave_approver and email a digest."""
	members = frappe.get_all(
		"Leave Planning Cycle Member",
		filters={
			"cycle": cycle.name,
			"exempt": 0,
			"plan_status": ["in", ["Not Started", "Draft", "Returned"]],
		},
		fields=["name", "employee", "leave_approver"],
	)
	by_approver: dict[str, list] = {}
	for m in members:
		if m.leave_approver:
			by_approver.setdefault(m.leave_approver, []).append(m)

	for approver, ms in by_approver.items():
		try:
			_send_manager_digest_email(cycle, approver, ms, days_to_deadline)
		except Exception:
			frappe.log_error(
				title=f"[seal_hrms] manager digest failed for {approver} on cycle {cycle.name}",
				message=frappe.get_traceback(),
			)


def _send_employee_reminder_email(cycle, member, days_to_deadline: int) -> None:
	user = frappe.db.get_value("Employee", member.employee, "user_id")
	if not user:
		return

	subject = _("Leave Plan reminder — {0} day(s) to {1}").format(
		days_to_deadline, cycle.cycle_name,
	)
	message = _(
		"<p>Hi,</p>"
		"<p>You have not yet submitted your Leave Plan for <b>{0}</b>. "
		"The submission deadline is <b>{1}</b> ({2} day(s) from today).</p>"
		"<p>Please file your plan via {3}.</p>"
	).format(
		cycle.cycle_name,
		cycle.submission_deadline,
		days_to_deadline,
		'<a href="/app/leave-plan/new?planning_cycle=' + cycle.name + '">Leave Plan</a>',
	)
	frappe.sendmail(
		recipients=[user],
		subject=subject,
		message=message,
		reference_doctype="Leave Planning Cycle",
		reference_name=cycle.name,
		now=False,
	)


def _send_manager_digest_email(cycle, approver_user: str, members: list, days_to_deadline: int) -> None:
	rows = "".join(
		f"<li>{m.employee}</li>" for m in members
	)
	subject = _("Leave planning — {0} direct report(s) not yet filed for {1}").format(
		len(members), cycle.cycle_name,
	)
	message = _(
		"<p>Hi,</p>"
		"<p>The following direct reports have not yet submitted their Leave Plan for "
		"<b>{0}</b> (deadline <b>{1}</b>, {2} day(s) away):</p>"
		"<ul>{3}</ul>"
		"<p>Please follow up.</p>"
	).format(cycle.cycle_name, cycle.submission_deadline, days_to_deadline, rows)

	frappe.sendmail(
		recipients=[approver_user],
		subject=subject,
		message=message,
		reference_doctype="Leave Planning Cycle",
		reference_name=cycle.name,
		now=False,
	)


def _send_cycle_closed_email(cycle_name: str) -> None:
	cycle = frappe.db.get_value(
		"Leave Planning Cycle", cycle_name,
		["cycle_name", "company"], as_dict=True,
	)
	hr_recipients = frappe.get_all(
		"Has Role",
		filters={"role": "HR Manager", "parenttype": "User"},
		pluck="parent",
	)
	if not hr_recipients:
		return

	link = get_link_to_form("Leave Planning Cycle", cycle_name)
	subject = _("Leave Planning Cycle closed: {0}").format(cycle.cycle_name)
	message = _(
		"<p>The Leave Planning Cycle {0} for {1} has closed. "
		"No further plans can be submitted to it.</p>"
	).format(link, cycle.company)

	frappe.sendmail(
		recipients=hr_recipients,
		subject=subject,
		message=message,
		reference_doctype="Leave Planning Cycle",
		reference_name=cycle_name,
		now=False,
	)
