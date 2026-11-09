# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What time off in lieu is waiting on each person for.

Plain records, answered on any site, in the shape of `handover_work`: kind,
doctype, name, title, subtitle, due, route. My Desk turns them into rows
(`seal_hrms/desk/providers.py`); nothing here knows the desk exists.

  * approval: claims waiting for this person to authorise or approve, including
    for an approver they stand in for during that approver's leave;
  * task: their own claims returned to them, or authorised and waiting for the
    hours they worked;
  * draft: their own claims not yet sent;
  * notification: their time off that lapses within LAPSE_WARNING_DAYS.
"""

import frappe
from frappe import _
from frappe.utils import add_days, flt, formatdate, getdate, today

from seal_hrms.seal_hrms.toil import access, approval
from seal_hrms.seal_hrms.toil.stage import days

CLAIM = "Time Off in Lieu Claim"
LAPSE_WARNING_DAYS = 14


def _record(kind, name, title, subtitle="", due=None):
	return frappe._dict(
		kind=kind,
		doctype=CLAIM,
		name=name,
		title=title,
		subtitle=subtitle,
		due=due,
		route=f"/app/time-off-in-lieu-claim/{name}",
	)


def work_for(user: str, on_date=None) -> list[frappe._dict]:
	"""Everything time off in lieu needs from `user` today."""
	if not frappe.db.table_exists(CLAIM):
		return []
	on_date = getdate(on_date or today())
	return [*_to_decide(user), *_mine(user, on_date)]


def _to_decide(user: str) -> list:
	approvers = [user, *access._principals_for(user)]
	me = access.employee_for_user(user)
	out = []
	for claim in frappe.get_all(
		CLAIM,
		filters=[
			["approver", "in", approvers],
			["docstatus", "=", 0],
			["status", "in", [approval.WAITING, approval.WAITING_AUTH]],
		],
		fields=["name", "employee", "employee_name", "status", "days", "sent_on"],
		order_by="sent_on asc",
	):
		if me and claim.employee == me:
			continue  # nobody decides their own
		what = (
			_("extra work to authorise")
			if claim.status == approval.WAITING_AUTH
			else _("{0} to approve").format(days(claim.days))
		)
		out.append(
			_record(
				"approval",
				claim.name,
				_("Time off claim from {0}").format(claim.employee_name),
				what,
				formatdate(claim.sent_on) if claim.sent_on else None,
			)
		)
	return out


def _mine(user: str, on_date) -> list:
	me = access.employee_for_user(user)
	if not me:
		return []
	out = []
	for claim in frappe.get_all(
		CLAIM,
		filters=[
			["employee", "=", me],
			["docstatus", "=", 0],
			["status", "in", [approval.DRAFT, approval.RETURNED, approval.AUTHORISED]],
		],
		fields=["name", "status", "decision_note"],
	):
		if claim.status == approval.RETURNED or (claim.status == approval.AUTHORISED and claim.decision_note):
			out.append(
				_record("task", claim.name, _("Your time off claim was returned"), claim.decision_note or "")
			)
		elif claim.status == approval.AUTHORISED:
			out.append(
				_record("task", claim.name, _("Confirm the hours you worked"), _("Extra work was authorised"))
			)
		else:
			out.append(_record("draft", claim.name, _("Time off claim not sent")))
	horizon = add_days(on_date, LAPSE_WARNING_DAYS)
	for claim in frappe.get_all(
		CLAIM,
		filters=[
			["employee", "=", me],
			["docstatus", "=", 1],
			["status", "=", approval.APPROVED],
			["days_left", ">", 0],
			["lapses_on", "is", "set"],
			["lapses_on", ">=", on_date],
			["lapses_on", "<=", horizon],
		],
		fields=["name", "days_left", "lapses_on"],
	):
		out.append(
			_record(
				"notification",
				claim.name,
				_("{0} of time off lapses on {1}").format(
					days(flt(claim.days_left)), formatdate(claim.lapses_on)
				),
				_("Apply for leave to use it"),
				formatdate(claim.lapses_on),
			)
		)
	return out
