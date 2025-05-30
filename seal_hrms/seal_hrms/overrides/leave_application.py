# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, cint, flt, time_diff_in_hours


def validate(doc, method=None):
	"""Hook for Leave Application: validate"""
	notice_period = frappe.get_value(
        "Leave Type", doc.leave_type, "custom_min_leave_application_days_in_advance"
    )
	if notice_period:
		if time_diff_in_hours(doc.from_date, doc.posting_date) < (notice_period * 24):
			frappe.throw(_(f"You cannot apply for <b>{doc.leave_type}</b> less than <b>{notice_period}</b> days before the start date."))

	settings = frappe.get_cached_doc("SEAL HRMS Settings")
	if not settings.enable_leave_planning: return

	matching_slot_info = _find_matching_plan_slot(doc)
	if not matching_slot_info:
		approved_plan_exists = frappe.db.exists("Leave Plan", {"employee": doc.employee, "docstatus": 1})
		if not approved_plan_exists:
			frappe.throw(frappe._("Leave Planning is enabled. You must have a Submitted Leave Plan."), title=frappe._("Submitted Leave Plan Required"))
		else:
			frappe.throw(frappe._("This Leave Application does not match any 'Open' slot in your Submitted Leave Plan(s)."), title=frappe._("No Matching Leave Plan Slot"))

def on_submit(doc, method=None):
	"""Hook for Leave Application: on_submit"""
	settings = frappe.get_cached_doc("SEAL HRMS Settings")
	if not settings.enable_leave_planning: return

	matching_slot_info = _find_matching_plan_slot(doc)
	if not matching_slot_info:
		frappe.log_error(f"Leave Application {doc.name}: Could not find matching Leave Plan slot on submit.", "Leave Plan Link Error")
		return

	try:
		frappe.db.set_value("Leave Plan Slot", matching_slot_info.leave_plan_slot_name, {
			"slot_status": "Applied",
			"leave_application": doc.name
		})
		
		leave_plan_doc = frappe.get_doc("Leave Plan", matching_slot_info.leave_plan_name)
		leave_plan_doc.update_status() # Call the plan's own status update method
		leave_plan_doc.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Leave Application {doc.name}: Failed to update Leave Plan {matching_slot_info.leave_plan_name}. Error: {e}", "Leave Plan Update Error")

def on_cancel(doc, method=None):
	"""Hook for Leave Application: on_cancel"""
	settings = frappe.get_cached_doc("SEAL HRMS Settings")
	if not settings.enable_leave_planning: return

	linked_slot_info = frappe.db.sql("""
		SELECT lps.parent as leave_plan_name, lps.name as leave_plan_slot_name
		FROM `tabLeave Plan Slot` AS lps WHERE lps.leave_application = %(la_name)s LIMIT 1
	""", {"la_name": doc.name}, as_dict=True)

	if linked_slot_info:
		info = linked_slot_info[0]
		try:
			if frappe.db.get_value("Leave Plan", info.leave_plan_name, "docstatus") == 1:
				frappe.db.set_value("Leave Plan Slot", info.leave_plan_slot_name, {"slot_status": "Open", "leave_application": None})
				leave_plan_doc = frappe.get_doc("Leave Plan", info.leave_plan_name)
				leave_plan_doc.update_status()
				leave_plan_doc.save(ignore_permissions=True)
				frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Leave Application {doc.name}: Failed to revert Leave Plan {info.leave_plan_name} on cancel. Error: {e}", "Leave Plan Revert Error")

# --- HELPER FUNCTION ---

def _find_matching_plan_slot(la_doc):
	"""Finds a submitted, open Leave Plan slot that matches the Leave Application."""
	return frappe.db.sql("""
		SELECT lp.name as leave_plan_name, lps.name as leave_plan_slot_name
		FROM `tabLeave Plan Slot` AS lps JOIN `tabLeave Plan` AS lp ON lps.parent = lp.name
		WHERE
			lp.employee = %(employee)s
			AND lp.docstatus = 1  -- The plan must be submitted
			AND lps.leave_type = %(leave_type)s
			AND lps.from_date = %(from_date)s
			AND lps.to_date = %(to_date)s
			AND lps.slot_status = 'Open'
		LIMIT 1
	""", {
		"employee": la_doc.employee, "leave_type": la_doc.leave_type,
		"from_date": la_doc.from_date, "to_date": la_doc.to_date
	}, as_dict=True)[0] if frappe.db.exists("DocType", "Leave Plan") else None