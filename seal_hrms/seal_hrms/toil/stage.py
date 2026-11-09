# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Where a time off claim is, what happens next, and what the person looking at it should do.

Every process form answers Now / Next / Do in that order (house rule), and the
Do row names a button on the form in the words on it. Worked out here, on the
server, for the person viewing, so the form only draws it and tests can read it.
"""

import frappe
from frappe import _
from frappe.utils import escape_html, flt, format_datetime, formatdate

from seal_hrms.seal_hrms.handover import user_for_employee
from seal_hrms.seal_hrms.toil import access, approval
from seal_hrms.seal_hrms.toil.evidence import APPROVER_ONLY

INFO, SUCCESS, WARNING, ERROR = "info", "success", "warning", "error"


def _b(text) -> str:
	return f"<b>{escape_html(str(text))}</b>"


def days(value) -> str:
	"""1 day, 1.5 days: a day count as a person writes it."""
	number = round(flt(value), 2)
	text = f"{number:g}"
	return _("{0} day").format(text) if number == 1 else _("{0} days").format(text)


def _who(user: str | None, fallback: str) -> str:
	return _b(frappe.utils.get_fullname(user)) if user else fallback


def where_it_is(doc, user: str | None = None) -> dict:
	"""{"type": colour, "items": [{"label": "Now"|"Next"|"Do", "text": html}]} for this viewer."""
	user = user or frappe.session.user
	mine = user_for_employee(doc.employee) == user
	approver = _who(doc.approver, _("their leave approver"))
	person = _b(doc.employee_name or doc.employee)
	status = doc.status or approval.DRAFT
	unsupported = [line for line in doc.get("lines") or [] if line.supported_by == APPROVER_ONLY]

	def rows(now, after, do, kind=INFO):
		return {
			"type": kind,
			"items": [
				{"label": _("Now"), "text": now},
				{"label": _("Next"), "text": after},
				{"label": _("Do"), "text": do},
			],
		}

	if status in (approval.DRAFT, approval.RETURNED):
		now = (
			_("Returned by {0}: {1}").format(
				_who(doc.approved_by, approver), escape_html(doc.decision_note or "")
			)
			if status == approval.RETURNED
			else _("Draft: not yet sent.")
		)
		after = _("{0} approves, returns or rejects it once it is sent.").format(approver)
		if access.can_send(doc, user):
			do = _("List each day you worked extra, then click {0}.").format(_b(_("Send for Approval")))
			if not mine:
				do = _("Check the days with {0}, then click {1} to send it for them.").format(
					person, _b(_("Send for Approval"))
				)
		else:
			do = _("Nothing for you: {0} sends it.").format(person)
		return rows(now, after, do, WARNING if status == approval.RETURNED else INFO)

	if status == approval.WAITING:
		now = _("Waiting for {0} to decide, since {1}.").format(
			approver, escape_html(format_datetime(doc.sent_on)) if doc.sent_on else _("it was sent")
		)
		after = _("Approved time is added to {0}'s time off, to take as ordinary leave.").format(person)
		if access.can_decide(doc, user):
			do = _("Check the days, then click {0}; or {1} or {2} with a reason.").format(
				_b(_("Approve")), _b(_("Other → Return")), _b(_("Other → Reject"))
			)
			if unsupported:
				do += " " + _(
					"{0} of these days have no record behind them: approving confirms them on your word."
				).format(len(unsupported))
		elif mine:
			do = _("Nothing for now. If {0} returns it, you can correct it and send it again.").format(
				approver
			)
		else:
			do = _("Nothing for you: {0} decides it.").format(approver)
		return rows(now, after, do, WARNING if unsupported and access.can_decide(doc, user) else INFO)

	if status == approval.APPROVED:
		now = _("Approved: {0} added. {1} left, usable until {2}.").format(
			days(doc.days_credited),
			days(doc.days_left),
			formatdate(doc.lapses_on) if doc.lapses_on else _("the end of the leave year"),
		)
		after = (
			_("Unused time lapses after {0}.").format(formatdate(doc.lapses_on))
			if doc.lapses_on
			else _("Nothing more is needed here.")
		)
		if mine and flt(doc.days_left):
			do = _("Click {0} to take it, in full or half days.").format(_b(_("Apply for Leave")))
		else:
			do = _("Nothing.")
		if flt(doc.days_not_credited):
			now += " " + _("{0} over the limit, not added.").format(days(doc.days_not_credited))
		return rows(now, after, do, SUCCESS)

	if status == approval.REJECTED:
		return rows(
			_("Rejected by {0}: {1}").format(
				_who(doc.approved_by, approver), escape_html(doc.decision_note or "")
			),
			_("Nothing more happens to this claim."),
			_("Nothing. If the reason no longer applies, make a new claim."),
			ERROR,
		)

	return rows(
		_("Cancelled: its time was taken back."), _("Nothing more happens to this claim."), _("Nothing.")
	)
