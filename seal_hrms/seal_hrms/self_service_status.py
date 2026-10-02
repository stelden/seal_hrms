# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What a member of staff has in flight about themselves: leave, claims, advances,
timesheets. Counted for the Employee linked to the person asking.

Plain records and plain Frappe calls: this module knows nothing about My Desk and runs on
any site. The My Desk adapter (`desk/providers.py`) turns its answers into figures.
Every count goes through `frappe.get_list`, so the person's own permissions apply.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import frappe
from frappe import _


@dataclass
class Figure:
	"""One count, and the list a person opens to see what was counted."""

	key: str
	caption: str
	doctype: str
	filters: list = field(default_factory=list)
	count: int = 0

	def route_options(self) -> dict:
		"""One condition per field, so the list shows exactly what was counted (§2.16)."""
		fields = [f[0] for f in self.filters]
		if len(fields) != len(set(fields)):
			raise ValueError(f"{self.key}: two conditions on one field cannot be a list route")
		return {f[0]: f[2] if f[1] == "=" else [f[1], f[2]] for f in self.filters}


def employee_of(user: str) -> str | None:
	"""The active Employee whose user is `user`. Their own id is a filter value, not data
	shown, so it is read directly even where the person may not read Employee."""
	return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")


def self_service(user: str, readable=None) -> list[Figure]:
	"""Leave still open, claims in approval and approved but unpaid, advances unpaid and
	to settle, timesheets in draft. Nothing at all for someone with no Employee record.

	`readable`: doctypes the person may read; a figure on any other is left out rather
	than shown as nought, which would claim there is nothing there."""
	employee = employee_of(user)
	if not employee:
		return []
	mine = ["employee", "=", employee]
	figures = [
		Figure("leave_open", _("Leave awaiting a decision"), "Leave Application", [mine, ["status", "=", "Open"], ["docstatus", "=", 0]]),
		Figure("claims_in_approval", _("Claims in approval"), "Expense Claim", [mine, ["docstatus", "=", 0]]),
		Figure("claims_unpaid", _("Claims approved, not paid"), "Expense Claim", [mine, ["docstatus", "=", 1], ["status", "=", "Unpaid"]]),
		Figure("advances_unpaid", _("Advances not yet paid"), "Employee Advance", [mine, ["docstatus", "=", 1], ["status", "=", "Unpaid"]]),
		Figure("advances_to_settle", _("Advances to settle"), "Employee Advance", [mine, ["docstatus", "=", 1], ["status", "in", ["Paid", "Partially Paid"]]]),
		Figure("timesheets_draft", _("Timesheets in draft"), "Timesheet", [mine, ["docstatus", "=", 0]]),
	]
	out = []
	for fig in figures:
		if not frappe.db.exists("DocType", fig.doctype) or (readable is not None and fig.doctype not in readable):
			continue
		rows = frappe.get_list(fig.doctype, filters=fig.filters, fields=[{"COUNT": "*", "as": "n"}], order_by=None)
		fig.count = int(rows[0].n or 0) if rows else 0
		out.append(fig)
	return out
