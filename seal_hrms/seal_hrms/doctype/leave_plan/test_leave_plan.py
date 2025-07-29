# Copyright (c) 2025, Stelden EA Ltd and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, add_days, nowdate, add_months
from datetime import timedelta

# Import the DocTypes to be tested or used in setup
from seal_hrms.seal_hrms.doctype.leave_plan.leave_plan import LeavePlan # Assuming this is the path
# from ..seal_hrms_settings.seal_hrms_settings import SEALHRMSSettings # Not directly needed for tests if settings are just fetched

def create_employee(employee_id, department="Sales", branch="Main Branch", company="_Test Company", designation="Sales Executive", holiday_list="_Test Holiday List"):
	if not frappe.db.exists("Employee", employee_id):
		emp = frappe.get_doc({
			"doctype": "Employee",
			"employee_id": employee_id,
			"employee_name": employee_id.replace("-", " ").title(),
			"company": company,
			"department": department,
			"branch": branch,
			"designation": designation,
			"date_of_joining": add_days(nowdate(), -365),
			"status": "Active",
			"holiday_list": holiday_list,
			# Add other mandatory fields if any
		})
		emp.insert(ignore_permissions=True)
		return emp
	return frappe.get_doc("Employee", employee_id)

def create_leave_type(leave_type_name, is_plannable=1, min_days_slot=1, allow_multiple=1, require_one_min_days=0):
	if not frappe.db.exists("Leave Type", leave_type_name):
		lt = frappe.get_doc({
			"doctype": "Leave Type",
			"leave_type_name": leave_type_name,
			"custom_is_plannable": is_plannable,
			"custom_min_days_per_planning_slot": min_days_slot,
			"custom_allow_multiple_slots_in_plan": allow_multiple,
			"custom_require_one_slot_min_days": require_one_min_days,
			# Add other mandatory fields
			"is_lwp": 0,
			"is_compensatory": 0,
			"is_encashable": 0,
		})
		lt.insert(ignore_permissions=True)
		return lt
	# Update existing if rules need to change for a test
	lt = frappe.get_doc("Leave Type", leave_type_name)
	lt.custom_is_plannable = is_plannable
	lt.custom_min_days_per_planning_slot = min_days_slot
	lt.custom_allow_multiple_slots_in_plan = allow_multiple
	lt.custom_require_one_slot_min_days = require_one_min_days
	lt.save(ignore_permissions=True)
	return lt


def create_leave_period(period_name, from_date, to_date):
	if not frappe.db.exists("Leave Period", period_name):
		lp = frappe.get_doc({
			"doctype": "Leave Period",
			"leave_period_name": period_name,
			"from_date": from_date,
			"to_date": to_date,
			"company": "_Test Company",
			# Add other mandatory fields
		})
		lp.insert(ignore_permissions=True)
		return lp
	return frappe.get_doc("Leave Period", period_name)

def create_leave_allocation(employee_id, leave_type_name, leave_period_name, days=20):
	if not frappe.db.exists("Leave Allocation", {"employee": employee_id, "leave_type": leave_type_name, "leave_period": leave_period_name}):
		la = frappe.get_doc({
			"doctype": "Leave Allocation",
			"employee": employee_id,
			"leave_type": leave_type_name,
			"leave_period": leave_period_name,
			"from_date": frappe.db.get_value("Leave Period", leave_period_name, "from_date"),
			"to_date": frappe.db.get_value("Leave Period", leave_period_name, "to_date"),
			"total_leaves_allocated": days,
			"new_leaves_allocated": days, # Or logic based on carry forward
			"docstatus": 1 # Submit it
		})
		la.insert(ignore_permissions=True)
		return la
	return frappe.get_doc("Leave Allocation", {"employee": employee_id, "leave_type": leave_type_name, "leave_period": leave_period_name})

def create_holiday_list(name="_Test Holiday List", weekly_off="Sunday"):
	if not frappe.db.exists("Holiday List", name):
		hl = frappe.get_doc({
			"doctype": "Holiday List",
			"holiday_list_name": name,
			"from_date": add_days(nowdate(), -730), # Last 2 years
			"to_date": add_days(nowdate(), 730),   # Next 2 years
			"weekly_off": weekly_off,
			"company": "_Test Company"
		})
		# Add some holidays if needed for testing calculate_leave_days thoroughly
		# hl.append("holidays", {"holiday_date": "YYYY-MM-DD", "description": "Test Holiday"})
		hl.insert(ignore_permissions=True)
		return hl
	return frappe.get_doc("Holiday List", name)

def setup_seal_hrms_settings(settings_data=None):
	settings = frappe.get_doc("SEAL HRMS Settings") # Singleton
	default_settings = {
		"enable_leave_planning": 1,
		"planning_overlap_scope": 'Department',
		"max_concurrent_planned_leaves_percentage": 20,
		"max_concurrent_planned_leaves_absolute": 1,
		"planning_submission_timing_method": 'Lead Days Before Slot',
		"planning_submission_lead_days": 7,
		"planning_submission_deadline_month": "January", # Default, not used if method is Lead Days
		"planning_submission_deadline_day": 30,        # Default
		"planning_submission_max_future_days": 365,
		"allow_plan_amendment_after_approval": 0,
		"auto_create_leave_application_reminder_days": 7,
	}
	if settings_data:
		default_settings.update(settings_data)
	
	for key, value in default_settings.items():
		settings.set(key, value)
	settings.save(ignore_permissions=True)
	frappe.db.commit() # Ensure settings are saved for the test session
	return settings

def create_employee_group(group_name, employees_list):
	if not frappe.db.exists("Employee Group", group_name):
		group = frappe.get_doc({
			"doctype": "Employee Group",
			"employee_group_name": group_name,
		})
		for emp_id in employees_list:
			emp_doc = frappe.get_doc("Employee", emp_id)
			group.append("employee_list", {
				"employee": emp_doc.name,
				"employee_name": emp_doc.employee_name,
				# "employee_user_id": emp_doc.user_id # if applicable
			})
		group.insert(ignore_permissions=True)
		return group
	return frappe.get_doc("Employee Group", group_name)


class TestLeavePlan(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.delete("Leave Plan")
		frappe.db.delete("Leave Plan Slot")
		# Clean up other test data if necessary
		# frappe.db.delete("Leave Allocation", {"employee": ["like", "test-emp-%"]})
		# frappe.db.delete("Employee", {"employee_id": ["like", "test-emp-%"]})
		# frappe.db.delete("Leave Type", {"leave_type_name": ["like", "Test Plan Leave%"]})
		# frappe.db.delete("Leave Period", {"leave_period_name": ["like", "Test Plan Period%"]})
		# frappe.db.delete("Employee Group", {"employee_group_name": ["like", "Test Plan Group%"]})

		# Setup basic masters
		create_holiday_list()
		cls.company = "_Test Company"
		cls.dept1 = "Test Dept 1"
		cls.dept2 = "Test Dept 2"
		cls.branch1 = "Test Branch 1"

		cls.emp1 = create_employee("test-emp-P1", department=cls.dept1, branch=cls.branch1, company=cls.company).name
		cls.emp2 = create_employee("test-emp-P2", department=cls.dept1, branch=cls.branch1, company=cls.company).name
		cls.emp3 = create_employee("test-emp-P3", department=cls.dept2, branch=cls.branch1, company=cls.company).name # Different dept, same branch
		cls.emp4 = create_employee("test-emp-P4", department=cls.dept1, branch="Test Branch 2", company=cls.company).name # Different branch

		cls.lt_annual = create_leave_type("Test Plan Annual", is_plannable=1, min_days_slot=1, require_one_min_days=5).name
		cls.lt_study = create_leave_type("Test Plan Study", is_plannable=1, min_days_slot=2).name
		cls.lt_sick = create_leave_type("Test Plan Sick", is_plannable=0).name # Non-plannable

		current_year = getdate().year
		cls.period1_start = f"{current_year}-01-01"
		cls.period1_end = f"{current_year}-12-31"
		cls.lp1 = create_leave_period(f"Test Plan Period {current_year}", cls.period1_start, cls.period1_end).name

		create_leave_allocation(cls.emp1, cls.lt_annual, cls.lp1, 25)
		create_leave_allocation(cls.emp1, cls.lt_study, cls.lp1, 10)
		create_leave_allocation(cls.emp2, cls.lt_annual, cls.lp1, 20)
		create_leave_allocation(cls.emp3, cls.lt_annual, cls.lp1, 20)
		create_leave_allocation(cls.emp4, cls.lt_annual, cls.lp1, 20)


		# Setup Employee Group for testing
		cls.group1_name = "Test Plan Group Alpha"
		create_employee_group(cls.group1_name, [cls.emp1, cls.emp2])


	def setUp(self):
		# Reset settings for each test to ensure isolation
		self.settings = setup_seal_hrms_settings()
		frappe.db.commit() # Ensure settings are committed before test runs

	def tearDown(self):
		# Clean up created Leave Plans after each test
		# frappe.db.delete("Leave Plan") # This might be too broad if tests depend on previous plans
		# frappe.db.delete("Leave Plan Slot")
		pass


	def create_basic_leave_plan_doc(self, employee, leave_period, slots_data):
		doc = frappe.get_doc({
			"doctype": "Leave Plan",
			"employee": employee,
			"leave_period": leave_period,
			"company": self.company, # Assuming employee's company
			"department": frappe.db.get_value("Employee", employee, "department"),
			"branch": frappe.db.get_value("Employee", employee, "branch"),
			"leave_plan_slots": slots_data
		})
		return doc

	# --- Test Slot Validations ---
	def test_slot_validations_pass(self):
		plan_start_date = add_days(nowdate(), 30) # Plan well in advance
		slots = [
			{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 6)}, # 7 days, meets 5 day rule
			{"leave_type": self.lt_study, "from_date": add_days(plan_start_date, 10), "to_date": add_days(plan_start_date, 12)} # 3 days, meets min 2
		]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		doc.insert(ignore_permissions=True) # Should pass validate
		self.assertTrue(doc.name)
		doc.delete()

	def test_slot_from_date_after_to_date(self):
		plan_start_date = add_days(nowdate(), 30)
		slots = [{"leave_type": self.lt_annual, "from_date": add_days(plan_start_date, 1), "to_date": plan_start_date}]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "From Date .* cannot be after To Date", doc.insert)

	def test_slot_outside_leave_period(self):
		invalid_date = add_months(self.period1_end, 1)
		slots = [{"leave_type": self.lt_annual, "from_date": invalid_date, "to_date": add_days(invalid_date, 1)}]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "must be within the selected Leave Period", doc.insert)

	def test_slot_non_plannable_leave_type(self):
		plan_start_date = add_days(nowdate(), 30)
		slots = [{"leave_type": self.lt_sick, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 1)}]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "not plannable", doc.insert)

	def test_slot_min_days_violation(self):
		create_leave_type("Test Min Days LT", min_days_slot=3) # Min 3 days
		plan_start_date = add_days(nowdate(), 30)
		slots = [{"leave_type": "Test Min Days LT", "from_date": plan_start_date, "to_date": add_days(plan_start_date, 0)}] # 1 day
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "Min days for slot .* is 3", doc.insert)

	def test_slot_multiple_not_allowed(self):
		lt_single_slot = create_leave_type("Test Single Slot LT", allow_multiple=0).name
		plan_start_date = add_days(nowdate(), 30)
		slots = [
			{"leave_type": lt_single_slot, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 1)},
			{"leave_type": lt_single_slot, "from_date": add_days(plan_start_date, 5), "to_date": add_days(plan_start_date, 6)}
		]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "doesn't allow multiple slots", doc.insert)

	def test_internal_slot_overlap(self):
		plan_start_date = add_days(nowdate(), 30)
		slots = [
			{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 5)},
			{"leave_type": self.lt_annual, "from_date": add_days(plan_start_date, 3), "to_date": add_days(plan_start_date, 7)} # Overlaps
		]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "overlaps Row", doc.insert)

	# --- Test Submission Rules ---
	def test_submission_lead_days_violation(self):
		setup_seal_hrms_settings({"planning_submission_timing_method": 'Lead Days Before Slot', "planning_submission_lead_days": 10})
		plan_start_date = add_days(nowdate(), 5) # Too soon
		slots = [{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 6)}]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "Plan must be submitted at least 10 days before", doc.insert)

	def test_submission_fixed_deadline_violation(self):
		# Assuming today is after Jan 15 of current year for this test
		today = getdate(nowdate())
		deadline_month = today.strftime("%B")
		deadline_day = today.day -1 # Yesterday
		if deadline_day == 0: # Handle start of month
			prev_month_date = add_days(today, -1)
			deadline_month = prev_month_date.strftime("%B")
			deadline_day = prev_month_date.day

		setup_seal_hrms_settings({
			"planning_submission_timing_method": 'Fixed Deadline for Period',
			"planning_submission_deadline_month": deadline_month,
			"planning_submission_deadline_day": deadline_day
		})
		plan_start_date = add_days(nowdate(), 60) # Plan date is fine
		slots = [{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 6)}]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "Submission deadline .* was", doc.insert)

	def test_submission_max_future_days_violation(self):
		setup_seal_hrms_settings({"planning_submission_max_future_days": 30})
		plan_start_date = add_days(nowdate(), 35) # Too far
		slots = [{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 6)}]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		self.assertRaisesRegex(frappe.ValidationError, "exceeds max future planning limit", doc.insert)

	# --- Test before_submit Validations ---
	def test_leave_allocation_exceeded(self):
		plan_start_date = add_days(nowdate(), 30)
		# emp1 has 25 days of lt_annual
		slots = [{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 25)}] # 26 days
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		doc.insert(ignore_permissions=True) # Save draft
		self.assertRaisesRegex(frappe.ValidationError, "exceed available balance", doc.submit)
		doc.delete()

	def test_require_one_slot_min_days_violation(self):
		# lt_annual requires one slot of at least 5 days
		plan_start_date = add_days(nowdate(), 30)
		slots = [
			{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 2)}, # 3 days
			{"leave_type": self.lt_annual, "from_date": add_days(plan_start_date, 10), "to_date": add_days(plan_start_date, 13)} # 4 days
		]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		doc.insert(ignore_permissions=True)
		self.assertRaisesRegex(frappe.ValidationError, "one slot must be >=", doc.submit)
		doc.delete()
	
	def test_leave_block_list_conflict(self):
		plan_start_date = add_days(nowdate(), 30)
		blocked_date = add_days(plan_start_date, 2)
		
		# Create a block list entry
		if not frappe.db.exists("Leave Block List", "Test Block List For Plans"):
			block_list = frappe.get_doc({
				"doctype": "Leave Block List",
				"leave_block_list_name": "Test Block List For Plans",
				"company": self.company,
				"allow_user_to_apply": 0 # Block completely
			})
			block_list.append("leave_block_list_dates", {"block_date": blocked_date, "reason": "Test Plan Block"})
			block_list.insert(ignore_permissions=True)
		else: # Ensure the date is there
			block_list = frappe.get_doc("Leave Block List", "Test Block List For Plans")
			if not any(d.block_date == blocked_date for d in block_list.leave_block_list_dates):
				block_list.append("leave_block_list_dates", {"block_date": blocked_date, "reason": "Test Plan Block"})
				block_list.save(ignore_permissions=True)


		slots = [{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 4)}] # Covers blocked_date
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		doc.insert(ignore_permissions=True)
		self.assertRaisesRegex(frappe.ValidationError, "is blocked", doc.submit)
		doc.delete()


	# --- Test Concurrency Overlap ---
	def test_concurrency_department_overlap_fail(self):
		# Settings: Dept scope, max 1 absolute
		setup_seal_hrms_settings({"planning_overlap_scope": 'Department', "max_concurrent_planned_leaves_absolute": 1, "max_concurrent_planned_leaves_percentage": 0})
		
		plan_date = add_days(nowdate(), 45)
		# Plan 1 for emp1 (Dept1)
		slots1 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 4)}] # 5 days
		doc1 = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots1)
		doc1.insert(ignore_permissions=True)
		doc1.submit()
		self.assertEqual(doc1.docstatus, 1)

		# Plan 2 for emp2 (Same Dept1) - should fail
		slots2 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 2)}] # Overlaps
		doc2 = self.create_basic_leave_plan_doc(self.emp2, self.lp1, slots2)
		doc2.insert(ignore_permissions=True)
		self.assertRaisesRegex(frappe.ValidationError, "conflicts with other plans in your Department", doc2.submit)
		
		doc1.cancel()
		doc1.delete()
		doc2.delete() # Delete draft


	def test_concurrency_department_overlap_pass_different_dept(self):
		setup_seal_hrms_settings({"planning_overlap_scope": 'Department', "max_concurrent_planned_leaves_absolute": 1, "max_concurrent_planned_leaves_percentage": 0})
		plan_date = add_days(nowdate(), 50)
		slots1 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 4)}]
		doc1 = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots1) # emp1 in Dept1
		doc1.insert(ignore_permissions=True); doc1.submit()

		slots2 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 2)}]
		doc2 = self.create_basic_leave_plan_doc(self.emp3, self.lp1, slots2) # emp3 in Dept2
		doc2.insert(ignore_permissions=True)
		doc2.submit() # Should pass as they are in different departments
		self.assertEqual(doc2.docstatus, 1)

		doc1.cancel(); doc1.delete()
		doc2.cancel(); doc2.delete()

	def test_concurrency_employee_group_overlap_fail(self):
		# emp1 and emp2 are in self.group1_name
		setup_seal_hrms_settings({"planning_overlap_scope": 'Employee Group', "max_concurrent_planned_leaves_absolute": 1, "max_concurrent_planned_leaves_percentage": 0})
		plan_date = add_days(nowdate(), 55)
		
		slots1 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 4)}]
		doc1 = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots1)
		doc1.insert(ignore_permissions=True); doc1.submit()

		slots2 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 2)}]
		doc2 = self.create_basic_leave_plan_doc(self.emp2, self.lp1, slots2) # emp2 in same group
		doc2.insert(ignore_permissions=True)
		self.assertRaisesRegex(frappe.ValidationError, "conflicts with other plans in your Employee Group", doc2.submit)

		doc1.cancel(); doc1.delete()
		doc2.delete()

	def test_concurrency_employee_group_overlap_pass_different_group(self):
		# emp1 in group1, emp3 not in group1
		setup_seal_hrms_settings({"planning_overlap_scope": 'Employee Group', "max_concurrent_planned_leaves_absolute": 1, "max_concurrent_planned_leaves_percentage": 0})
		plan_date = add_days(nowdate(), 60)
		
		slots1 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 4)}]
		doc1 = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots1)
		doc1.insert(ignore_permissions=True); doc1.submit()

		slots2 = [{"leave_type": self.lt_annual, "from_date": plan_date, "to_date": add_days(plan_date, 2)}]
		doc2 = self.create_basic_leave_plan_doc(self.emp3, self.lp1, slots2) # emp3 not in emp1's group
		doc2.insert(ignore_permissions=True)
		doc2.submit() # Should pass
		self.assertEqual(doc2.docstatus, 1)

		doc1.cancel(); doc1.delete()
		doc2.cancel(); doc2.delete()


	# --- Test Successful Submission ---
	def test_successful_plan_submission(self):
		setup_seal_hrms_settings() # Default settings, should allow this
		plan_start_date = add_days(nowdate(), 30)
		slots = [
			{"leave_type": self.lt_annual, "from_date": plan_start_date, "to_date": add_days(plan_start_date, 6)}, # 7 days (meets 5 day rule)
			{"leave_type": self.lt_study, "from_date": add_days(plan_start_date, 20), "to_date": add_days(plan_start_date, 22)} # 3 days (meets min 2)
		]
		doc = self.create_basic_leave_plan_doc(self.emp1, self.lp1, slots)
		doc.insert(ignore_permissions=True)
		doc.submit()
		self.assertEqual(doc.docstatus, 1)
		doc.cancel() # Clean up
		doc.delete()

	@classmethod
	def tearDownClass(cls):
		# Clean up all created test data
		frappe.db.delete("Leave Plan")
		frappe.db.delete("Leave Plan Slot")
		frappe.db.delete("Leave Allocation", {"employee": ["in", [cls.emp1, cls.emp2, cls.emp3, cls.emp4]]})
		frappe.db.delete("Employee", {"name": ["in", [cls.emp1, cls.emp2, cls.emp3, cls.emp4]]})
		frappe.db.delete("Leave Type", {"name": ["in", [cls.lt_annual, cls.lt_study, cls.lt_sick, "Test Min Days LT", "Test Single Slot LT"]]})
		frappe.db.delete("Leave Period", {"name": cls.lp1})
		frappe.db.delete("Employee Group", {"name": cls.group1_name})
		frappe.db.delete("Leave Block List", "Test Block List For Plans")
		frappe.db.delete("Holiday List", "_Test Holiday List")
		frappe.db.commit()
		super().tearDownClass()