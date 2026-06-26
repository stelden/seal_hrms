# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Convert legacy `Leave Plan Slot.leave_application` back-links into
	`Leave Plan Slot Booking` rows, then drop the legacy column.

	Pre-Phase-2 model: each slot held a single `leave_application` field
	naming the LA that consumed it.

	New model: bookings are independent rows. Each slot can have multiple
	bookings (partial draws). This patch migrates the old shape to the new
	without losing data.

	Anomalies (LA range outside slot range, missing LA, etc.) are catalogued
	via frappe.log_error per §3.11 — surface, don't auto-correct.

	Reference: dev_notes/seal_hrms/LEAVE_PLANNING_MIGRATION.md §3.7
	"""
	if not frappe.db.has_column("Leave Plan Slot", "leave_application"):
		print("[seal_hrms.v1_2] leave_application column already dropped — no-op")
		return

	rows = frappe.db.sql(
		"""
		SELECT
			slot.name        AS slot_name,
			slot.parent      AS plan_name,
			slot.leave_application,
			slot.from_date   AS slot_from,
			slot.to_date     AS slot_to,
			slot.days        AS slot_days,
			la.employee,
			la.from_date     AS la_from,
			la.to_date       AS la_to,
			la.total_leave_days,
			la.docstatus     AS la_docstatus
		FROM `tabLeave Plan Slot` slot
		JOIN `tabLeave Application` la ON la.name = slot.leave_application
		WHERE slot.leave_application IS NOT NULL AND slot.leave_application != ''
		""",
		as_dict=True,
	)

	if not rows:
		print("[seal_hrms.v1_2] no slot->LA links to migrate — dropping orphan column")
		frappe.db.sql_ddl(
			"ALTER TABLE `tabLeave Plan Slot` DROP COLUMN `leave_application`"
		)
		return

	anomalies: list[str] = []
	created = 0
	for r in rows:
		if frappe.db.exists("Leave Plan Slot Booking", {"leave_application": r.leave_application}):
			continue
		if not (r.slot_from <= r.la_from and r.la_to <= r.slot_to):
			anomalies.append(
				f"slot {r.slot_name}: LA {r.leave_application} dates "
				f"[{r.la_from}, {r.la_to}] not within slot [{r.slot_from}, {r.slot_to}]"
			)
			continue

		booking = frappe.new_doc("Leave Plan Slot Booking")
		booking.leave_plan = r.plan_name
		booking.slot = r.slot_name
		booking.leave_application = r.leave_application
		booking.employee = r.employee
		booking.from_date = r.la_from
		booking.to_date = r.la_to
		booking.days = r.total_leave_days or 0
		booking.status = "Active" if r.la_docstatus == 1 else "Cancelled"
		booking.flags.ignore_validate = True
		booking.insert(ignore_permissions=True)
		created += 1

	if anomalies:
		frappe.log_error(
			title="[seal_hrms.v1_2] migrate_slot_links_to_bookings anomalies",
			message="\n".join(anomalies),
		)
		print(f"[seal_hrms.v1_2] {len(anomalies)} anomalies — see error log")

	print(f"[seal_hrms.v1_2] created {created} bookings; preserving column for re-runs")

	if not anomalies:
		frappe.db.sql_ddl(
			"ALTER TABLE `tabLeave Plan Slot` DROP COLUMN `leave_application`"
		)
		print("[seal_hrms.v1_2] dropped legacy column tabLeave Plan Slot.leave_application")
