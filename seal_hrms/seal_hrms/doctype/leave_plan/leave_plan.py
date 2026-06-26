# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Leave Plan controller — read-and-throw gates per SPEC §6.2.

Per SEAL_DEV_RULES §3.1, validate() is a gate: it reads, computes display
fields on `self`, and throws on violation. It does NOT write to other docs,
send mail, publish realtime, or commit. Side effects live in the v2
endpoints under `seal_hrms.seal_hrms.leave_planning.endpoints`.

Workflow handling per §3.2: this controller is "workflow-tolerant" — when
the Leave Plan Approval workflow is active, transitions are validated; when
it isn't (no workflow_state value), submit proceeds normally.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from seal_hrms.seal_hrms.leave_planning.slots import calculate_slot_days


_VALID_WORKFLOW_STATES = {
	"Draft", "Pending Manager", "Pending HR", "Returned", "Approved", "Cancelled",
}


class LeavePlan(Document):

	def validate(self) -> None:
		self._recalculate_slot_days()
		self._compute_total_days()
		self._validate_cycle_gate()
		self._validate_employee_in_scope()
		self._validate_uniqueness()
		self._validate_slot_dates_in_period()
		self._validate_slot_internals()
		self._validate_slot_overlap_within_plan()
		self._validate_per_slot_day_range_vs_leave_type()
		self._validate_slot_count_vs_leave_type()
		self._validate_workflow_state_transition()

	def before_submit(self) -> None:
		self._validate_workflow_state_for_submit()
		self._validate_at_least_one_slot()
		self._validate_leave_allocations()
		self._validate_leave_block_list()
		self._validate_concurrency_rules()

	def on_submit(self) -> None:
		pass

	def before_cancel(self) -> None:
		"""Per §3.1 — read+throw gate. Defends against direct .cancel() bypassing the
		cancel_plan endpoint. Runs while docstatus is still 1, so the gate is
		'has active bookings' rather than the endpoint's broader 'can_cancel' check.
		"""
		active = frappe.db.sql(
			"""
			SELECT leave_application FROM `tabLeave Plan Slot Booking`
			WHERE leave_plan = %s AND status = 'Active'
			""",
			(self.name,),
		)
		if active:
			la_list = ", ".join(b[0] for b in active[:5])
			more = f" (+{len(active) - 5} more)" if len(active) > 5 else ""
			frappe.throw(_(
				"Cannot cancel — {0} Leave Application(s) still draw from this plan: {1}{2}. "
				"Cancel those first."
			).format(len(active), la_list, more), title=_("Cannot Cancel Leave Plan"))

	def on_cancel(self) -> None:
		pass

	def _recalculate_slot_days(self) -> None:
		"""Recompute slot.days from from/to. Pure assignment to self — not a DB write."""
		for slot in self.leave_plan_slots or []:
			if slot.from_date and slot.to_date:
				slot.days = calculate_slot_days(self.employee, slot.from_date, slot.to_date)

	def _compute_total_days(self) -> None:
		self.total_days_planned = sum(flt(s.days or 0) for s in (self.leave_plan_slots or []))

	def _validate_cycle_gate(self) -> None:
		"""New plans require an Open cycle. Existing plans are unaffected by cycle close."""
		if self.docstatus == 1:
			return
		cycle_status = frappe.db.get_value("Leave Planning Cycle", self.planning_cycle, "status")
		if cycle_status != "Open":
			frappe.throw(_(
				"Planning Cycle {0} is {1}. New Leave Plans can only be created while the cycle is Open."
			).format(self.planning_cycle, cycle_status or "missing"))

	def _validate_employee_in_scope(self) -> None:
		exists = frappe.db.exists("Leave Planning Cycle Member", {
			"cycle": self.planning_cycle, "employee": self.employee,
		})
		if not exists:
			frappe.throw(_(
				"Employee {0} is not in the scope of Planning Cycle {1}. "
				"Ask HR to add them to the cycle's roster."
			).format(self.employee, self.planning_cycle))

	def _validate_uniqueness(self) -> None:
		"""At most one non-Cancelled plan per (cycle, employee)."""
		others = frappe.db.sql(
			"""
			SELECT name FROM `tabLeave Plan`
			WHERE planning_cycle = %s AND employee = %s
			  AND docstatus != 2 AND name != %s
			""",
			(self.planning_cycle, self.employee, self.name or ""),
		)
		if others:
			frappe.throw(_(
				"{0} already has a Leave Plan ({1}) for cycle {2}. Cancel that one first."
			).format(self.employee, others[0][0], self.planning_cycle))

	def _validate_slot_dates_in_period(self) -> None:
		"""Year-end reject (Fork C / C3): slot dates must fit inside the cycle's leave period."""
		if not self.leave_period:
			return
		period = frappe.db.get_value(
			"Leave Period", self.leave_period,
			["from_date", "to_date"], as_dict=True,
		)
		if not period:
			return
		for idx, slot in enumerate(self.leave_plan_slots or [], start=1):
			if not slot.from_date or not slot.to_date:
				continue
			f, t = getdate(slot.from_date), getdate(slot.to_date)
			if f < period.from_date or t > period.to_date:
				frappe.throw(_(
					"Slot {0} ({1} to {2}) crosses out of leave period {3} "
					"({4} to {5}). File a separate Leave Plan in the cycle covering the other dates."
				).format(idx, slot.from_date, slot.to_date, self.leave_period,
				         period.from_date, period.to_date))

	def _validate_slot_internals(self) -> None:
		for idx, slot in enumerate(self.leave_plan_slots or [], start=1):
			if not slot.leave_type or not slot.from_date or not slot.to_date:
				continue
			if getdate(slot.from_date) > getdate(slot.to_date):
				frappe.throw(_("Slot {0}: From Date cannot be after To Date.").format(idx))

			is_plannable = frappe.get_cached_value(
				"Leave Type", slot.leave_type, "custom_is_plannable",
			)
			if not is_plannable:
				frappe.throw(_(
					"Slot {0}: Leave Type {1} is not marked Plannable and cannot appear in a Leave Plan."
				).format(idx, slot.leave_type))

			if slot.coverage_assignee:
				if slot.coverage_assignee == self.employee:
					frappe.throw(_(
						"Slot {0}: Coverage Assignee cannot be the planning employee."
					).format(idx))
				cover_status = frappe.db.get_value("Employee", slot.coverage_assignee, "status")
				if cover_status != "Active":
					frappe.throw(_(
						"Slot {0}: Coverage Assignee {1} is not an Active employee."
					).format(idx, slot.coverage_assignee))

	def _validate_slot_overlap_within_plan(self) -> None:
		slots = [s for s in (self.leave_plan_slots or []) if s.from_date and s.to_date]
		for i, a in enumerate(slots):
			af, at_ = getdate(a.from_date), getdate(a.to_date)
			for b in slots[i + 1:]:
				bf, bt = getdate(b.from_date), getdate(b.to_date)
				if af <= bt and bf <= at_:
					frappe.throw(_(
						"Slot {0} ({1} to {2}) overlaps slot {3} ({4} to {5}). "
						"Slots within a plan must have non-overlapping date ranges."
					).format(a.idx, a.from_date, a.to_date, b.idx, b.from_date, b.to_date))

	def _validate_per_slot_day_range_vs_leave_type(self) -> None:
		for slot in self.leave_plan_slots or []:
			if not slot.leave_type or not slot.days:
				continue
			lt = frappe.get_cached_doc("Leave Type", slot.leave_type)
			min_d = int(lt.get("custom_min_days_per_slot") or 0)
			max_d = int(lt.get("custom_max_days_per_slot") or 0)
			days = flt(slot.days)
			if min_d and days < min_d:
				frappe.throw(_(
					"Slot of {0} from {1} to {2}: {3} day(s) is below the minimum {4} for this leave type."
				).format(slot.leave_type, slot.from_date, slot.to_date, days, min_d))
			if max_d and days > max_d:
				frappe.throw(_(
					"Slot of {0} from {1} to {2}: {3} day(s) exceeds the maximum {4} for this leave type."
				).format(slot.leave_type, slot.from_date, slot.to_date, days, max_d))

	def _validate_slot_count_vs_leave_type(self) -> None:
		counts: dict[str, int] = {}
		for slot in self.leave_plan_slots or []:
			if slot.leave_type:
				counts[slot.leave_type] = counts.get(slot.leave_type, 0) + 1
		for lt_name, n in counts.items():
			max_slots = int(frappe.get_cached_value("Leave Type", lt_name, "custom_max_slots_per_plan") or 0)
			if max_slots and n > max_slots:
				frappe.throw(_(
					"This plan has {0} slots of {1} but the leave type allows at most {2} per plan."
				).format(n, lt_name, max_slots))

	def _validate_workflow_state_transition(self) -> None:
		"""Per §3.2 two-mode override: detect any state change and validate it.

		Workflow-tolerant: if no workflow_state is set anywhere, skip entirely.
		Otherwise the new state must be one of the canonical states.
		"""
		if not self.workflow_state:
			return
		if self.workflow_state not in _VALID_WORKFLOW_STATES:
			frappe.throw(_(
				"Workflow state {0} is not recognised. Allowed: {1}."
			).format(self.workflow_state, ", ".join(sorted(_VALID_WORKFLOW_STATES))))

	def _validate_workflow_state_for_submit(self) -> None:
		"""When a workflow_state IS set, only Approved is allowed at submit.

		Without a workflow_state value (no workflow active), submit is unguarded.
		"""
		if not self.workflow_state:
			return
		if self.workflow_state != "Approved":
			frappe.throw(_(
				"Leave Plan can only be submitted from workflow state Approved (currently {0})."
			).format(self.workflow_state))

	def _validate_at_least_one_slot(self) -> None:
		if not self.leave_plan_slots:
			frappe.throw(_("At least one slot is required to submit a Leave Plan."))

	def _validate_leave_allocations(self) -> None:
		from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
		for slot in self.leave_plan_slots or []:
			balance = get_leave_balance_on(
				employee=self.employee,
				leave_type=slot.leave_type,
				date=slot.from_date,
				to_date=slot.to_date,
				for_consumption=True,
			)
			consumable = flt((balance or {}).get("leave_balance_for_consumption", 0))
			if flt(slot.days) > consumable:
				frappe.throw(_(
					"Slot of {0} from {1} to {2} requests {3} day(s) but only {4} available "
					"in {5}'s allocation."
				).format(slot.leave_type, slot.from_date, slot.to_date, slot.days, consumable, self.employee))

	def _validate_leave_block_list(self) -> None:
		from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
		for slot in self.leave_plan_slots or []:
			blocked = get_applicable_block_dates(
				from_date=slot.from_date,
				to_date=slot.to_date,
				employee=self.employee,
				company=self.company,
				leave_type=slot.leave_type,
			)
			if blocked:
				dates = ", ".join(str(b.block_date) for b in blocked)
				frappe.throw(_(
					"Slot of {0} from {1} to {2} overlaps blocked dates: {3}."
				).format(slot.leave_type, slot.from_date, slot.to_date, dates))

	def _validate_concurrency_rules(self) -> None:
		from seal_hrms.seal_hrms.leave_planning.concurrency import evaluate_slot
		for slot in self.leave_plan_slots or []:
			violations = evaluate_slot(slot, self)
			if violations:
				frappe.throw(violations[0]["message"])
