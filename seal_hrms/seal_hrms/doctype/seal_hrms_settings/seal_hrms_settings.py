# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, datetime
import calendar

class SEALHRMSSettings(Document):
	def validate(self):
		self.validate_concurrency_settings()
		self.validate_submission_rules()
		self.validate_other_numeric_fields()

	def validate_concurrency_settings(self):
		if flt(self.max_concurrent_planned_leaves_percentage) < 0 or flt(self.max_concurrent_planned_leaves_percentage) > 100:
			frappe.throw(frappe._("Max Concurrent Leaves Percentage must be between 0 and 100."))
		
		if cint(self.max_concurrent_planned_leaves_absolute) < 0:
			frappe.throw(frappe._("Max Concurrent Leaves Absolute must be a non-negative integer."))
		
		if self.planning_overlap_scope != 'None' and flt(self.max_concurrent_planned_leaves_percentage) == 0 and cint(self.max_concurrent_planned_leaves_absolute) == 0:
			frappe.msgprint(
				frappe._("Concurrency limits are not set. No numeric limit will be applied to overlaps."),
				title=frappe._("Concurrency Limit Notice"), indicator="orange"
			)

	def validate_submission_rules(self):
		if self.planning_submission_timing_method == 'Lead Days Before Slot':
			if self.planning_submission_lead_days is None:
				frappe.throw(frappe._("Submission Lead Days is required for the selected timing method."))
			if cint(self.planning_submission_lead_days) < 0:
				frappe.throw(frappe._("Submission Lead Days must be a non-negative integer."))
		
		elif self.planning_submission_timing_method == 'Fixed Deadline for Period':
			if not self.planning_submission_deadline_month or not self.planning_submission_deadline_day:
				frappe.throw(frappe._("Deadline Day and Month are required for the selected timing method."))
			# As per your request, since UI limits day to 28, no further day/month validation is needed here.

	def validate_other_numeric_fields(self):
		if self.get("planning_submission_max_future_days") and cint(self.planning_submission_max_future_days) < 0:
			frappe.throw(frappe._("Max Future Planning Days must be a non-negative integer."))
			
		if cint(self.auto_create_leave_application_reminder_days) < 0:
			frappe.throw(frappe._("Leave Application Reminder Days must be a non-negative integer."))
