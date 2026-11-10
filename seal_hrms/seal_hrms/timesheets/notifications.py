# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Emails as a timesheet moves through approval: to the approver when sent, to the person when decided.

Email Templates named "Timesheet - ...", created once after migrate and never
overwritten, so HR's wording stays (SEAL_DEV_RULES §1.18). Rendering and sending
never fail the move (the contract of the handover emails, whose `render` this
reuses).
"""

import frappe
from frappe.utils import escape_html, formatdate, get_url_to_form

from seal_hrms.seal_hrms.handover import user_for_employee
from seal_hrms.seal_hrms.handover_notifications import render

PREFIX = "Timesheet - "
ASK_APPROVAL = PREFIX + "Asked to Approve"
APPROVED = PREFIX + "Approved"
RETURNED = PREFIX + "Returned"

TEMPLATES = {
	ASK_APPROVAL: (
		"{{ employee_name }} sent a timesheet for approval",
		"<p>{{ employee_name }} recorded {{ hours }} hours from {{ start_date }} to {{ end_date }}.</p>"
		'<p><a href="{{ link }}">Open the timesheet</a> to approve it or return it with a reason.</p>',
	),
	APPROVED: (
		"Your timesheet was approved",
		"<p>{{ approver_name }} approved your timesheet for {{ start_date }} to {{ end_date }}.</p>"
		'<p><a href="{{ link }}">Open the timesheet</a></p>',
	),
	RETURNED: (
		"Your timesheet needs a change",
		"<p>{{ approver_name }} returned your timesheet for {{ start_date }} to {{ end_date }}: {{ reason }}</p>"
		'<p>Open <a href="{{ link }}">your timesheet</a>, correct it and send it again.</p>',
	),
}

_FOR_DECISION = {"approved": APPROVED, "returned": RETURNED}


def ensure_templates() -> None:
	"""after_migrate: create any template that is missing; an existing one is HR's."""
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
			title="Timesheet approval: email templates not created", message=frappe.get_traceback()
		)


def _context(doc) -> dict:
	return {
		"employee_name": escape_html(doc.employee_name or ""),
		"approver_name": escape_html(
			frappe.utils.get_fullname(doc.get("custom_approved_by") or doc.get("custom_approver")) or ""
		),
		"hours": f"{(doc.total_hours or 0):g}",
		"start_date": formatdate(doc.start_date) if doc.start_date else "",
		"end_date": formatdate(doc.end_date) if doc.end_date else "",
		"reason": escape_html(doc.get("custom_return_reason") or ""),
		"link": get_url_to_form(doc.doctype, doc.name),
		"timesheet": doc.name,
	}


def _send(recipient: str | None, template: str, doc) -> None:
	if not recipient:
		return
	context = _context(doc)
	subject, body = TEMPLATES[template]
	subject, message = render(
		template, context, frappe.render_template(subject, context), frappe.render_template(body, context)
	)
	from seal_hrms.seal_hrms import notify

	notify.log(recipient, subject, doc.doctype, doc.name)
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
			title="Timesheet approval: email not sent",
			message=frappe.get_traceback(),
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)


def sent(doc) -> None:
	_send(doc.get("custom_approver"), ASK_APPROVAL, doc)


def decided(doc, kind: str) -> None:
	_send(user_for_employee(doc.employee), _FOR_DECISION[kind], doc)
