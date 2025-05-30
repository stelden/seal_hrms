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
        validate_planning_slot_days_against_max_allowed(doc)

def validate_planning_slot_days_against_max_allowed(doc):
		"""
		Validates that planning rules do not exceed the max_leaves_allowed for the leave type.
		"""
		max_allowed = cint(doc.max_leaves_allowed) # Assuming max_leaves_allowed can be 0 or positive

		# 1. Check custom_min_days_per_planning_slot
		min_days_slot = cint(doc.custom_min_days_per_planning_slot)
		if min_days_slot > 0 and max_allowed > 0 and min_days_slot > max_allowed:
			frappe.throw(_("Minimum Days Per Planning Slot ({0}) cannot exceed Max Leaves Allowed ({1}).")
				.format(min_days_slot, max_allowed)
			)

		# 2. Check custom_require_one_slot_min_days
		require_one_min_days = cint(doc.custom_require_one_slot_min_days)
		if require_one_min_days > 0 and max_allowed > 0 and require_one_min_days > max_allowed:
			frappe.throw(_("Duration for 'Require One Slot Min Days' ({0}) cannot exceed Max Leaves Allowed ({1}).")
				.format(require_one_min_days, max_allowed)
			)