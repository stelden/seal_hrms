# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Emails sent as work moves between a member of staff and their stand-in.

Each email lists only the work in THIS assignment. The 2024 version listed every
open ToDo between the two people, so a stand-in covering the same colleague
twice was sent last year's work as if it were new.

Sending never fails the move: work that reached the right list matters more
than the email about it, so a mail error is logged and swallowed here.
"""

import frappe
from frappe import _
from frappe.utils import escape_html, formatdate

from seal_hrms.seal_hrms.handover import summary_lines, user_for_employee


def _send(recipient: str | None, subject: str, paragraphs: list[str], lines: list[str], assignment) -> None:
	if not recipient:
		return
	body = "".join(f"<p>{p}</p>" for p in paragraphs)
	if lines:
		body += "<ul>" + "".join(f"<li>{escape_html(line)}</li>" for line in lines) + "</ul>"
	try:
		frappe.sendmail(
			recipients=[recipient],
			subject=subject,
			message=body,
			reference_doctype=assignment.doctype,
			reference_name=assignment.name,
		)
	except Exception:
		frappe.log_error(
			title="Task Assignment: email not sent",
			message=frappe.get_traceback(),
			reference_doctype=assignment.doctype,
			reference_name=assignment.name,
		)


def _dates(assignment) -> str:
	return _("{0} to {1}").format(formatdate(assignment.leave_from), formatdate(assignment.leave_to))


def asked_to_cover(assignment, stand_in_employee: str, rows) -> None:
	"""Tell a stand-in what they are being asked to cover, before anything moves."""
	_send(
		user_for_employee(stand_in_employee),
		_("{0} has asked you to cover their work").format(assignment.employee_name),
		[
			_("{0} will be on leave from {1}, and has asked you to cover the work below.").format(
				escape_html(assignment.employee_name), _dates(assignment)
			),
			_("Open {0} to accept or decline. Nothing moves to your list until the leave starts.").format(
				assignment.name
			),
		],
		summary_lines(assignment, rows),
		assignment,
	)


def work_handed_over(assignment, stand_in_employee: str, rows) -> None:
	"""Tell a stand-in the work is now on their list."""
	_send(
		user_for_employee(stand_in_employee),
		_("You are now covering for {0}").format(assignment.employee_name),
		[
			_("{0} is on leave from {1}. This work is now on your list.").format(
				escape_html(assignment.employee_name), _dates(assignment)
			),
			_("Add notes on {0} as you go, so {1} can pick up where you left off.").format(
				assignment.name, escape_html(assignment.employee_name)
			),
		],
		summary_lines(assignment, rows),
		assignment,
	)


def welcome_back(assignment) -> None:
	"""Tell the employee what came back, and what was finished while they were away."""
	returned = [r for r in assignment.assignment_todos if r.row_status == "Handed Back"]
	done = [r for r in assignment.assignment_todos if r.row_status == "Done while away"]
	paragraphs = [_("Welcome back. Your work has been returned to your list.")]
	if done:
		paragraphs.append(
			_("{0} item(s) were finished while you were away; see the notes on {1}.").format(len(done), assignment.name)
		)
	if assignment.get("return_summary"):
		paragraphs.append(_("Your stand-in left a note for you on {0}.").format(assignment.name))
	_send(
		user_for_employee(assignment.employee),
		_("Welcome back: your work is on your list again"),
		paragraphs,
		summary_lines(assignment, returned),
		assignment,
	)


def answered(assignment, status: str) -> None:
	"""Tell the owner that everyone has agreed, or that someone has declined."""
	if status == "Accepted":
		subject = _("Your handover has been agreed")
		paragraphs = [_("Everyone you asked has agreed to cover your work during your leave ({0}).").format(_dates(assignment))]
	else:
		subject = _("A stand-in cannot cover your work")
		paragraphs = [
			_("Someone you asked to cover your leave ({0}) has declined. Their reason is on {1}.").format(
				_dates(assignment), assignment.name
			),
			_("Cancel the handover and amend it with someone else. Nothing has moved yet."),
		]
	_send(user_for_employee(assignment.employee), subject, paragraphs, [], assignment)


def return_note_due(assignment, stand_in_employee: str) -> None:
	"""Remind a stand-in, the day before, to leave a note for the owner's return."""
	_send(
		user_for_employee(stand_in_employee),
		_("{0} is back tomorrow").format(assignment.employee_name),
		[
			_("{0} returns on {1}, and what you are still covering goes back to them that morning.").format(
				escape_html(assignment.employee_name), formatdate(assignment.return_date)
			),
			_("Leave them a note on {0}: what you finished, what is waiting, and who called.").format(assignment.name),
		],
		[],
		assignment,
	)


def assignment_withdrawn(assignment, stand_in_employee: str) -> None:
	"""Tell a stand-in the handover is off, because the leave was rejected or cancelled."""
	_send(
		user_for_employee(stand_in_employee),
		_("You no longer need to cover for {0}").format(assignment.employee_name),
		[
			_("The leave {0} asked you to cover ({1}) has been withdrawn. Anything you were given has gone back to them.").format(
				escape_html(assignment.employee_name), _dates(assignment)
			)
		],
		[],
		assignment,
	)


def stranded_work_returned(assignment, recipient_user: str, lines: list[str], to_owner: bool) -> None:
	"""The one-off return of work that stayed with a stand-in after an old leave ended."""
	if to_owner:
		subject = _("Work you handed over has been returned to you")
		paragraph = _(
			"When you went on leave, some of your work was passed to a stand-in and never came back. "
			"It is on your list again."
		)
	else:
		subject = _("Work you covered has gone back to its owner")
		paragraph = _(
			"You were covering some of {0}'s work during leave that has since ended. It has gone back to them."
		).format(escape_html(assignment.employee_name))
	_send(recipient_user, subject, [paragraph], lines, assignment)
