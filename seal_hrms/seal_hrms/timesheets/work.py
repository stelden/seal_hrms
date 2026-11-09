# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What timesheet approval is waiting on each person for, as plain records (shape of `handover_work`).

  * approval: timesheets waiting for this person to approve, including for an
    approver they stand in for;
  * task: their own timesheets returned to them.

My Desk turns these into rows (`desk/providers.py`); nothing here knows the desk.
"""

import frappe
from frappe import _
from frappe.utils import flt, formatdate

from seal_hrms.seal_hrms import acting
from seal_hrms.seal_hrms.timesheets import approval
from seal_hrms.seal_hrms.toil import access


def _record(kind, name, title, subtitle="", due=None):
	return frappe._dict(
		kind=kind,
		doctype="Timesheet",
		name=name,
		title=title,
		subtitle=subtitle,
		due=due,
		route=f"/app/timesheet/{name}",
	)


def work_for(user: str) -> list[frappe._dict]:
	if not frappe.get_meta("Timesheet").has_field("custom_approval_state"):
		return []
	kinds = acting.kinds_answering(approval.AUTHORITY)
	approvers = [
		user,
		*[r.principal for r in acting.acting_for(user) if r.authority in kinds and r.principal],
	]
	me = access.employee_for_user(user)
	out = []
	for ts in frappe.get_all(
		"Timesheet",
		filters=[
			["custom_approver", "in", approvers],
			["docstatus", "=", 0],
			["custom_approval_state", "=", approval.WAITING],
		],
		fields=[
			"name",
			"employee",
			"employee_name",
			"start_date",
			"end_date",
			"total_hours",
			"custom_sent_on",
		],
		order_by="custom_sent_on asc",
	):
		if me and ts.employee == me:
			continue
		out.append(
			_record(
				"approval",
				ts.name,
				_("Timesheet from {0}").format(ts.employee_name),
				_("{0} hours, {1} to {2}").format(
					f"{flt(ts.total_hours):g}", formatdate(ts.start_date), formatdate(ts.end_date)
				),
				formatdate(ts.custom_sent_on) if ts.custom_sent_on else None,
			)
		)
	if me:
		for ts in frappe.get_all(
			"Timesheet",
			filters=[
				["employee", "=", me],
				["docstatus", "=", 0],
				["custom_approval_state", "=", approval.RETURNED],
			],
			fields=["name", "start_date", "custom_return_reason"],
		):
			out.append(
				_record(
					"task",
					ts.name,
					_("Your timesheet from {0} was returned").format(formatdate(ts.start_date)),
					ts.custom_return_reason or "",
				)
			)
	return out
