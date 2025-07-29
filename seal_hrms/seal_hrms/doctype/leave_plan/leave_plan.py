# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.utils.data import cint, flt
from hrms.hr.utils import get_holidays_for_employee
from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
import calendar

class LeavePlan(Document):

	def validate(self):
		self.validate_active_employee()
		self.validate_leave_period()
		self.recalculate_and_validate_slots()
		self.validate_submission_rules()

	def before_submit(self):
		self.validate_leave_allocations()
		self.validate_one_slot_min_days_rule_for_all_types()
		self.validate_leave_block_list_for_all_slots()
		self.validate_concurrency_overlap()

	def on_submit(self):
		self.status = "Not Applied"

	def on_cancel(self):
		self.status = "Not Applied"

	def validate_active_employee(self):
		status = frappe.db.get_value("Employee", self.employee, "status")
		if status != "Active":
			frappe.throw(_("Leave Plan can only be created for active employees."))

	def validate_leave_period(self):
		lpd = frappe.get_doc("Leave Period", self.leave_period)
		if not (lpd.start_date <= getdate(self.posting_date) <= lpd.end_date):
			frappe.throw(_("Leave Plan posting date must fall within the selected Leave Period."))

	def recalculate_and_validate_slots(self):
		for slot in self.leave_plan_slots:
			days = self.calculate_slot_days(slot.from_date, slot.to_date)
			slot.days = days

			if getdate(slot.from_date) > getdate(slot.to_date):
				frappe.throw(_("From Date cannot be after To Date for leave slot."))

	def validate_leave_allocations(self):
		for slot in self.leave_plan_slots:
			consumable_balance = get_leave_balance_on(
				employee=self.employee,
				leave_type=slot.leave_type,
				date=slot.from_date,
				to_date=slot.to_date,
				for_consumption=True
			).get("leave_balance_for_consumption", 0)

			if slot.days > consumable_balance:
				frappe.throw(_(
					f"Slot from {slot.from_date} to {slot.to_date} requires {slot.days} days, "
					f"but only {consumable_balance} days are available for {slot.leave_type}."
				))

	def validate_leave_block_list_for_all_slots(self):
		for slot in self.leave_plan_slots:
			blocked = get_applicable_block_dates(
				from_date=slot.from_date,
				to_date=slot.to_date,
				employee=self.employee,
				company=self.company,
				leave_type=slot.leave_type
			)

			if blocked:
				blocked_dates = ", ".join(str(b.block_date) for b in blocked)
				frappe.throw(_(
					f"Slot ({slot.from_date} to {slot.to_date}) overlaps with blocked leave dates: {blocked_dates}."
				))

	def validate_one_slot_min_days_rule_for_all_types(self):
		from hrms.hr.doctype.leave_type.leave_type import get_leave_type_map

		required_by_type = {}
		at_least_one_valid = {}

		for slot in self.leave_plan_slots:
			if slot.leave_type not in required_by_type:
				min_days = frappe.db.get_value("Leave Type", slot.leave_type, "custom_require_one_slot_min_days") or 0
				required_by_type[slot.leave_type] = min_days
				at_least_one_valid[slot.leave_type] = False

			if slot.days >= required_by_type[slot.leave_type]:
				at_least_one_valid[slot.leave_type] = True

		for lt, met in at_least_one_valid.items():
			if required_by_type[lt] > 0 and not met:
				frappe.throw(_(
					f"At least one slot for Leave Type {lt} must be at least {required_by_type[lt]} days long."
				))

	def validate_submission_rules(self):
		settings = frappe.get_single("SEAL HRMS Settings")
		method = settings.planning_submission_timing_method

		for slot in self.leave_plan_slots:
			slot_start = getdate(slot.from_date)
			today = getdate(self.posting_date)

			if method == "Lead Days Before Slot":
				lead = settings.planning_submission_lead_days
				if (slot_start - today).days < lead:
					frappe.throw(_(
						f"Leave slot from {slot.from_date} must be planned at least {lead} days in advance."
					))
			elif method == "Fixed Deadline for Period":
				from datetime import date
				deadline = date(today.year, frappe.utils.month_map[settings.planning_submission_deadline_month], int(settings.planning_submission_deadline_day))
				
				if today > deadline:
					frappe.throw(_("Leave Plan submission deadline has passed."))

	def validate_concurrency_overlap(self):
		settings = frappe.get_cached_doc("SEAL HRMS Settings")
		if settings.planning_overlap_scope == 'None':
			return

		for cur_slot in self.get("leave_plan_slots"):
			if not cur_slot.from_date or not cur_slot.to_date:
				continue

			s_from, s_to = getdate(cur_slot.from_date), getdate(cur_slot.to_date)

			query_base = """
				SELECT lp.employee FROM `tabLeave Plan Slot` AS lps
				JOIN `tabLeave Plan` AS lp ON lps.parent = lp.name
				WHERE lp.docstatus = 1
				AND lp.name != %(current_plan_name)s
				AND %(slot_from_date)s <= lps.to_date AND %(slot_to_date)s >= lps.from_date
			"""

			q_filters = {
				"current_plan_name": self.name,
				"slot_from_date": s_from,
				"slot_to_date": s_to
			}

			scope_clauses = []
			employees_in_scope_for_check = None

			if settings.planning_overlap_scope == 'Department' and self.department:
				scope_clauses.append("lp.department = %(department)s")
				q_filters["department"] = self.department

			elif settings.planning_overlap_scope == 'Branch' and self.branch:
				scope_clauses.append("lp.branch = %(branch)s")
				q_filters["branch"] = self.branch

			elif settings.planning_overlap_scope == 'Company' and self.company:
				scope_clauses.append("lp.company = %(company)s")
				q_filters["company"] = self.company

			elif settings.planning_overlap_scope == 'Employee Group':
				# Get current employee's groups
				employee_groups = frappe.get_all(
					"Employee Group Table",
					filters={"employee": self.employee},
					pluck="parent"
				)
				if not employee_groups:
					continue  # No groups, skip concurrency check

				employees_in_scope_for_check = frappe.get_all(
					"Employee Group Table",
					filters={"parent": ["in", employee_groups]},
					pluck="employee"
				)

				if not employees_in_scope_for_check:
					continue

				# Remove self
				employees_in_scope_for_check = list(set(employees_in_scope_for_check) - {self.employee})
				if not employees_in_scope_for_check:
					continue

				scope_clauses.append("lp.employee IN %(group_employees)s")
				q_filters["group_employees"] = tuple(employees_in_scope_for_check)

			query = query_base + (" AND " + " AND ".join(scope_clauses) if scope_clauses else "")
			overlapping_emps = {r[0] for r in frappe.db.sql(query, q_filters)}

			max_allowed = self._get_max_allowed_concurrent(settings, employees_in_scope_for_check)
			if (len(overlapping_emps) + 1) > max_allowed:
				frappe.throw(_(
					f"Slot ({s_from.strftime('%Y-%m-%d')} to {s_to.strftime('%Y-%m-%d')}) exceeds concurrency limit "
					f"in scope {settings.planning_overlap_scope}. Existing: {len(overlapping_emps)}. Limit: {max_allowed}."
				))


	def _get_max_allowed_concurrent(self, settings, group_employees_list=None):
		scope_filter = {'status': 'Active'}
		total_emps_in_scope = 0

		scope = settings.planning_overlap_scope

		if scope == 'Department' and self.department:
			scope_filter['department'] = self.department
			total_emps_in_scope = frappe.db.count("Employee", filters=scope_filter)

		elif scope == 'Branch' and self.branch:
			scope_filter['branch'] = self.branch
			total_emps_in_scope = frappe.db.count("Employee", filters=scope_filter)

		elif scope == 'Company' and self.company:
			scope_filter['company'] = self.company
			total_emps_in_scope = frappe.db.count("Employee", filters=scope_filter)

		elif scope == 'Employee Group' and group_employees_list is not None:
			active_group_employees = frappe.get_all(
				"Employee",
				filters={"name": ["in", group_employees_list], "status": "Active"},
				pluck="name"
			)
			total_emps_in_scope = len(set(active_group_employees + [self.employee]))

		if total_emps_in_scope == 0:
			return float("inf")

		abs_max = cint(settings.max_concurrent_planned_leaves_absolute)
		perc_max = flt(settings.max_concurrent_planned_leaves_percentage)

		perc_limit = cint((perc_max / 100.0) * total_emps_in_scope) if perc_max > 0 else 0
		if perc_max > 0 and perc_limit == 0:
			perc_limit = 1  # minimum 1 if positive percentage

		if abs_max and perc_limit:
			return min(abs_max, perc_limit)
		elif abs_max:
			return abs_max
		elif perc_limit:
			return perc_limit
		else:
			return total_emps_in_scope or float("inf")

	def calculate_slot_days(self, from_date, to_date):
		from_date, to_date = getdate(from_date), getdate(to_date)
		if from_date > to_date:
			return 0

		total_days = (to_date - from_date).days + 1
		holidays = get_holidays_for_employee(self.employee, from_date, to_date)
		holiday_dates = {getdate(h["holiday_date"]) for h in holidays}

		working_days = sum(
			1 for i in range(total_days)
			if (from_date + frappe.utils.timedelta(days=i)) not in holiday_dates
		)

		return working_days

	def update_application_status(self):
		total = len(self.leave_plan_slots)
		applied = sum(1 for slot in self.leave_plan_slots if slot.slot_status == "Applied")

		if applied == 0:
			self.status = "Not Applied"
		elif applied == total:
			self.status = "Fully Applied"
		else:
			self.status = "Partially Applied"