# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate(doc, method=None):
	if not doc.custom_is_plannable:
		return

	min_days = int(doc.get("custom_min_days_per_slot") or 0)
	max_days = int(doc.get("custom_max_days_per_slot") or 0)
	max_allowed = int(doc.get("max_leaves_allowed") or 0)

	if min_days and max_allowed and min_days > max_allowed:
		frappe.throw(_(
			"Minimum days per slot ({0}) cannot exceed Maximum Leaves Allowed ({1})."
		).format(min_days, max_allowed))

	if min_days and max_days and min_days > max_days:
		frappe.throw(_(
			"Minimum days per slot ({0}) cannot exceed Maximum days per slot ({1})."
		).format(min_days, max_days))
