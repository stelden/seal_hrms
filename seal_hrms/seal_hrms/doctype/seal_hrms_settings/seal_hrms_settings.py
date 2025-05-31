# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint

class SEALHRMSSettings(Document):
	def validate(self):
		if not self.enable_leave_planning:
			return  # Skip validation if planning is off

		self.validate_concurrency_settings()
		self.validate_submission_timing_rules()
		self.validate_numeric_ranges()

	def validate_concurrency_settings(self):
		if self.planning_overlap_scope != "None":
			method = self.leave_plan_concurrency_based_on

			if method == "Percentage":
				if flt(self.max_concurrent_planned_leaves_percentage) <= 0:
					frappe.throw("Max concurrent planned leaves percentage must be greater than 0.")
			elif method == "Absolute":
				if cint(self.max_concurrent_planned_leaves_absolute) <= 0:
					frappe.throw("Max concurrent planned leaves (absolute) must be greater than 0.")
			else:
				frappe.throw("Invalid concurrency method selected.")
		else:
			self.max_concurrent_planned_leaves_absolute = 0
			self.max_concurrent_planned_leaves_percentage = 0

	def validate_submission_timing_rules(self):
		method = self.planning_submission_timing_method

		if method == "Lead Days Before Slot":
			if cint(self.planning_submission_lead_days) < 0:
				frappe.throw("Planning submission lead days must be zero or positive.")
		elif method == "Fixed Deadline for Period":
			if not self.planning_submission_deadline_month or not self.planning_submission_deadline_day:
				frappe.throw("Both deadline month and day must be set for fixed deadline.")
		else:
			frappe.throw("Invalid submission timing method selected.")

	def validate_numeric_ranges(self):
		if cint(self.planning_submission_max_future_days) < 0:
			frappe.throw("Leave Planning Cycle (Days) must be ≥ 0.")

		if cint(self.auto_create_leave_application_reminder_days) < 0:
			frappe.throw("Auto Create Leave Application Reminder Days must be ≥ 0.")
