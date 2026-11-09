# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Where a timesheet is in its approval, what happens next, and what the viewer should do (Now / Next / Do).

Only where the company's policy asks for approval; otherwise Timesheet is stock
and draws no banner. Worked out on the server for the person viewing, drawn by
`public/js/where_it_is.js`.
"""

import frappe
from frappe import _
from frappe.utils import escape_html, format_datetime

from seal_hrms.seal_hrms.handover import user_for_employee
from seal_hrms.seal_hrms.timesheets import approval
from seal_hrms.seal_hrms.toil import access

INFO, SUCCESS, WARNING = "info", "success", "warning"


def _b(text) -> str:
	return f"<b>{escape_html(str(text))}</b>"


def where_it_is(doc, user: str | None = None) -> dict:
	user = user or frappe.session.user
	mine = user_for_employee(doc.employee) == user
	approver = (
		_b(frappe.utils.get_fullname(doc.custom_approver))
		if doc.get("custom_approver")
		else _("the approver")
	)
	person = _b(doc.employee_name or doc.employee)
	state = doc.get("custom_approval_state") or approval.NOT_SENT

	def rows(now, after, do, kind=INFO):
		return {
			"type": kind,
			"items": [
				{"label": _("Now"), "text": now},
				{"label": _("Next"), "text": after},
				{"label": _("Do"), "text": do},
			],
		}

	if doc.docstatus == 2:
		return rows(_("Cancelled."), _("Nothing more happens to this timesheet."), _("Nothing."))
	if doc.docstatus == 1 or state == approval.APPROVED:
		by = frappe.utils.get_fullname(doc.custom_approved_by) if doc.get("custom_approved_by") else None
		return rows(
			_("Approved by {0}.").format(_b(by)) if by else _("Approved."),
			_("Its hours count towards projects, costing and pay."),
			_("Nothing."),
			SUCCESS,
		)
	if state in (approval.NOT_SENT, approval.RETURNED):
		now = (
			_("Returned by {0}: {1}").format(
				_b(frappe.utils.get_fullname(doc.custom_approved_by))
				if doc.get("custom_approved_by")
				else approver,
				escape_html(doc.get("custom_return_reason") or ""),
			)
			if state == approval.RETURNED
			else _("Not sent yet.")
		)
		after = _("{0} approves it or returns it with a reason.").format(approver)
		if access.can_send(doc, user):
			do = _("Record the week's time, then click {0}.").format(_b(_("Send for Approval")))
			if not mine:
				do = _("Check it with {0}, then click {1} to send it for them.").format(
					person, _b(_("Send for Approval"))
				)
		else:
			do = _("Nothing for you: {0} sends it.").format(person)
		return rows(now, after, do, WARNING if state == approval.RETURNED else INFO)
	# Waiting for approval
	since = (
		escape_html(format_datetime(doc.custom_sent_on)) if doc.get("custom_sent_on") else _("it was sent")
	)
	now = _("Waiting for {0} to approve, since {1}.").format(approver, since)
	after = _("Once approved it is submitted, and its hours count.")
	if approval.can_decide(doc, user):
		do = _("Check the time, then click {0}, or {1} with a reason.").format(
			_b(_("Approve")), _b(_("Return"))
		)
	elif mine:
		do = _("Nothing for now. If {0} returns it, you can correct it and send it again.").format(approver)
	else:
		do = _("Nothing for you: {0} approves it.").format(approver)
	return rows(now, after, do)
