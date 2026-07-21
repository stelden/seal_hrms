# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Drop the leave-planning fields stranded on SEAL HRMS Settings.

These nine were superseded when planning config moved to Leave Planning Cycle
and Leave Concurrency Rule, and were never removed. Leave planning has since
left this app entirely, so nothing can read them — but a Single keeps its
values as rows in `tabSingles`, so removing the fields from the DocType leaves
the rows behind looking like live config.

Read directly from `tabSingles` rather than via get_single_value: the fields
are gone from the DocType by the time this runs (see SEAL_DEV_RULES §2.x on
post_model_sync patches reading Singles).
"""

import frappe

DEAD_FIELDS = (
	"planning_overlap_scope",
	"leave_plan_concurrency_based_on",
	"max_concurrent_planned_leaves_percentage",
	"max_concurrent_planned_leaves_absolute",
	"planning_submission_timing_method",
	"planning_submission_lead_days",
	"planning_submission_deadline_month",
	"planning_submission_deadline_day",
	"auto_create_leave_application_reminder_days",
)


def execute():
	rows = frappe.db.sql(
		"""
		SELECT field, value FROM `tabSingles`
		WHERE doctype = 'SEAL HRMS Settings' AND field IN %(fields)s
		""",
		{"fields": DEAD_FIELDS},
		as_dict=True,
	)
	if not rows:
		print("[seal_hrms.v1_5] no stranded leave-planning settings — no-op")
		return

	# Report before deleting: if anyone had configured these, that intent is
	# worth surfacing rather than silently discarding.
	configured = [r for r in rows if r.value not in (None, "", "0")]
	if configured:
		print(
			"[seal_hrms.v1_5] discarding %d configured value(s) superseded by "
			"Leave Planning Cycle / Leave Concurrency Rule: %s"
			% (len(configured), ", ".join(f"{r.field}={r.value}" for r in configured))
		)

	frappe.db.sql(
		"""
		DELETE FROM `tabSingles`
		WHERE doctype = 'SEAL HRMS Settings' AND field IN %(fields)s
		""",
		{"fields": DEAD_FIELDS},
	)
	print(f"[seal_hrms.v1_5] dropped {len(rows)} stranded setting row(s)")
