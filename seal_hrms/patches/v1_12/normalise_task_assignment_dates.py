# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Clear Task Assignment leave dates that are not dates, before they become Date columns.

`leave_from`, `leave_to` and `leave_days` were Read Only text copied from the
Leave Application. 1.4.0 makes them Date/Float so the scheduler can compare them
as dates. MariaDB refuses to convert a column holding a value it cannot read as
a date, which would stop migrate on that site. A blank here re-fetches from the
Leave Application the next time the record is saved; nothing is guessed.

Runs before model sync, so it sees the old text columns. A no-op where every
value is already a proper date, which on the MHC restore is all 40 records.
"""

import frappe


def execute():
	if not frappe.db.table_exists("Task Assignment"):
		return
	columns = {c.lower() for c in frappe.db.get_table_columns("Task Assignment")}
	for field in ("leave_from", "leave_to"):
		if field not in columns:
			continue
		frappe.db.sql(
			f"""UPDATE `tabTask Assignment` SET `{field}` = NULL
			WHERE `{field}` IS NOT NULL AND `{field}` NOT REGEXP '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$'"""
		)
	if "leave_days" in columns:
		frappe.db.sql(
			"""UPDATE `tabTask Assignment` SET leave_days = NULL
			WHERE leave_days IS NOT NULL AND leave_days NOT REGEXP '^-?[0-9]+(\\\\.[0-9]+)?$'"""
		)
	print("[task-assignment] leave dates checked before becoming Date columns")
