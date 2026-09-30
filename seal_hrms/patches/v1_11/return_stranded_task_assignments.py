# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Give Task Assignment a status, and return work stranded by the 2024 code.

Before 1.3.0, a submitted Task Assignment edited each ToDo to point at the
stand-in and never pointed it back when the leave ended. Work therefore stayed
on stand-ins' lists indefinitely. On the MHC restore (2026-06) that was 21 ToDos
the rows name, plus 21 more the rows never recorded: tasks typed straight into
the handover were given a fresh ToDo that was never written back to the row.

Decision T1 (2026-09-30): stranded work goes back to its owner. The rule, in
full, is in `dev_notes/seal_hrms/TASK_ASSIGNMENT_DESIGN.md` §6. In short:

  * A ToDo is stranded when it is Open, still with the stand-in, and the leave of
    the most recent handover that lists it has ended.
  * Where several handovers list the same ToDo, only the latest one decides. If
    the ToDo is no longer with that handover's stand-in, someone has moved it
    since, so it is left where it is.
  * Nothing is guessed. An owner who has left, or has no login, and a free-text
    task that matches more than one ToDo, are all skipped and listed.
  * `assigned_by` was overwritten by the old code and cannot be recovered, so it
    is left as it is.
  * A handover whose stand-in is the owner themselves (the old form allowed it)
    moved nothing, so it has nothing to return.

Idempotent: a returned ToDo is no longer with its stand-in, so a second run finds
nothing to do and sends no second email. Status is only set where it is blank.

Every outcome is printed and logged under the title "Task Assignment return",
so the deploy log is the catalogue (SEAL_DEV_RULES §3.11).
"""

from collections import defaultdict

import frappe

from seal_hrms.seal_hrms import legacy_handover

ASSIGNMENT = "Task Assignment"
ROW = "Task Assignment ToDo"


def execute():
	if not frappe.db.table_exists(ASSIGNMENT):
		print("[task-assignment] no-op: doctype not installed")
		return

	classified = _classify()
	returned, skipped = _return_stranded()

	print(f"[task-assignment] status set on {classified} record(s)")
	print(f"[task-assignment] returned {len(returned)} stranded ToDo(s); skipped {len(skipped)}")
	for line in skipped:
		print(f"[task-assignment]   skipped: {line}")
	if returned or skipped:
		frappe.log_error(
			title="Task Assignment return: stranded work",
			message="Returned:\n" + "\n".join(returned or ["(none)"]) + "\n\nSkipped:\n" + "\n".join(skipped or ["(none)"]),
		)


def _classify() -> int:
	"""Status for records that predate it: submitted ones become Legacy.

	Adding the column with its default stamps every existing row "Draft" during
	the same migrate, before this patch runs. So "unclassified" means blank OR
	that default on a record that is not actually a draft: the new flow never
	leaves a submitted or cancelled handover in Draft, which also keeps this
	idempotent.
	"""
	count = 0
	for docstatus, status in ((0, "Draft"), (1, "Legacy"), (2, "Cancelled")):
		unclassified = ["", None] if docstatus == 0 else ["", None, "Draft"]
		names = frappe.get_all(
			ASSIGNMENT,
			filters=[["docstatus", "=", docstatus], ["status", "in", unclassified]],
			pluck="name",
		)
		for name in names:
			frappe.db.set_value(ASSIGNMENT, name, "status", status, update_modified=False)
		count += len(names)
	return count


def _return_stranded():
	returnable, skipped = legacy_handover.find_stranded()
	returned = []
	by_assignment = defaultdict(list)
	for item in returnable:
		doc = frappe.get_doc("ToDo", item.todo)
		doc.allocated_to = item.to_user
		doc.save(ignore_permissions=True)
		frappe.db.set_value(
			ROW, item.row, {"todo": item.todo, "row_status": "Handed Back"}, update_modified=False
		)
		returned.append(f"{item.todo} ({item.assignment}): {item.from_user} -> {item.to_user}")
		by_assignment[item.assignment].append(item)
	_notify(by_assignment)
	return returned, skipped


def _notify(by_assignment) -> None:
	from seal_hrms.seal_hrms import handover_notifications

	for parent, items in by_assignment.items():
		assignment = frappe.get_doc(ASSIGNMENT, parent)
		lines = [item.description for item in items]
		handover_notifications.stranded_work_returned(assignment, items[0].to_user, lines, to_owner=True)
		handover_notifications.stranded_work_returned(assignment, items[0].from_user, lines, to_owner=False)
