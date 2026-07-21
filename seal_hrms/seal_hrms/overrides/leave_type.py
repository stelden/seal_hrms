# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate

def validate(doc, method=None):
    # ensure custom_min_leave_days <= max_leaves_allowed (guard None -> 0)
    if flt(doc.custom_min_leave_days) > flt(doc.max_leaves_allowed):
        frappe.throw(_("Minimum Leave Days cannot be greater than Maximum Leaves Allowed"))