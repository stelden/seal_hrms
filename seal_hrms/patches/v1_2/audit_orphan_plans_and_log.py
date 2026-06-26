# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Read-only audit of Leave Plan / Booking integrity after Phase 2 migration.

	Per SEAL_DEV_RULES §3.11: anomalies are catalogued, not auto-corrected.
	The right correction may require sign-off or mask deeper integrity issues.
	The migration's job is to surface drift, not resolve it.

	Output: stdout deploy log + a single frappe.log_error with a structured title.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.8
	"""
	issues: list[str] = []

	no_cycle = frappe.db.sql(
		"""
		SELECT name FROM `tabLeave Plan`
		WHERE docstatus != 2
		  AND (planning_cycle IS NULL OR planning_cycle = '')
		"""
	)
	if no_cycle:
		issues.append(
			f"{len(no_cycle)} non-cancelled plans have no planning_cycle: "
			f"{[r[0] for r in no_cycle[:10]]}{'...' if len(no_cycle) > 10 else ''}"
		)

	orphan_bookings = frappe.db.sql(
		"""
		SELECT b.name FROM `tabLeave Plan Slot Booking` b
		LEFT JOIN `tabLeave Application` la ON la.name = b.leave_application
		WHERE b.status = 'Active' AND la.name IS NULL
		"""
	)
	if orphan_bookings:
		issues.append(f"{len(orphan_bookings)} active bookings reference a non-existent LA")

	stale_bookings = frappe.db.sql(
		"""
		SELECT b.name FROM `tabLeave Plan Slot Booking` b
		JOIN `tabLeave Application` la ON la.name = b.leave_application
		WHERE b.status = 'Active' AND la.docstatus = 2
		"""
	)
	if stale_bookings:
		issues.append(f"{len(stale_bookings)} active bookings whose LA is cancelled")

	if not issues:
		print("[seal_hrms.v1_2] audit clean — no anomalies")
		return

	msg = "\n".join(f"  - {i}" for i in issues)
	print(f"[seal_hrms.v1_2] AUDIT FOUND ANOMALIES:\n{msg}")
	frappe.log_error(
		title="[seal_hrms.v1_2] Leave Planning audit anomalies",
		message=msg,
	)
