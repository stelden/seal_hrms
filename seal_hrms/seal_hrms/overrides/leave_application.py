# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Leave Application overrides — gate Leave Application against Leave Plan slots
for plannable leave types, and own the booking lifecycle.

Per SPEC §8.2-§8.4: validate finds a matching slot before allowing save;
on_submit creates a booking via the §3.3 pessimistic-lock endpoint;
on_cancel cancels the booking idempotently.
"""

import frappe
from frappe import _
from frappe.utils import getdate, time_diff_in_hours

from seal_hrms.seal_hrms.leave_planning.endpoints.booking import (
	cancel_booking_for_la,
	create_booking_for_la,
	find_matching_slot,
)


def validate(doc, method=None):
	leave_type = frappe.get_cached_doc("Leave Type", doc.leave_type)

	_check_application_timing(doc, leave_type)

	if not leave_type.get("custom_is_plannable"):
		return

	result = find_matching_slot(doc.employee, doc.leave_type, doc.from_date, doc.to_date)
	if not result["plan"]:
		frappe.throw(result["reason"], title=_("Leave Plan Slot Required"))


def on_submit(doc, method=None):
	if not frappe.get_cached_value("Leave Type", doc.leave_type, "custom_is_plannable"):
		return
	create_booking_for_la(doc.name)


def on_cancel(doc, method=None):
	cancel_booking_for_la(doc.name)


def _check_application_timing(doc, leave_type) -> None:
	min_advance = int(leave_type.get("custom_min_application_advance_days") or 0)
	max_advance = int(leave_type.get("custom_max_application_advance_days") or 0)

	if min_advance > 0:
		hours_until_start = time_diff_in_hours(doc.from_date, doc.posting_date)
		if hours_until_start < (min_advance * 24):
			frappe.throw(_(
				"You cannot apply for {0} less than {1} day(s) before the start date."
			).format(doc.leave_type, min_advance))

	if max_advance > 0:
		days_until_start = (getdate(doc.from_date) - getdate(doc.posting_date)).days
		if days_until_start > max_advance:
			frappe.throw(_(
				"You cannot apply for {0} more than {1} day(s) before the start date."
			).format(doc.leave_type, max_advance))
