# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""HR-only Leave Planning admin endpoints.

Bulk operations triggered from the Compliance Dashboard. Per §3.7 each
member is throttled — at most one nudge per day even if HR clicks bulk
nudge multiple times.
"""

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, today

from seal_hrms.seal_hrms.leave_planning.permissions import HR_BACKOFFICE_ROLES


@frappe.whitelist()
def bulk_nudge_members(cycle: str, member_names: list[str] | str) -> dict:
	"""Send a one-shot reminder to selected Cycle Member rows.

	Returns: {nudged: int, throttled: int, skipped: int, reason_skipped: dict}
	"""
	_require_hr_role()

	if isinstance(member_names, str):
		import json
		try:
			member_names = json.loads(member_names)
		except (ValueError, TypeError):
			member_names = [member_names]
	if not member_names:
		return {"nudged": 0, "throttled": 0, "skipped": 0, "reason_skipped": {}}

	cycle_doc = frappe.get_doc("Leave Planning Cycle", cycle)
	if cycle_doc.status != "Open":
		frappe.throw(_("Cycle {0} is {1} — bulk nudge only works on Open cycles.").format(
			cycle, cycle_doc.status,
		))

	today_d = getdate(today())
	deadline = getdate(cycle_doc.submission_deadline) if cycle_doc.submission_deadline else None
	days_to_deadline = (deadline - today_d).days if deadline else 0

	nudged = 0
	throttled = 0
	skipped = 0
	reason_skipped: dict[str, int] = {}

	for member_name in member_names:
		row = frappe.db.get_value(
			"Leave Planning Cycle Member", member_name,
			["name", "cycle", "employee", "exempt", "plan_status", "last_nudge_at", "nudges_sent"],
			as_dict=True,
		)
		if not row or row.cycle != cycle:
			skipped += 1
			reason_skipped["wrong cycle"] = reason_skipped.get("wrong cycle", 0) + 1
			continue
		if row.exempt:
			skipped += 1
			reason_skipped["exempt"] = reason_skipped.get("exempt", 0) + 1
			continue
		if row.plan_status not in ("Not Started", "Draft", "Returned"):
			skipped += 1
			reason_skipped["already filed"] = reason_skipped.get("already filed", 0) + 1
			continue
		if row.last_nudge_at and getdate(row.last_nudge_at) >= today_d:
			throttled += 1
			continue

		try:
			from seal_hrms.seal_hrms.leave_planning.scheduler import (
				_send_employee_reminder_email,
			)
			_send_employee_reminder_email(cycle_doc, row, days_to_deadline)
			frappe.db.set_value(
				"Leave Planning Cycle Member", row.name,
				{
					"nudges_sent": int(row.nudges_sent or 0) + 1,
					"last_nudge_at": now_datetime(),
				},
				update_modified=False,
			)
			nudged += 1
		except Exception:
			frappe.log_error(
				title=f"[seal_hrms] bulk nudge failed for {member_name}",
				message=frappe.get_traceback(),
			)
			skipped += 1
			reason_skipped["error"] = reason_skipped.get("error", 0) + 1

	return {"nudged": nudged, "throttled": throttled, "skipped": skipped, "reason_skipped": reason_skipped}


def _require_hr_role():
	if frappe.session.user == "Administrator":
		return
	if not (set(frappe.get_roles(frappe.session.user)) & HR_BACKOFFICE_ROLES):
		frappe.throw(_("Only HR User or HR Manager can perform bulk planning actions."))
