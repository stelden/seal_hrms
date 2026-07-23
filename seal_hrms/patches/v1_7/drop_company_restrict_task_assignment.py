# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Drop the defunct Company field `custom_restrict_task_assignment`.

It gated the Task Assignment coverage list to the absent employee's own
department. That responsibility moved to Leave Planning — cover is chosen per
slot on the Leave Plan and validated by the concurrency rules — so the flag no
longer does anything. `get_assignable_employees` has already stopped reading it.

Idempotent: the field is absent on sites that never had it (wel.local), present
on those that did (dev.local). Not shipped by any active fixture, so deleting it
here is final — nothing re-imports it.
"""

import json

import frappe

FIELD = "custom_restrict_task_assignment"
CUSTOM_FIELD = f"Company-{FIELD}"
FIELD_ORDER_PS = "Company-main-field_order"


def execute():
	if frappe.db.exists("Custom Field", CUSTOM_FIELD):
		# force=True also drops the column from `tabCompany`.
		frappe.delete_doc("Custom Field", CUSTOM_FIELD, ignore_permissions=True, force=True)
		print(f"[seal_hrms] deleted Custom Field {CUSTOM_FIELD}")
	else:
		print(f"[seal_hrms] Custom Field {CUSTOM_FIELD} absent — nothing to delete")

	# A site whose Company layout was customised carries a field_order Property
	# Setter listing every field by name. Leaving the deleted field in it is
	# harmless (Frappe ignores unknown names) but untidy, so strip it.
	if frappe.db.exists("Property Setter", FIELD_ORDER_PS):
		order = json.loads(frappe.db.get_value("Property Setter", FIELD_ORDER_PS, "value") or "[]")
		if FIELD in order:
			frappe.db.set_value(
				"Property Setter", FIELD_ORDER_PS,
				"value", json.dumps([f for f in order if f != FIELD]),
			)
			print(f"[seal_hrms] removed {FIELD} from {FIELD_ORDER_PS}")

	frappe.clear_cache(doctype="Company")
