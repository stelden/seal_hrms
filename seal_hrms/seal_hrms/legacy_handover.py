# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Which pre-1.3.0 handovers left work stranded with a stand-in.

Read only. The one-off return patch (`patches/v1_11/return_stranded_task_assignments`)
acts on what `find_stranded` reports, and the health check counts the same
thing, so the two can never disagree about what "stranded" means. They did,
briefly: the check counted work still with the stand-in of ANY old handover,
while the patch lets only the most recent one decide.

The rule is decision T1 in `dev_notes/seal_hrms/TASK_ASSIGNMENT_DESIGN.md` §6.
"""

from collections import defaultdict

import frappe
from frappe.utils import getdate, today

ASSIGNMENT = "Task Assignment"
ROW = "Task Assignment ToDo"


def legacy_assignments():
	rows = frappe.db.sql(
		"""
		SELECT a.name, a.employee, a.employee_name, a.task_assignee, a.leave_to,
		       ee.user_id AS employee_user, ee.status AS employee_status,
		       se.user_id AS stand_in_user
		FROM `tabTask Assignment` a
		LEFT JOIN `tabEmployee` ee ON ee.name = a.employee
		LEFT JOIN `tabEmployee` se ON se.name = a.task_assignee
		WHERE a.docstatus = 1 AND a.status = 'Legacy'
		""",
		as_dict=True,
	)
	for row in rows:
		row.leave_to = getdate(row.leave_to) if row.leave_to else None
	return {row.name: row for row in rows}


def _candidates(assignments) -> dict[str, list[tuple[str, str]]]:
	"""ToDo -> [(assignment, row)] for every row that points at, or produced, a ToDo."""
	found = defaultdict(list)
	rows = frappe.get_all(
		ROW,
		filters={"parenttype": ASSIGNMENT, "parent": ["in", list(assignments) or [""]]},
		fields=["name", "parent", "todo", "description", "reference_type", "reference_name"],
	)
	for row in rows:
		if row.todo:
			found[row.todo].append((row.parent, row.name))
			continue
		# A task typed straight into the handover: find the ToDo the old code
		# created for it. It must match exactly, and match only one.
		assignment = assignments[row.parent]
		if not (assignment.stand_in_user and assignment.employee_user):
			continue
		filters = [
			["allocated_to", "=", assignment.stand_in_user],
			["assigned_by", "=", assignment.employee_user],
			["description", "=", row.description],
			["reference_name", "=", row.reference_name] if row.reference_name else ["reference_name", "is", "not set"],
		]
		matches = frappe.get_all("ToDo", filters=filters, pluck="name")
		if len(matches) == 1:
			found[matches[0]].append((row.parent, row.name))
		elif len(matches) > 1:
			found[f"ambiguous:{row.name}"].append((row.parent, row.name))
	return found


def find_stranded(on_date=None):
	"""Returns (returnable, skipped).

	`returnable` is a list of dicts: todo, assignment, row, from_user, to_user,
	description. `skipped` is a list of sentences, one per piece of work that
	looks stranded but must not be moved automatically.
	"""
	on_date = getdate(on_date or today())
	assignments = legacy_assignments()
	returnable, skipped = [], []

	for todo_name, owners in _candidates(assignments).items():
		if todo_name.startswith("ambiguous:"):
			parent, _row = owners[0]
			skipped.append(f"{parent}: a typed-in task matches more than one ToDo, so none was moved")
			continue
		todo = frappe.db.get_value(
			"ToDo", todo_name, ["name", "status", "allocated_to", "description"], as_dict=True
		)
		if not todo or todo.status != "Open":
			continue

		# The most recent handover listing this work is the one that decides.
		parent, row_name = max(owners, key=lambda o: assignments[o[0]].leave_to or getdate("1900-01-01"))
		assignment = assignments[parent]
		if not assignment.leave_to or assignment.leave_to >= on_date:
			continue
		# The 2024 form let someone name themselves as their own stand-in. Their
		# work never left them, so there is nothing to return.
		if assignment.stand_in_user and assignment.stand_in_user == assignment.employee_user:
			continue
		if todo.allocated_to != assignment.stand_in_user:
			if todo.allocated_to != assignment.employee_user:
				skipped.append(f"{todo_name} ({parent}): moved to {todo.allocated_to} since, left there")
			continue
		if assignment.employee_status != "Active" or not assignment.employee_user:
			skipped.append(f"{todo_name} ({parent}): owner {assignment.employee} has left or has no login")
			continue

		returnable.append(frappe._dict(
			todo=todo_name,
			assignment=parent,
			row=row_name,
			from_user=assignment.stand_in_user,
			to_user=assignment.employee_user,
			description=frappe.utils.strip_html(todo.description or "").strip(),
		))
	return returnable, skipped
