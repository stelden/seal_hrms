# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Emails sent as work moves between a member of staff and their stand-in.

Every email is an Email Template named "Task Assignment - ...", shipped as a
fixture, so HR can reword it in Desk without a code change. Rendering never
fails a send: if a template is missing, empty, or its Jinja does not render,
the built-in wording below is used instead and the problem is logged. A handover
email that silently stopped because someone mistyped a tag would be worse than
slightly stale wording.

Each email lists only the work in THIS assignment. The 2024 version listed every
open ToDo between the two people, so a stand-in covering the same colleague
twice was sent last year's work as if it were new.

Sending never fails the move either: work that reached the right list matters
more than the email about it.

Every template is given the same variables, so a reworded template can use any
of them (listed in `_context`). User-entered text is escaped before it reaches
the template.
"""

import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, get_url_to_form

from seal_hrms.seal_hrms.handover import summary_lines, user_for_employee

PREFIX = "Task Assignment - "
ASKED_TO_COVER = PREFIX + "Asked to Cover"
HANDED_OVER = PREFIX + "Now Covering"
AGREED = PREFIX + "Agreed"
DECLINED = PREFIX + "Declined"
RETURN_NOTE_DUE = PREFIX + "Back Tomorrow"
WELCOME_BACK = PREFIX + "Welcome Back"
WITHDRAWN = PREFIX + "Called Off"
PREPARE = PREFIX + "Prepare Your Handover"
STRANDED_TO_OWNER = PREFIX + "Old Work Returned to You"
STRANDED_TO_STAND_IN = PREFIX + "Old Work Returned to Its Owner"

ALL_TEMPLATES = (
	ASKED_TO_COVER, HANDED_OVER, AGREED, DECLINED, RETURN_NOTE_DUE, WELCOME_BACK,
	WITHDRAWN, PREPARE, STRANDED_TO_OWNER, STRANDED_TO_STAND_IN,
)


def render(template_name: str, context: dict, fallback_subject: str, fallback_message: str) -> tuple[str, str]:
	"""(subject, message) from the named Email Template, or the fallback. Never raises."""
	try:
		row = frappe.db.get_value(
			"Email Template", template_name, ["subject", "response", "response_html", "use_html"], as_dict=True
		)
	except Exception:
		row = None
	if not row:
		return fallback_subject, fallback_message
	body = (row.response_html if row.use_html else row.response) or ""
	if not (row.subject and body.strip()):
		return fallback_subject, fallback_message
	try:
		return frappe.render_template(row.subject, context), frappe.render_template(body, context)
	except Exception:
		frappe.log_error(
			title=f"Task Assignment: email template did not render: {template_name}",
			message=frappe.get_traceback(),
		)
		return fallback_subject, fallback_message


def _context(assignment=None, **extra) -> dict:
	"""The variables every template may use."""
	context = {
		"employee_name": "", "stand_in_name": "", "leave_from": "", "leave_to": "", "return_date": "",
		"handover": "", "link": "", "items": [], "reason": "", "done_count": 0, "has_note": False,
		"days_until": 0, "leave_application": "",
	}
	if assignment is not None:
		context.update({
			"employee_name": escape_html(assignment.employee_name or ""),
			"stand_in_name": escape_html(assignment.get("task_assignee_name") or ""),
			"leave_from": formatdate(assignment.leave_from) if assignment.get("leave_from") else "",
			"leave_to": formatdate(assignment.leave_to) if assignment.get("leave_to") else "",
			"return_date": formatdate(assignment.return_date) if assignment.get("return_date") else "",
			"handover": assignment.name,
			"link": get_url_to_form(assignment.doctype, assignment.name),
			"has_note": bool(assignment.get("return_summary")),
		})
	context.update(extra)
	context["items"] = [escape_html(i) for i in context["items"]]
	return context


def _fallback_body(paragraphs: list[str], items: list[str]) -> str:
	body = "".join(f"<p>{p}</p>" for p in paragraphs)
	if items:
		body += "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
	return body


def _send(recipient, template, context, fallback_subject, paragraphs, doctype, name) -> None:
	if not recipient:
		return
	subject, message = render(template, context, fallback_subject, _fallback_body(paragraphs, context["items"]))
	try:
		frappe.sendmail(
			recipients=[recipient], subject=subject, message=message, reference_doctype=doctype, reference_name=name
		)
	except Exception:
		frappe.log_error(
			title="Task Assignment: email not sent", message=frappe.get_traceback(),
			reference_doctype=doctype, reference_name=name,
		)


def _to(assignment, recipient, template, context, fallback_subject, paragraphs) -> None:
	_send(recipient, template, context, fallback_subject, paragraphs, assignment.doctype, assignment.name)


def asked_to_cover(assignment, stand_in_employee: str, rows) -> None:
	"""Tell a stand-in what they are being asked to cover, before anything moves."""
	c = _context(assignment, items=summary_lines(assignment, rows))
	_to(assignment, user_for_employee(stand_in_employee), ASKED_TO_COVER, c,
	    _("{0} has asked you to cover their work").format(c["employee_name"]), [
		_("{0} will be on leave from {1} to {2}, and has asked you to cover the work below.").format(
			c["employee_name"], c["leave_from"], c["leave_to"]),
		_('Open <a href="{0}">{1}</a> to accept or decline. Nothing moves to your list until the leave starts.').format(
			c["link"], c["handover"]),
	])


def work_handed_over(assignment, stand_in_employee: str, rows) -> None:
	"""Tell a stand-in the work is now on their list."""
	c = _context(assignment, items=summary_lines(assignment, rows))
	_to(assignment, user_for_employee(stand_in_employee), HANDED_OVER, c,
	    _("You are now covering for {0}").format(c["employee_name"]), [
		_("{0} is on leave from {1}. This work is now on your list.").format(c["employee_name"], c["leave_from"]),
		_('Add notes on <a href="{0}">{1}</a> as you go, so {2} can pick up where you left off.').format(
			c["link"], c["handover"], c["employee_name"]),
	])


def answered(assignment, status: str) -> None:
	"""Tell the owner that everyone has agreed, or that someone has declined."""
	reasons = [assignment.get("decline_reason")] + [
		r.decline_reason for r in [*assignment.assignment_todos, *(assignment.get("authorities") or [])]
		if r.get("decline_reason")
	]
	c = _context(assignment, reason=escape_html("; ".join(r for r in reasons if r)))
	owner = user_for_employee(assignment.employee)
	if status == "Accepted":
		_to(assignment, owner, AGREED, c, _("Your handover has been agreed"), [
			_("Everyone you asked has agreed to cover your work during your leave ({0} to {1}).").format(
				c["leave_from"], c["leave_to"]),
		])
	else:
		_to(assignment, owner, DECLINED, c, _("A stand-in cannot cover your work"), [
			_("Someone you asked to cover your leave ({0} to {1}) has declined: {2}").format(
				c["leave_from"], c["leave_to"], c["reason"]),
			_('Open <a href="{0}">{1}</a>, cancel it and amend it with someone else. Nothing has moved yet.').format(
				c["link"], c["handover"]),
		])


def return_note_due(assignment, stand_in_employee: str) -> None:
	"""Remind a stand-in, the day before, to leave a note for the owner's return."""
	c = _context(assignment)
	_to(assignment, user_for_employee(stand_in_employee), RETURN_NOTE_DUE, c,
	    _("{0} is back tomorrow").format(c["employee_name"]), [
		_("{0} returns on {1}, and what you are still covering goes back to them that morning.").format(
			c["employee_name"], c["return_date"]),
		_('Leave them a note on <a href="{0}">{1}</a>: what you finished, what is waiting, and who called.').format(
			c["link"], c["handover"]),
	])


def welcome_back(assignment) -> None:
	"""Tell the employee what came back, and what was finished while they were away."""
	returned = [r for r in assignment.assignment_todos if r.row_status == "Handed Back"]
	done = [r for r in assignment.assignment_todos if r.row_status == "Done while away"]
	c = _context(assignment, items=summary_lines(assignment, returned), done_count=len(done))
	paragraphs = [_("Welcome back. Your work has been returned to your list.")]
	if done:
		paragraphs.append(_('{0} item(s) were finished while you were away; see the notes on <a href="{1}">{2}</a>.').format(
			len(done), c["link"], c["handover"]))
	if c["has_note"]:
		paragraphs.append(_('Your stand-in left a note for you on <a href="{0}">{1}</a>.').format(c["link"], c["handover"]))
	_to(assignment, user_for_employee(assignment.employee), WELCOME_BACK, c,
	    _("Welcome back: your work is on your list again"), paragraphs)


def assignment_withdrawn(assignment, stand_in_employee: str) -> None:
	"""Tell a stand-in the handover is off, because the leave was rejected or cancelled."""
	c = _context(assignment)
	_to(assignment, user_for_employee(stand_in_employee), WITHDRAWN, c,
	    _("You no longer need to cover for {0}").format(c["employee_name"]), [
		_("The leave {0} asked you to cover ({1} to {2}) has been withdrawn. Anything you were given has gone back to them.").format(
			c["employee_name"], c["leave_from"], c["leave_to"]),
	])


def prepare_your_handover(leave, employee_name: str, days_until: int) -> None:
	"""Remind someone with leave coming up that nobody is covering their work yet."""
	c = _context(
		employee_name=escape_html(employee_name or ""),
		leave_from=formatdate(leave.from_date), leave_to=formatdate(leave.to_date),
		link=get_url_to_form("Leave Application", leave.name), leave_application=leave.name, days_until=days_until,
	)
	_send(user_for_employee(leave.employee), PREPARE, c, _("Hand over your work before your leave on {0}").format(c["leave_from"]), [
		_("Your leave starts on {0}, and nobody has been asked to cover your work yet.").format(c["leave_from"]),
		_('Open <a href="{0}">your leave application</a> and click Prepare Handover. It lists your open work, and you name who covers it.').format(c["link"]),
	], "Leave Application", leave.name)


def stranded_work_returned(assignment, recipient_user: str, lines: list[str], to_owner: bool) -> None:
	"""The one-off return of work that stayed with a stand-in after an old leave ended."""
	c = _context(assignment, items=lines)
	if to_owner:
		_to(assignment, recipient_user, STRANDED_TO_OWNER, c, _("Work you handed over has been returned to you"), [
			_("When you went on leave, some of your work was passed to a stand-in and never came back. It is on your list again."),
		])
	else:
		_to(assignment, recipient_user, STRANDED_TO_STAND_IN, c, _("Work you covered has gone back to its owner"), [
			_("You were covering some of {0}'s work during leave that has since ended. It has gone back to them.").format(
				c["employee_name"]),
		])
