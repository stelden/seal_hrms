# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Claim time off in lieu from a timesheet: the extra hours it records become a new claim.

On a submitted timesheet (approved, where approval is on) of someone whose
company banks extra hours and whose grade does, the extra hours it records are
the candidates: every hour on a rest day or public holiday, and hours beyond the
working day on a working day. Days already claimed, paid as overtime or on
approved leave, and days under the company's minimum, are left out.

`make_toil_claim` returns a new, unsaved claim with a line per day, each linked
to the timesheet, so nothing is written until the person saves it, and an
approved claim then stops the timesheet being cancelled from under it (Frappe's
own back-link check). In a company that authorises extra work first, the hours
are also the planned hours, so the claim is authorised after the fact.
"""

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate

from seal_hrms.seal_hrms.toil import access, rules
from seal_hrms.seal_hrms.toil.evidence import extra
from seal_hrms.seal_hrms.working_time.calendar import day_kinds
from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST, policy_for

CLAIM = "Time Off in Lieu Claim"


def _eligible(doc) -> bool:
	policy = policy_for(doc.company)
	if not policy.toil_enabled or not policy.leave_type:
		return False
	return frappe.db.get_value("Employee", doc.employee, "grade") in policy.eligible_grades


def candidates(doc) -> list[dict]:
	"""[{work_date, hours, work_done}] the timesheet's extra hours, leaving out what cannot be claimed."""
	if doc.docstatus != 1 or not doc.get("employee") or not _eligible(doc):
		return []
	policy = policy_for(doc.company)
	per_day: dict = {}
	notes: dict = {}
	for line in doc.time_logs:
		if not line.from_time:
			continue
		day = getdate(line.from_time)
		per_day[day] = per_day.get(day, 0) + flt(line.hours)
		if line.description:
			notes.setdefault(day, []).append(line.description.strip())
	if not per_day:
		return []
	dates = sorted(per_day)
	kinds = day_kinds(doc.employee, dates)
	taken = (
		set(rules.claimed_dates(doc.employee, dates))
		| set(rules.paid_dates(doc.employee, dates))
		| set(rules.leave_dates(doc.employee, dates))
	)
	out = []
	for day in dates:
		if day in taken:
			continue
		hours = extra(kinds[day], per_day[day], flt(policy.hours_per_day))
		if not hours or hours < flt(policy.minimum_hours):
			continue
		work_done = "; ".join(dict.fromkeys(notes.get(day, []))) or _("Recorded on timesheet {0}").format(
			doc.name
		)
		out.append({"work_date": str(day), "hours": hours, "work_done": work_done[:500]})
	return out


def onload(doc, method=None) -> None:
	"""Timesheet onload: how many days of extra hours the viewer could claim from it."""
	if doc.is_new() or doc.docstatus != 1 or not doc.get("employee"):
		return
	if not frappe.db.table_exists(CLAIM) or not access.can_send(doc, frappe.session.user):
		return
	try:
		doc.set_onload("toil_candidates", len(candidates(doc)))
	except frappe.ValidationError:
		frappe.clear_last_message()  # no holiday list: nothing to offer, and nothing to shout about on load


@frappe.whitelist()
def make_toil_claim(source_name: str, target_doc=None) -> dict:
	"""A new, unsaved claim from a timesheet's extra hours. Writes nothing."""
	doc = frappe.get_doc("Timesheet", source_name)
	doc.check_permission("read")
	access.require_self_or_hr(doc.employee)
	if doc.docstatus != 1:
		frappe.throw(_("Claim from a timesheet once it is approved (submitted)."))
	if not _eligible(doc):
		frappe.throw(
			_("{0} does not bank extra hours as time off.").format(doc.employee_name or doc.employee),
			title=_("Not a Grade That Banks Hours"),
		)
	found = candidates(doc)
	if not found:
		frappe.throw(
			_("Timesheet {0} records no extra hours that can still be claimed.").format(doc.name),
			title=_("Nothing to Claim"),
		)
	first = policy_for(doc.company).prior_authorisation == AUTHORISE_FIRST
	claim = frappe.new_doc(CLAIM)
	claim.employee = doc.employee
	claim.employee_name = doc.employee_name
	claim.company = doc.company
	claim.mode = policy_for(doc.company).prior_authorisation
	claim.note = _("From timesheet {0}, {1} to {2}.").format(
		doc.name, formatdate(doc.start_date), formatdate(doc.end_date)
	)
	for row in found:
		claim.append(
			"lines",
			{
				"work_date": row["work_date"],
				"hours": row["hours"],
				"planned_hours": row["hours"] if first else None,
				"work_done": row["work_done"],
				"timesheet": doc.name,
			},
		)
	return claim.as_dict()
