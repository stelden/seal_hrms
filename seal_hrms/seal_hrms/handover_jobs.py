# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Daily work for Task Assignments.

Each assignment is handled in its own try/except and committed on its own, so
one broken record cannot hold up everybody else's return.
"""

import frappe
from frappe.utils import getdate, today

from seal_hrms.seal_hrms import handover
from seal_hrms.seal_hrms.handover import ASSIGNMENT, Status


def daily() -> None:
	"""Scheduler entry point."""
	hand_back_ended_leave()


def hand_back_ended_leave(on_date=None) -> list[str]:
	"""Return the work of everyone whose leave has ended. Returns the assignments handled."""
	on_date = getdate(on_date or today())
	due = frappe.get_all(
		ASSIGNMENT,
		filters=[["docstatus", "=", 1], ["status", "=", Status.ACTIVE], ["leave_to", "<", on_date]],
		pluck="name",
	)
	done = []
	for name in due:
		try:
			if handover.hand_back(name):
				done.append(name)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				title="Task Assignment: work could not be returned",
				message=frappe.get_traceback(),
				reference_doctype=ASSIGNMENT,
				reference_name=name,
			)
	return done
