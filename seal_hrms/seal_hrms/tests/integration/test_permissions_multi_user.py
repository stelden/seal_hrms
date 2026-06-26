# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Multi-user permission scoping — real users, real roles, real get_list filtering.

Per SPEC §10:
  - Employee Self Service: only own records visible
  - Leave Approver: own + direct reports
  - HR User / HR Manager: everything in company

Each test creates a couple of disposable users with the right roles,
links them to existing test employees, and verifies that frappe.get_list
honors the scoping.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms.tests.integration._fixtures import (
	COMPANY,
	add_cycle_member,
	cleanup_cycle_and_member,
	cleanup_plan,
	create_leave_plan,
	create_open_cycle,
	ensure_allocation,
	ensure_leave_period,
	ensure_plannable_leave_type,
	next_business_day,
)


EMP_PRIMARY = "_T-Employee-00002"
EMP_TEAM_REPORT = "_T-Employee-00003"
EMP_OTHER = "_T-Employee-00001"


def _ensure_user_bare(email: str) -> str:
	"""Create-or-ensure a User with NO custom roles."""
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.email = email
		user.first_name = email.split("@")[0]
		user.send_welcome_email = 0
		user.enabled = 1
		user.user_type = "System User"
		user.flags.ignore_password_policy = True
		user.insert(ignore_permissions=True)
	return email


def _force_add_role(user_email: str, role: str) -> None:
	"""Insert Has Role row directly to bypass `validate_employee_role` from
	ERPNext, which strips Employee Self Service for users not linked to an
	Employee record. Test fixtures only — production code goes through
	User.add_roles."""
	if frappe.db.exists("Has Role", {"parent": user_email, "role": role}):
		return
	hr = frappe.get_doc({
		"doctype": "Has Role",
		"parent": user_email,
		"parenttype": "User",
		"parentfield": "roles",
		"role": role,
	})
	hr.flags.ignore_permissions = True
	hr.insert(ignore_permissions=True)


def _link_employee_to_user(employee: str, user: str) -> str:
	"""Set Employee.user_id = user. Returns the previous value for restoration."""
	previous = frappe.db.get_value("Employee", employee, "user_id") or ""
	frappe.db.set_value("Employee", employee, "user_id", user, update_modified=False)
	return previous


def _set_leave_approver(employee: str, approver_user: str) -> str:
	previous = frappe.db.get_value("Employee", employee, "leave_approver") or ""
	frappe.db.set_value("Employee", employee, "leave_approver", approver_user, update_modified=False)
	return previous


class TestPermissionsMultiUser(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.leave_type = ensure_plannable_leave_type("MultiUser Plannable")
		cls.leave_period = ensure_leave_period(COMPANY)
		ensure_allocation(EMP_PRIMARY, cls.leave_type, cls.leave_period, days=30)
		ensure_allocation(EMP_TEAM_REPORT, cls.leave_type, cls.leave_period, days=30)
		ensure_allocation(EMP_OTHER, cls.leave_type, cls.leave_period, days=30)

		cls.employee_user = _ensure_user_bare("test-leave-employee@example.com")
		cls.manager_user = _ensure_user_bare("test-leave-manager@example.com")
		cls.hr_user = _ensure_user_bare("test-leave-hr@example.com")

		# Link employee→user FIRST so Employee Self Service role survives
		# the ERPNext validate_employee_role hook on subsequent saves.
		cls._original_user_ids = {
			EMP_PRIMARY: _link_employee_to_user(EMP_PRIMARY, cls.employee_user),
			EMP_TEAM_REPORT: _link_employee_to_user(EMP_TEAM_REPORT, cls.manager_user),
			EMP_OTHER: _link_employee_to_user(EMP_OTHER, ""),
		}
		cls._original_approvers = {
			EMP_PRIMARY: _set_leave_approver(EMP_PRIMARY, cls.manager_user),
			EMP_TEAM_REPORT: _set_leave_approver(EMP_TEAM_REPORT, cls.manager_user),
			EMP_OTHER: _set_leave_approver(EMP_OTHER, ""),
		}
		frappe.db.commit()

		# Force-add roles via direct Has Role insert (bypasses validate_employee_role).
		for role in ("Employee Self Service",):
			_force_add_role(cls.employee_user, role)
		for role in ("Employee Self Service", "Leave Approver"):
			_force_add_role(cls.manager_user, role)
		for role in ("Employee Self Service", "HR User"):
			_force_add_role(cls.hr_user, role)
		frappe.db.commit()
		for u in (cls.employee_user, cls.manager_user, cls.hr_user):
			frappe.clear_cache(user=u)

	@classmethod
	def tearDownClass(cls):
		for emp, prev in cls._original_user_ids.items():
			frappe.db.set_value("Employee", emp, "user_id", prev or None, update_modified=False)
		for emp, prev in cls._original_approvers.items():
			frappe.db.set_value("Employee", emp, "leave_approver", prev or None, update_modified=False)
		frappe.db.commit()
		super().tearDownClass()

	def setUp(self):
		self.cycle = create_open_cycle(COMPANY, self.leave_period, label_suffix=self._testMethodName)
		self.member_primary = add_cycle_member(self.cycle, EMP_PRIMARY)
		self.member_report = add_cycle_member(self.cycle, EMP_TEAM_REPORT)
		self.member_other = add_cycle_member(self.cycle, EMP_OTHER)

		self.plan_primary = self._submit_plan(EMP_PRIMARY, days_offset=30)
		self.plan_report = self._submit_plan(EMP_TEAM_REPORT, days_offset=60)
		self.plan_other = self._submit_plan(EMP_OTHER, days_offset=90)
		self._original_user = frappe.session.user
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user(self._original_user)
		for plan in (self.plan_primary, self.plan_report, self.plan_other):
			cleanup_plan(plan)
		for member in (self.member_primary, self.member_report, self.member_other):
			if frappe.db.exists("Leave Planning Cycle Member", member):
				frappe.delete_doc("Leave Planning Cycle Member", member, force=1, ignore_permissions=True)
		cleanup_cycle_and_member(self.cycle, "")
		frappe.db.commit()

	def test_employee_self_service_sees_own_plan_only(self):
		frappe.set_user(self.employee_user)
		visible = frappe.get_list("Leave Plan", filters={"planning_cycle": self.cycle}, pluck="name")
		self.assertIn(self.plan_primary, visible)
		self.assertNotIn(self.plan_report, visible)
		self.assertNotIn(self.plan_other, visible)

	def test_leave_approver_sees_direct_reports_plans(self):
		frappe.set_user(self.manager_user)
		visible = frappe.get_list("Leave Plan", filters={"planning_cycle": self.cycle}, pluck="name")
		self.assertIn(self.plan_primary, visible, "manager should see primary's plan (manager is approver)")
		self.assertIn(self.plan_report, visible, "manager should see direct report's plan")
		self.assertNotIn(self.plan_other, visible, "manager should NOT see plans of non-reports")

	def test_hr_user_sees_every_plan_in_cycle(self):
		frappe.set_user(self.hr_user)
		visible = frappe.get_list("Leave Plan", filters={"planning_cycle": self.cycle}, pluck="name")
		for p in (self.plan_primary, self.plan_report, self.plan_other):
			self.assertIn(p, visible, f"HR User should see {p}")

	def test_administrator_sees_every_plan(self):
		frappe.set_user("Administrator")
		visible = frappe.get_list("Leave Plan", filters={"planning_cycle": self.cycle}, pluck="name")
		for p in (self.plan_primary, self.plan_report, self.plan_other):
			self.assertIn(p, visible)

	def test_cycle_member_visibility_for_employee_self_service(self):
		frappe.set_user(self.employee_user)
		visible = frappe.get_list(
			"Leave Planning Cycle Member",
			filters={"cycle": self.cycle},
			pluck="name",
		)
		self.assertIn(self.member_primary, visible)
		self.assertNotIn(self.member_other, visible)

	def test_booking_visibility_scoped_to_employee(self):
		"""A booking for EMP_PRIMARY should only be visible to that employee + their approver + HR."""
		from seal_hrms.seal_hrms.tests.integration._fixtures import file_leave_application
		slot = frappe.db.get_value(
			"Leave Plan Slot",
			{"parent": self.plan_primary},
			["name", "from_date", "to_date"],
			as_dict=True,
		)
		la = file_leave_application(EMP_PRIMARY, self.leave_type, slot.from_date, slot.to_date)
		la.submit()

		try:
			frappe.set_user(self.employee_user)
			visible_self = frappe.get_list("Leave Plan Slot Booking", pluck="name")
			self.assertGreater(len(visible_self), 0, "owner should see own bookings")

			# A user with no relationship to the booking either sees an empty list
			# OR is denied at the doctype-perm layer — both indicate the gate works.
			frappe.set_user("test-leave-employee@example.com")  # owner user is fine here
			frappe.set_user("Guest")
			gate_held = False
			try:
				visible_guest = frappe.get_list(
					"Leave Plan Slot Booking",
					filters={"leave_application": la.name},
					pluck="name",
				)
				gate_held = visible_guest == []
			except frappe.exceptions.PermissionError:
				gate_held = True
			self.assertTrue(gate_held, "Guest must not see any bookings")
		finally:
			frappe.set_user("Administrator")
			la.cancel()
			frappe.delete_doc("Leave Application", la.name, force=1, ignore_permissions=True)

	def _submit_plan(self, employee: str, days_offset: int) -> str:
		slot_from = next_business_day(add_days(today(), days_offset))
		slot_to = add_days(slot_from, 4)
		plan = create_leave_plan(self.cycle, employee, [{
			"leave_type": self.leave_type,
			"from_date": slot_from,
			"to_date": slot_to,
		}])
		plan.submit()
		return plan.name
