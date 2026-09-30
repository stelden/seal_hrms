# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Moving a member of staff's work to their stand-in, and back again.

A Task Assignment row is one piece of work. Moving it and giving it back are the
only two things that ever happen to it, and both live here so that the
controller, the scheduler, the Leave Application hooks and the legacy patch all
move work the same way.

How a row moves (`move_row`):

  * the stand-in gets a NEW ToDo, through Frappe's own assignment path when the
    work is about a document. That path posts the "assigned" comment, notifies
    the stand-in, and shares the document with them if they could not otherwise
    open it — which the 2024 code never did, so a stand-in could be handed work
    they had no way to reach;
  * the employee's own ToDo is set to Cancelled, not edited. Its `assigned_by`
    is therefore never overwritten, and whoever originally gave the work out is
    kept on the row as `original_assignor` for the return journey.

How it comes back (`hand_back_row`):

  * work the stand-in finished stays finished ("Done while away");
  * anything still open is cancelled on the stand-in's list and assigned back to
    the employee, from the original assignor;
  * a share this module created for the stand-in is removed again. A share or
    an assignment the stand-in already had before the handover is left alone.

Every step is idempotent: a row remembers how far it has got, and the parent is
locked for update before a whole assignment moves (SEAL_DEV_RULES §3.3), so a
scheduler run racing a button press does the work once.
"""

import frappe
from frappe import _
from frappe.desk.form import assign_to
from frappe.utils import add_days, cstr, getdate, now_datetime, today

ASSIGNMENT = "Task Assignment"
ROW = "Task Assignment ToDo"


class Status:
	"""Where a whole Task Assignment has got to."""

	DRAFT = "Draft"
	AWAITING = "Awaiting Acceptance"
	ACCEPTED = "Accepted"
	DECLINED = "Declined"
	ACTIVE = "Active"
	HANDED_BACK = "Handed Back"
	CANCELLED = "Cancelled"
	# Submitted before this module existed. Never moved by the new flow.
	LEGACY = "Legacy"


class RowStatus:
	"""Where one piece of work has got to."""

	WITH_EMPLOYEE = ""
	HANDED_OVER = "Handed Over"
	DONE_WHILE_AWAY = "Done while away"
	HANDED_BACK = "Handed Back"
	# The employee had already finished it before the handover took effect.
	ALREADY_DONE = "Already done"


class Answer:
	PENDING = "Pending"
	ACCEPTED = "Accepted"
	DECLINED = "Declined"


def return_date_for(employee: str, leave_to) -> str | None:
	"""The first working day after the leave, on the employee's own holiday list."""
	if not leave_to:
		return None
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	day = getdate(add_days(leave_to, 1))
	# HRMS answers through Holiday List Assignment, effective from a date, so ask for the return day.
	holiday_list = get_holiday_list_for_employee(employee, raise_exception=False, as_on=day)
	if not holiday_list:
		return day
	holidays = set(
		getdate(d)
		for d in frappe.get_all(
			"Holiday",
			filters={"parent": holiday_list, "holiday_date": ["between", [day, add_days(day, 60)]]},
			pluck="holiday_date",
		)
	)
	for _step in range(60):
		if day not in holidays:
			return day
		day = getdate(add_days(day, 1))
	return day


def user_for_employee(employee: str | None) -> str | None:
	"""The login of an employee, or None if they have none."""
	if not employee:
		return None
	return frappe.db.get_value("Employee", employee, "user_id") or None


def _reference(row) -> tuple[str | None, str | None]:
	"""The document this piece of work is about, if it still exists."""
	if row.reference_type and row.reference_name and frappe.db.exists(row.reference_type, row.reference_name):
		return row.reference_type, row.reference_name
	return None, None


def _open_todo(reference_type, reference_name, user) -> str | None:
	return frappe.db.get_value(
		"ToDo",
		{
			"reference_type": reference_type,
			"reference_name": reference_name,
			"allocated_to": user,
			"status": "Open",
		},
		"name",
		order_by="creation desc",
	)


def _give(row, user: str, assigned_by: str) -> tuple[str, bool, bool]:
	"""Put this piece of work on `user`'s list.

	Returns (todo name, the user already had it, a share was created for them).
	"""
	reference_type, reference_name = _reference(row)
	if not reference_type:
		todo = frappe.new_doc("ToDo")
		todo.allocated_to = user
		todo.assigned_by = assigned_by
		todo.description = row.description
		todo.priority = row.priority or "Medium"
		todo.date = row.due_date
		todo.status = "Open"
		todo.insert(ignore_permissions=True)
		return todo.name, False, False

	existing = _open_todo(reference_type, reference_name, user)
	if existing:
		return existing, True, False

	reference = frappe.get_doc(reference_type, reference_name)
	needs_share = not frappe.has_permission(doc=reference, user=user)
	if needs_share:
		# Shared here rather than left to assign_to, which checks that whoever
		# is logged in may share the document. Work moves when a stand-in
		# accepts or an owner comes back early, and neither can share a
		# document they do not own. Read and write, because covering work
		# usually means updating it; never submit, which stays with the owner.
		frappe.share.add_docshare(
			reference_type, reference_name, user, read=1, write=1, flags={"ignore_share_permission": True}
		)
	args = {
		"assign_to": [user],
		"doctype": reference_type,
		"name": reference_name,
		"description": row.description,
		"priority": row.priority or "Medium",
		"assigned_by": assigned_by,
	}
	if row.due_date:
		args["date"] = row.due_date
	assign_to._add(args, ignore_permissions=True)
	return _open_todo(reference_type, reference_name, user), False, needs_share


def _unshare(reference_type, reference_name, user) -> None:
	"""Close a share this module opened. Like opening it, not the session user's decision."""
	share = frappe.db.get_value(
		"DocShare", {"share_doctype": reference_type, "share_name": reference_name, "user": user}, "name"
	)
	if share:
		frappe.delete_doc("DocShare", share, ignore_permissions=True, flags={"ignore_share_permission": True})


def _set_todo_status(todo_name: str | None, status: str) -> None:
	if not todo_name or not frappe.db.exists("ToDo", todo_name):
		return
	todo = frappe.get_doc("ToDo", todo_name)
	if todo.status == status:
		return
	todo.status = status
	todo.save(ignore_permissions=True)


def move_row(row, employee_user: str, stand_in_user: str) -> None:
	"""Hand one piece of work to the stand-in. A row already moved is left alone."""
	if row.row_status and row.row_status != RowStatus.WITH_EMPLOYEE:
		return

	original = None
	if row.todo and frappe.db.exists("ToDo", row.todo):
		original = frappe.get_doc("ToDo", row.todo)
		if not row.reference_type and original.reference_type:
			row.reference_type, row.reference_name = original.reference_type, original.reference_name

	if original and original.status == "Closed":
		row.row_status = RowStatus.ALREADY_DONE
		row.db_update()
		return

	assignor = (original.assigned_by if original else None) or employee_user
	todo, already_had_it, shared = _give(row, stand_in_user, assigned_by=employee_user)

	# Only now take it off the employee's list: if giving it failed above, the
	# work stays where it was rather than vanishing from both lists.
	if original and original.status == "Open" and original.allocated_to == employee_user:
		_set_todo_status(original.name, "Cancelled")

	row.original_assignor = assignor
	row.stand_in_todo = todo
	row.stand_in_already_had_it = 1 if already_had_it else 0
	row.shared_with_stand_in = 1 if shared else 0
	row.row_status = RowStatus.HANDED_OVER
	row.db_update()


def hand_back_row(row, employee_user: str, stand_in_user: str) -> None:
	"""Give one piece of work back to the employee. Only a row that moved can come back."""
	if row.row_status != RowStatus.HANDED_OVER:
		return

	stand_in_status = frappe.db.get_value("ToDo", row.stand_in_todo, "status") if row.stand_in_todo else None

	if stand_in_status == "Closed":
		row.row_status = RowStatus.DONE_WHILE_AWAY
		if row.todo:
			_set_todo_status(row.todo, "Closed")
	else:
		if stand_in_status == "Open" and not row.stand_in_already_had_it:
			_set_todo_status(row.stand_in_todo, "Cancelled")
		todo, _already, _shared = _give(row, employee_user, assigned_by=row.original_assignor or employee_user)
		row.todo = todo
		row.row_status = RowStatus.HANDED_BACK

	reference_type, reference_name = _reference(row)
	if row.shared_with_stand_in and reference_type and not _open_todo(reference_type, reference_name, stand_in_user):
		_unshare(reference_type, reference_name, stand_in_user)
		row.shared_with_stand_in = 0

	row.db_update()


def covered_by(assignment, row) -> str | None:
	"""The employee covering this row: the row's own stand-in, else the assignment's."""
	return row.get("task_assignee") or assignment.task_assignee


def answers_for_itself(assignment, row) -> bool:
	"""A row names its own stand-in, different from the assignment's, who answers for it."""
	return bool(row.get("task_assignee")) and row.task_assignee != assignment.task_assignee


def answer_for(assignment, row) -> str | None:
	"""Whether whoever covers this row agreed to."""
	return row.get("acceptance") if answers_for_itself(assignment, row) else assignment.get("acceptance")


def _stand_in_for(assignment, row) -> str | None:
	return user_for_employee(covered_by(assignment, row))


def _rows_to_move(assignment):
	"""Rows that are handed over when the assignment takes effect.

	Only work somebody agreed to carry moves. A declined row stays with the
	employee; the approval gate is what stops leave going ahead that way.
	"""
	return [row for row in assignment.assignment_todos if answer_for(assignment, row) == Answer.ACCEPTED]


def stand_ins(assignment) -> dict[str, list]:
	"""Each stand-in, with the work rows they cover. Anyone who approves in the owner's place is listed too."""
	covering = {assignment.task_assignee: []} if assignment.task_assignee else {}
	for row in assignment.assignment_todos:
		covering.setdefault(covered_by(assignment, row), []).append(row)
	for row in assignment.get("authorities") or []:
		covering.setdefault(covered_by(assignment, row), [])
	covering.pop(None, None)
	return covering


def overall_answer(assignment) -> str:
	"""Declined if anyone declined, Accepted once everyone has, otherwise Pending."""
	answers = [assignment.get("acceptance")] + [
		row.acceptance for row in assignment.assignment_todos if answers_for_itself(assignment, row)
	] + [row.acceptance for row in assignment.get("authorities") or []]
	if Answer.DECLINED in answers:
		return Answer.DECLINED
	if all(a == Answer.ACCEPTED for a in answers):
		return Answer.ACCEPTED
	return Answer.PENDING


def leave_is_approved(assignment) -> bool:
	if not assignment.leave_application:
		return False
	return bool(frappe.db.get_value(
		"Leave Application",
		{"name": assignment.leave_application, "docstatus": 1, "status": "Approved"},
		"name",
	))


def maybe_activate(name: str, on_date=None) -> bool:
	"""Hand the work over if everything is in place for it: agreed, approved, and the leave has started."""
	on_date = getdate(on_date or today())
	assignment = frappe.get_doc(ASSIGNMENT, name)
	if assignment.docstatus != 1 or assignment.status != Status.ACCEPTED:
		return False
	if not assignment.leave_from or getdate(assignment.leave_from) > on_date:
		return False
	if not leave_is_approved(assignment):
		return False
	if not activate(name):
		return False
	assignment.reload()
	from seal_hrms.seal_hrms import handover_notifications

	for employee, rows in stand_ins(assignment).items():
		moved = [r for r in rows if r.row_status == RowStatus.HANDED_OVER]
		handover_notifications.work_handed_over(assignment, employee, moved)
	return True


def activate(name: str) -> bool:
	"""Hand the assignment's work to its stand-ins. Returns True if this call did it.

	Row-locks the assignment first (§3.3): a second caller blocks, then sees
	`activated_at` set and returns False without touching anything.
	"""
	if frappe.db.get_value(ASSIGNMENT, name, "activated_at", for_update=True):
		return False

	assignment = frappe.get_doc(ASSIGNMENT, name)
	employee_user = user_for_employee(assignment.employee)
	if not employee_user:
		frappe.log_error(
			title="Task Assignment: employee has no login",
			message=f"{name}: {assignment.employee} has no user, so there is no list to take work from.",
			reference_doctype=ASSIGNMENT,
			reference_name=name,
		)
		return False

	for row in _rows_to_move(assignment):
		stand_in_user = _stand_in_for(assignment, row)
		if not stand_in_user:
			continue
		move_row(row, employee_user, stand_in_user)

	from seal_hrms.seal_hrms import acting

	# Approvals move with the work (acting.py). Status goes Active only after,
	# because being Active is what makes the stand-in count as acting.
	assignment.db_set("status", Status.ACTIVE, update_modified=False)
	acting.grant_for(assignment)
	assignment.db_set({"status": Status.ACTIVE, "activated_at": now_datetime()}, update_modified=False)
	return True


def hand_back(name: str, final_status: str = Status.HANDED_BACK) -> bool:
	"""Give every piece of moved work back to the employee. Returns True if this call did it."""
	if frappe.db.get_value(ASSIGNMENT, name, "handed_back_at", for_update=True):
		return False

	assignment = frappe.get_doc(ASSIGNMENT, name)
	employee_user = user_for_employee(assignment.employee)
	moved = [row for row in assignment.assignment_todos if row.row_status == RowStatus.HANDED_OVER]

	if employee_user:
		for row in moved:
			stand_in_user = _stand_in_for(assignment, row)
			if stand_in_user:
				hand_back_row(row, employee_user, stand_in_user)

	from seal_hrms.seal_hrms import acting

	acting.revoke_for(assignment)
	assignment.db_set({"status": final_status, "handed_back_at": now_datetime()}, update_modified=False)
	# A cancelled leave is not a return, so there is no "welcome back" for it.
	if moved and employee_user and final_status == Status.HANDED_BACK:
		from seal_hrms.seal_hrms import handover_notifications

		handover_notifications.welcome_back(assignment)
	return True


def summary_lines(assignment, rows) -> list[str]:
	"""One plain line per piece of work, for emails."""
	lines = []
	for row in rows:
		line = cstr(frappe.utils.strip_html(row.description or "")).strip() or _("(no description)")
		if row.reference_type and row.reference_name:
			line += f" — {_(row.reference_type)} {row.reference_name}"
		if row.due_date:
			line += " — " + _("due {0}").format(frappe.utils.formatdate(row.due_date))
		lines.append(line)
	return lines
