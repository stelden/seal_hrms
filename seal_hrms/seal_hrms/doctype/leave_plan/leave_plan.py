# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, date_diff, nowdate, add_days, cint, flt, cstr
from datetime import datetime, date
import calendar

# Provided Utilities
from hrms.hr.utils import (
	get_holiday_dates_for_employee, # Returns list of stringified dates
	validate_active_employee,
)
from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates # Returns list of dicts
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on # Returns float or dict

class LeavePlan(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_leave_period()
		self.recalculate_and_validate_slots()
		self.validate_submission_rules()

	def before_submit(self):
		self.validate_leave_allocations() # Now uses get_leave_balance_on
		self.validate_one_slot_min_days_rule_for_all_types()
		self.validate_leave_block_list_for_all_slots() # Updated with utility's return type
		self.validate_concurrency_overlap() # Updated for Employee Group and direct self.department/branch

	def on_submit(self):
		self.db_set("status", "Not Applied")

	def validate_leave_period(self):
		if not self.leave_period:
			frappe.throw(_("Leave Period is mandatory."))
		if not frappe.db.exists("Leave Period", self.leave_period):
			frappe.throw(_("Leave Period {0} does not exist.").format(self.leave_period))

	def update_status(self):
		"""Recalculates the plan's 'status' field based on its child slots."""
		if self.docstatus != 1: return

		open_slots, applied_slots = False, False
		if not self.get("leave_plan_slots"):
			if self.status != 'Not Applied': self.db_set('status', 'Not Applied')
			return

		for slot in self.get("leave_plan_slots"):
			if slot.slot_status == 'Open': open_slots = True
			elif slot.slot_status == 'Applied': applied_slots = True
		
		new_status = self.status
		if applied_slots and not open_slots: new_status = 'Fully Applied'
		elif applied_slots and open_slots: new_status = 'Partially Applied'
		elif not applied_slots and open_slots: new_status = 'Not Applied'
		
		if self.status != new_status:
			self.db_set('status', new_status)

	def recalculate_and_validate_slots(self):
		if not self.get("leave_plan_slots"):
			frappe.throw(_("At least one Leave Plan Slot is required."))

		slot_leave_types_processed = {}
		leave_period_doc = frappe.get_doc("Leave Period", self.leave_period)

		for i, slot in enumerate(self.get("leave_plan_slots")):
			row_num = i + 1
			self._validate_slot_mandatory_fields(slot, row_num)
			self._validate_slot_dates_order_and_period(slot, row_num, leave_period_doc)

			slot.days = self.calculate_leave_days(slot.from_date, slot.to_date, self.employee)
			if slot.days <= 0:
				frappe.throw(_("Row #{0}: Calculated leave days must be > 0 for {1} to {2}.").format(row_num, slot.from_date, slot.to_date))

			self._validate_slot_leave_type_rules(slot, row_num, slot_leave_types_processed)
			self._validate_internal_slot_overlap(i, slot, row_num)

	def _validate_slot_mandatory_fields(self, slot, row_num):
		if not slot.leave_type: frappe.throw(_("Row #{0}: Leave Type is mandatory.").format(row_num))
		if not slot.from_date: frappe.throw(_("Row #{0}: From Date is mandatory.").format(row_num))
		if not slot.to_date: frappe.throw(_("Row #{0}: To Date is mandatory.").format(row_num))

	def _validate_slot_dates_order_and_period(self, slot, row_num, leave_period_doc):
		if getdate(slot.from_date) > getdate(slot.to_date):
			frappe.throw(_("Row #{0}: From Date ({1}) after To Date ({2}).").format(row_num, slot.from_date, slot.to_date))
		if getdate(slot.from_date) < getdate(leave_period_doc.from_date) or \
		   getdate(slot.to_date) > getdate(leave_period_doc.to_date):
			frappe.throw(_("Row #{0}: Slot ({1} to {2}) outside Leave Period ({3} to {4}).")
						 .format(row_num, slot.from_date, slot.to_date, leave_period_doc.from_date, leave_period_doc.to_date))

	def _validate_slot_leave_type_rules(self, slot, row_num, slot_leave_types_processed):
		lt_doc = frappe.get_doc("Leave Type", slot.leave_type)
		if not lt_doc.custom_is_plannable:
			frappe.throw(_("Row #{0}: Leave Type {1} not plannable.").format(row_num, slot.leave_type))

		min_days_slot = cint(lt_doc.custom_min_days_per_planning_slot)
		if min_days_slot > 0 and slot.days < min_days_slot:
			frappe.throw(_("Row #{0}: Min days for {1} slot is {2}. Planned: {3}.").format(row_num, slot.leave_type, min_days_slot, slot.days))

		if not lt_doc.custom_allow_multiple_slots_in_plan:
			if slot.leave_type in slot_leave_types_processed:
				frappe.throw(_("{0} doesn't allow multiple slots. Used in Row #{1}.").format(slot.leave_type, slot_leave_types_processed[slot.leave_type]))
			slot_leave_types_processed[slot.leave_type] = row_num

	def _validate_internal_slot_overlap(self, current_idx, current_slot, current_row_num):
		for j, other_slot in enumerate(self.get("leave_plan_slots")):
			if current_idx == j: continue
			if current_slot.leave_type == other_slot.leave_type and \
			   max(getdate(current_slot.from_date), getdate(other_slot.from_date)) <= min(getdate(current_slot.to_date), getdate(other_slot.to_date)):
				frappe.throw(_("Row #{0} overlaps Row #{1} for {2}.").format(current_row_num, j + 1, current_slot.leave_type))

	def validate_submission_rules(self):
		settings = frappe.get_cached_doc("SEAL HRMS Settings")
		if not settings.enable_leave_planning:
			frappe.throw(_("Leave Planning disabled in SEAL HRMS Settings."))

		if not self.get("leave_plan_slots"): return
		today = getdate(nowdate())
		earliest_slot_from_date = min(getdate(s.from_date) for s in self.get("leave_plan_slots") if s.from_date)
		if not earliest_slot_from_date: frappe.throw(_("Cannot determine earliest slot date."))

		if settings.planning_submission_timing_method == 'Lead Days Before Slot':
			lead_days = cint(settings.planning_submission_lead_days)
			deadline = add_days(earliest_slot_from_date, -lead_days)
			if today > deadline:
				frappe.throw(_("Plan due by {0} ({1} days before {2}).").format(deadline.strftime('%Y-%m-%d'), lead_days, earliest_slot_from_date.strftime('%Y-%m-%d')))
		elif settings.planning_submission_timing_method == 'Fixed Deadline for Period':
			year = getdate(frappe.get_value("Leave Period", self.leave_period, "from_date")).year
			month_map = {name: num for num, name in enumerate(calendar.month_name) if num}
			try:
				if not settings.planning_submission_deadline_month or not settings.planning_submission_deadline_day:
					frappe.throw(_("Fixed deadline month/day not set in SEAL HRMS Settings."))
				month_num = month_map[settings.planning_submission_deadline_month]
				deadline = datetime(year, month_num, cint(settings.planning_submission_deadline_day)).date()
			except (ValueError, KeyError) as e:
				frappe.throw(_("Invalid fixed deadline in Settings: {0}-{1}. Error: {2}").format(
					settings.planning_submission_deadline_day, settings.planning_submission_deadline_month, e))
			if today > deadline:
				frappe.throw(_("Submission deadline for period {0} was {1}.").format(self.leave_period, deadline.strftime('%Y-%m-%d')))

		if cint(settings.planning_submission_max_future_days) > 0:
			max_date = add_days(today, cint(settings.planning_submission_max_future_days))
			for slot in self.get("leave_plan_slots"):
				if slot.from_date and getdate(slot.from_date) > max_date:
					frappe.throw(_("Slot from {0} exceeds max future planning of {1} days.").format(slot.from_date, settings.planning_submission_max_future_days))

	def validate_leave_allocations(self):
		planned_days_by_type = {}
		# Find the latest date mentioned in the plan for each leave type
		# This will be used as the 'as_of_date' for balance checking.
		# Alternatively, use the leave period's end date.
		leave_period_end_date = getdate(frappe.get_value("Leave Period", self.leave_period, "to_date"))

		for slot in self.get("leave_plan_slots"):
			if slot.leave_type and slot.days:
				planned_days_by_type[slot.leave_type] = planned_days_by_type.get(slot.leave_type, 0) + flt(slot.days)

		for leave_type, total_planned in planned_days_by_type.items():
			# Get balance as of the end of the leave period to see total available for planning.
			# `consider_all_leaves_in_the_allocation_period=True` effectively does this too.
			# `for_consumption=False` to get the theoretical balance.
			available_balance = get_leave_balance_on(
				employee=self.employee,
				leave_type=leave_type,
				date=leave_period_end_date, # Check balance as of end of period
				consider_all_leaves_in_the_allocation_period=True,
				for_consumption=False # Get raw balance, not "consumable today"
			)
			
			if available_balance is None: # Should not happen if allocations exist
				frappe.throw(_("Could not retrieve leave balance for {0}, Type {1}.").format(self.employee, leave_type))

			if total_planned > flt(available_balance):
				frappe.throw(_("Planned {0} days for {1} exceed available balance of {2} for the period.")
							 .format(total_planned, leave_type, available_balance))

	def validate_one_slot_min_days_rule_for_all_types(self):
		slots_by_type = {}
		for slot in self.get("leave_plan_slots"):
			if slot.leave_type and slot.days:
				slots_by_type.setdefault(slot.leave_type, []).append(flt(slot.days))

		for lt_name, slot_days_list in slots_by_type.items():
			lt_doc = frappe.get_doc("Leave Type", lt_name)
			min_duration = cint(lt_doc.custom_require_one_slot_min_days)
			if min_duration > 0 and not any(p_days >= min_duration for p_days in slot_days_list):
				frappe.throw(_("For {0}, one slot must be >= {1} day(s).").format(lt_name, min_duration))

	def validate_leave_block_list_for_all_slots(self):
		for slot in self.get("leave_plan_slots"):
			if not slot.from_date or not slot.to_date: continue
			try:
				# get_applicable_block_dates returns list of dicts: [{"block_date": date, "reason": str}, ...]
				blocked_dates_info = get_applicable_block_dates(
					from_date=slot.from_date, to_date=slot.to_date, 
					employee=self.employee, leave_type=slot.leave_type
					# company=self.company might also be needed if utility uses it.
				)
				if blocked_dates_info: 
					reasons = list(set(d.get("reason") for d in blocked_dates_info if d.get("reason")))
					reason_str = (": " + ", ".join(reasons)) if reasons else ""
					frappe.throw(_("Slot from {0} to {1} for {2} is blocked{3}")
								 .format(slot.from_date, slot.to_date, slot.leave_type, reason_str))
			except Exception as e: # Catch other errors from utility
				frappe.log_error(f"Error checking block list for slot {slot.from_date}-{slot.to_date}: {e}")
				frappe.throw(_("Could not verify leave block list for slot {0}-{1} due to: {2}").format(slot.from_date, slot.to_date, e))


	def validate_concurrency_overlap(self):
		settings = frappe.get_cached_doc("SEAL HRMS Settings")
		if not settings.enable_leave_planning or settings.planning_overlap_scope == 'None': return

		for cur_slot in self.get("leave_plan_slots"):
			if not cur_slot.from_date or not cur_slot.to_date: continue
			s_from, s_to = getdate(cur_slot.from_date), getdate(cur_slot.to_date)

			query_base = """SELECT lp.employee FROM `tabLeave Plan Slot` AS lps
						JOIN `tabLeave Plan` AS lp ON lps.parent = lp.name
						WHERE lp.docstatus = 1
						AND lp.name != %(current_plan_name)s
						AND %(slot_from_date)s <= lps.to_date AND %(slot_to_date)s >= lps.from_date"""
			
			q_filters = {"current_plan_name": self.name, "slot_from_date": s_from, "slot_to_date": s_to}
			
			scope_clauses = []
			employees_in_scope_for_check = None # List of employees for Employee Group scope

			if settings.planning_overlap_scope == 'Department':
				if not self.department: continue 
				scope_clauses.append("lp.department = %(department)s")
				q_filters["department"] = self.department
			elif settings.planning_overlap_scope == 'Branch':
				if not self.branch: continue 
				scope_clauses.append("lp.branch = %(branch)s")
				q_filters["branch"] = self.branch
			elif settings.planning_overlap_scope == 'Employee Group':
				employee_groups = frappe.get_all("Employee Group Table",
												 filters={"employee": self.employee},
												 fields=["parent"], pluck="parent", distinct=True)
				if not employee_groups: continue # No group, so no restriction from this scope type
				
				employees_in_scope_for_check = frappe.get_all("Employee Group Table",
															filters={"parent": ["in", employee_groups]},
															fields=["employee"], pluck="employee", distinct=True)
				if not employees_in_scope_for_check: continue

				# Remove current employee if present in the list for checking others' plans
				if self.employee in employees_in_scope_for_check:
					employees_in_scope_for_check.remove(self.employee)
				
				if not employees_in_scope_for_check: continue # No other employees in group

				scope_clauses.append("lp.employee IN %(group_employees)s")
				q_filters["group_employees"] = tuple(employees_in_scope_for_check)


			if scope_clauses: query = query_base + " AND " + " AND ".join(scope_clauses)
			else: query = query_base # Company Wide if no specific scope matched or if scope had no criteria
			
			overlapping_emps = {r[0] for r in frappe.db.sql(query, q_filters)}
			max_allowed = self._get_max_allowed_concurrent(settings, employees_in_scope_for_check)

			if (len(overlapping_emps) + 1) > max_allowed:
				frappe.throw(_("Slot ({0} to {1}) conflicts in {2}. Others: {3}. Max (incl. this): {4}.")
					.format(s_from.strftime('%Y-%m-%d'), s_to.strftime('%Y-%m-%d'), settings.planning_overlap_scope,
							len(overlapping_emps), cint(max_allowed)))

	def _get_max_allowed_concurrent(self, settings, group_employees_list=None):
		total_emps_in_scope = 0
		scope_filter = {'status': 'Active'}

		if settings.planning_overlap_scope == 'Department' and self.department:
			scope_filter['department'] = self.department
			total_emps_in_scope = frappe.db.count('Employee', scope_filter)
		elif settings.planning_overlap_scope == 'Branch' and self.branch:
			scope_filter['branch'] = self.branch
			total_emps_in_scope = frappe.db.count('Employee', scope_filter)
		elif settings.planning_overlap_scope == 'Employee Group':
			if group_employees_list is not None:
				# Count active employees within the provided list
				active_group_employees = frappe.get_all("Employee",
				                                        filters={"name": ["in", group_employees_list], "status": "Active"},
				                                        pluck="name", distinct=True)
				total_emps_in_scope = len(set(active_group_employees + [self.employee])) # Include current employee for total scope size
			else: # Should not happen if group_employees_list is passed correctly
				total_emps_in_scope = 0
		elif settings.planning_overlap_scope == 'Company':
			total_emps_in_scope = frappe.db.count('Employee', scope_filter)
		
		if total_emps_in_scope == 0 and settings.planning_overlap_scope != 'Company':
			return float('inf') 

		abs_max = cint(settings.max_concurrent_planned_leaves_absolute)
		perc_max_calculated = 0
		if flt(settings.max_concurrent_planned_leaves_percentage) > 0 and total_emps_in_scope > 0:
			perc_val = (flt(settings.max_concurrent_planned_leaves_percentage) / 100.0) * total_emps_in_scope
			perc_max_calculated = cint(perc_val) if perc_val >= 1.0 else 1 # At least 1 if percentage is positive and yields a fraction > 0
		
		if abs_max > 0 and perc_max_calculated > 0: max_allowed = min(abs_max, perc_max_calculated)
		elif abs_max > 0: max_allowed = abs_max
		elif perc_max_calculated > 0: max_allowed = perc_max_calculated
		else: max_allowed = total_emps_in_scope if total_emps_in_scope > 0 else float('inf') 

		return max_allowed

	def calculate_leave_days(self, from_date_str, to_date_str, employee_id):
		if not from_date_str or not to_date_str or not employee_id: return 0
		start_date, end_date = getdate(from_date_str), getdate(to_date_str)
		
		try: 
			# get_holiday_dates_for_employee returns list of stringified dates
			holiday_date_strings = get_holiday_dates_for_employee(employee_id, start_date, end_date)
			holidays = {getdate(hd_str) for hd_str in holiday_date_strings} # Convert to date objects
		except Exception as e:
			frappe.log_error(f"Error fetching holidays for {employee_id}: {e}")
			holidays = set()

		emp_holiday_list = frappe.db.get_value("Employee", employee_id, "holiday_list") \
			or frappe.db.get_value("Company", frappe.db.get_value("Employee", employee_id, "company"), "default_holiday_list")
		
		weekly_off = frappe.db.get_value("Holiday List", emp_holiday_list, "weekly_off") if emp_holiday_list else None
		
		days_count = 0
		curr_date = start_date
		while curr_date <= end_date:
			is_weekly_off = weekly_off and curr_date.strftime("%A") == weekly_off
			is_holiday = curr_date in holidays
			
			if not is_weekly_off and not is_holiday:
				days_count += 1
			curr_date = add_days(curr_date, 1)
		return days_count