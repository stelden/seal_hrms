# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Emails as a time off claim moves: to the approver when it is sent, to the person when it is decided.

Each email is an Email Template named "Time Off in Lieu - ...", so HR can reword
it in Desk. The templates are created once, after migrate, and never
overwritten: a fixture would be re-imported on every migrate and undo HR's
wording (SEAL_DEV_RULES §1.18). Rendering and sending never fail the move: a
missing or broken template falls back to the wording below, and a send that
fails is logged (the same contract as the handover emails, whose `render` this
reuses). My Desk shows the same things for people who work from there.
"""

import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, get_url_to_form

from seal_hrms.seal_hrms.handover import user_for_employee
from seal_hrms.seal_hrms.handover_notifications import render

PREFIX = "Time Off in Lieu - "
ASK_AUTHORISATION = PREFIX + "Asked to Authorise"
ASK_APPROVAL = PREFIX + "Asked to Approve"
AUTHORISED = PREFIX + "Authorised"
APPROVED = PREFIX + "Approved"
REJECTED = PREFIX + "Rejected"
RETURNED = PREFIX + "Returned"

#: name -> (subject, body). Every template gets the variables in `_context`.
TEMPLATES = {
	ASK_AUTHORISATION: (
		"{{ employee_name }} asks to work extra hours for time off",
		"<p>{{ employee_name }} plans to work {{ hours }} extra hours on {{ dates }} and asks you to agree it "
		'before the work.</p><p><a href="{{ link }}">Open the claim</a> to authorise, return or reject it.</p>',
	),
	ASK_APPROVAL: (
		"{{ employee_name }} claims time off for extra hours",
		"<p>{{ employee_name }} worked {{ hours }} extra hours on {{ dates }}, which would add {{ days }} days of "
		'time off.</p><p><a href="{{ link }}">Open the claim</a> to approve, return or reject it.</p>',
	),
	AUTHORISED: (
		"Your extra hours are agreed",
		"<p>{{ approver_name }} agreed the extra work on {{ dates }}. Once you have done it, open "
		'<a href="{{ link }}">your claim</a>, enter the hours you actually worked and send it for approval.</p>',
	),
	APPROVED: (
		"{{ days }} days of time off added",
		"<p>{{ approver_name }} approved your claim. {{ days }} days of time off were added, usable until "
		'{{ lapses_on }}. Take them with an ordinary leave application.</p><p><a href="{{ link }}">Open the '
		"claim</a></p>",
	),
	REJECTED: (
		"Your time off claim was not approved",
		"<p>{{ approver_name }} did not approve your claim for {{ dates }}: {{ reason }}</p>"
		'<p><a href="{{ link }}">Open the claim</a></p>',
	),
	RETURNED: (
		"Your time off claim needs a change",
		"<p>{{ approver_name }} returned your claim for {{ dates }}: {{ reason }}</p><p>Open "
		'<a href="{{ link }}">your claim</a>, correct it and send it again.</p>',
	),
}

_FOR_DECISION = {"authorised": AUTHORISED, "approved": APPROVED, "rejected": REJECTED, "returned": RETURNED}


def ensure_templates() -> None:
	"""after_migrate: create any template that is missing. An existing one is HR's, and left alone."""
	try:
		for name, (subject, body) in TEMPLATES.items():
			if frappe.db.exists("Email Template", name):
				continue
			doc = frappe.new_doc("Email Template")
			doc.name = name
			doc.subject = subject
			doc.response = body
			doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			title="Time off in lieu: email templates not created", message=frappe.get_traceback()
		)


def _context(doc, reason: str | None = None) -> dict:
	lines = doc.get("lines") or []
	hours = sum((line.hours or line.planned_hours or 0) for line in lines)
	return {
		"employee_name": escape_html(doc.employee_name or ""),
		"approver_name": escape_html(
			frappe.utils.get_fullname(doc.approved_by or doc.authorised_by or doc.approver) or ""
		),
		"dates": ", ".join(formatdate(line.work_date) for line in lines),
		"hours": f"{hours:g}",
		"days": f"{(doc.days_credited or doc.days or 0):g}",
		"lapses_on": formatdate(doc.lapses_on) if doc.get("lapses_on") else "",
		"reason": escape_html(reason or doc.decision_note or ""),
		"link": get_url_to_form(doc.doctype, doc.name),
		"claim": doc.name,
	}


def _send(recipient: str | None, template: str, doc) -> None:
	if not recipient:
		return
	subject, body = TEMPLATES[template]
	context = _context(doc)
	fallback_subject = frappe.render_template(subject, context)
	fallback_body = frappe.render_template(body, context)
	subject, message = render(template, context, fallback_subject, fallback_body)
	try:
		frappe.sendmail(
			recipients=[recipient],
			subject=subject,
			message=message,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)
	except Exception:
		frappe.log_error(
			title="Time off in lieu: email not sent",
			message=frappe.get_traceback(),
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)


def sent(doc) -> None:
	"""To the approver: a claim is waiting for them."""
	template = ASK_AUTHORISATION if doc.status == "Waiting for Authorisation" else ASK_APPROVAL
	_send(doc.approver, template, doc)


def decided(doc, kind: str) -> None:
	"""To the person: their claim was authorised, approved, rejected or returned."""
	_send(user_for_employee(doc.employee), _FOR_DECISION[kind], doc)
