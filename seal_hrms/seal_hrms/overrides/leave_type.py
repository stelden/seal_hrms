import frappe
from frappe import _ 
from frappe.model.document import Document
from frappe.utils import cint, flt # cint for integers, flt for floats if max_leaves_allowed can be float

def validate(doc, method=None):
    leave_cycle = frappe.db.get_single_value("SEAL HRMS Settings", "planning_submission_max_future_days")
    min_application_advance_days = cint(doc.custom_min_leave_application_days_in_advance)
    leave_type_max_days_allowed = cint(doc.max_leaves_allowed)

    if leave_cycle > 0 and min_application_advance_days > 0:
        if (min_application_advance_days + leave_type_max_days_allowed) > leave_cycle:
            frappe.throw(_("Minimum Leave Application Notice Days must be within the Leave Cycle of {0} days.")
                .format(leave_cycle)
            )
        
    # These validations apply if the leave type is marked as plannable
    if doc.custom_is_plannable:
        if doc.custom_require_one_slot_min_days and doc.custom_require_one_slot_min_days > doc.max_leaves_allowed:
            frappe.throw(_("Minimum slot days cannot exceed maximum allowed leaves."))