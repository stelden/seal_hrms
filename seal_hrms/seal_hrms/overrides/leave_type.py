# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate

def validate(doc, method=None):
    """A leave type's minimum days must not exceed its maximum.

    The minimum is a custom field another app adds (seal_leave_planning, seal_customizations), so
    it is read with `get`: on a site without it, reading the attribute stopped every Leave Type
    save (found on wel.local, 2026-11-07). A maximum of 0 means no limit, as HRMS reads it.
    """
    maximum = flt(doc.max_leaves_allowed)
    if maximum and flt(doc.get("custom_min_leave_days")) > maximum:
        frappe.throw(_("Minimum Leave Days cannot be greater than Maximum Leaves Allowed"))