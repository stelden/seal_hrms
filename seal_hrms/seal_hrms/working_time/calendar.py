# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What kind of day a date was for a member of staff: working day, rest day or public holiday.

Read from the person's holiday list, as Frappe HR's overtime does
(`overtime_slip.py`): a holiday row marked as a weekly off is a rest day; any
other holiday row is a public holiday, and wins if a date has both.
"""

import frappe
from frappe import _
from frappe.utils import getdate
from hrms.utils.holiday_list import get_holiday_dates_between_range, get_holiday_list_ranges_for_employee

from seal_hrms.seal_hrms.toil.days import PUBLIC, REST, WORKING


def day_kinds(employee: str, dates) -> dict:
	"""{date: kind} for each of `dates`."""
	dates = sorted({getdate(d) for d in dates if d})
	if not dates:
		return {}
	start, end = dates[0], dates[-1]
	if not get_holiday_list_ranges_for_employee(employee, start, end, raise_exception=False):
		frappe.throw(
			_(
				"{0} has no holiday list, so rest days and public holidays cannot be told apart. "
				"Ask HR to assign one."
			).format(frappe.db.get_value("Employee", employee, "employee_name") or employee),
			title=_("No Holiday List"),
		)
	public, rest = set(), set()
	for row in get_holiday_dates_between_range(employee, start, end, as_dict=True):
		(rest if row.get("weekly_off") else public).add(getdate(row.holiday_date))
	return {d: PUBLIC if d in public else REST if d in rest else WORKING for d in dates}
