# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Adding approved time off to Frappe HR's leave ledger, and taking it back.

The balance stays Frappe HR's, so leave applications, approvers and balance
reports work unchanged. Allocations of one leave type cannot overlap, so each
person has one allocation of the time off type per leave period, started at
zero (an "anchor"), and each approved claim adds one ledger row tagged with the
claim (`custom_toil_claim`) — the route Compensatory Leave Request takes
(`hrms.hr.utils.create_additional_leave_ledger_entry`), with the tag added.

Cancelling a claim writes a matching negative row, as Compensatory Leave
Request does, so the trail keeps both.

Lapsing time is `toil.lapse` (1.13.0): Frappe HR's year-end job never lapses an
allocation with more than one row, so every lapse is written there
(WORKING_TIME_DESIGN.md F1, §5.5).

Nothing here is whitelisted; the callers check who is asking (§2.15).
"""

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import add_days, flt, formatdate, getdate, today
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.utils import get_leave_period

from seal_hrms.seal_hrms.toil.days import round2, within_cap
from seal_hrms.seal_hrms.working_time.policy import DAY_APPROVED, policy_for

FLAG = "seal_toil_ledger"
ALLOCATION = "Leave Allocation"
LEDGER = "Leave Ledger Entry"


@contextmanager
def toil_ledger_writes():
	"""Mark writes as ours, so the guards on allocations let them through. In-process only."""
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = True
	try:
		yield
	finally:
		frappe.flags[FLAG] = previous


def is_ours() -> bool:
	return bool(frappe.flags.get(FLAG))


def held(employee: str, leave_type: str) -> float:
	"""Time off the person holds now, counting leave already approved for later.

	`get_leave_balance_on` with its access check left out: that check admits the
	person and their named approver only, and a stand-in approving in the
	approver's place, already checked by our callers, would be refused.
	"""
	from hrms.hr.doctype.leave_application import leave_application as la

	day = today()
	allocation = la.get_leave_allocation_records(employee, day, leave_type).get(leave_type, frappe._dict())
	if not allocation:
		return 0.0
	cf_expiry = la.get_allocation_expiry_for_cf_leaves(employee, leave_type, day, allocation.from_date)
	taken = la.get_leaves_for_period(employee, leave_type, allocation.from_date, allocation.to_date)
	expired = la.get_manually_expired_leaves(employee, leave_type, allocation.from_date, allocation.to_date)
	return flt(la.get_remaining_leaves(allocation, taken, day, cf_expiry, expired).get("leave_balance"))


def _period(company: str):
	day = getdate(today())
	period = get_leave_period(day, day, company)
	if not period:
		frappe.throw(
			_(
				"{0} has no active leave period covering today, so time off cannot be added. Ask HR to set one up."
			).format(company),
			title=_("No Leave Period"),
		)
	return period[0]


def prepare(claim) -> None:
	"""At approval, before submit: where the time goes, until when, and how much fits under the cap."""
	policy = policy_for(claim.company)
	_period(claim.company)
	claim.leave_type = policy.leave_type
	claim.earned_on = max(getdate(line.work_date) for line in claim.lines)
	start = getdate(today()) if policy.lapse_counted_from == DAY_APPROVED else claim.earned_on
	claim.lapses_on = add_days(start, int(policy.validity_days or 0)) if policy.validity_days else None
	if claim.lapses_on and getdate(claim.lapses_on) < getdate(today()):
		frappe.throw(
			_("This time would have lapsed on {0}, so there is nothing left to add.").format(
				formatdate(claim.lapses_on)
			),
			title=_("Already Lapsed"),
		)
	current = held(claim.employee, policy.leave_type) if policy.balance_cap else 0.0
	claim.days_credited, claim.days_not_credited = within_cap(claim.days, current, flt(policy.balance_cap))
	if claim.days_credited <= 0:
		frappe.throw(
			_("{0} already holds the most time off allowed ({1} days), so nothing can be added.").format(
				claim.employee_name, policy.balance_cap
			),
			title=_("At the Limit"),
		)


def _allocation_for(claim) -> str:
	"""The person's time off allocation covering today, made if there is none."""
	day = getdate(today())
	name = frappe.db.get_value(
		ALLOCATION,
		[
			["employee", "=", claim.employee],
			["leave_type", "=", claim.leave_type],
			["docstatus", "=", 1],
			["from_date", "<=", day],
			["to_date", ">=", day],
		],
		"name",
	)
	if name:
		return name
	period = _period(claim.company)
	clash = frappe.db.get_value(
		ALLOCATION,
		[
			["employee", "=", claim.employee],
			["leave_type", "=", claim.leave_type],
			["docstatus", "=", 1],
			["to_date", ">=", period.from_date],
			["from_date", "<=", period.to_date],
		],
		"name",
	)
	if clash:
		frappe.throw(
			_(
				"{0} already has an allocation of {1} ({2}) that does not cover today. Ask HR to correct it."
			).format(claim.employee_name, claim.leave_type, clash)
		)
	joined = frappe.db.get_value("Employee", claim.employee, "date_of_joining")
	allocation = frappe.new_doc(ALLOCATION)
	allocation.employee = claim.employee
	allocation.leave_type = claim.leave_type
	allocation.from_date = max(getdate(period.from_date), getdate(joined)) if joined else period.from_date
	allocation.to_date = period.to_date
	allocation.new_leaves_allocated = 0
	allocation.carry_forward = 0
	allocation.description = _("Time off in lieu, added claim by claim")
	with toil_ledger_writes():
		allocation.insert(ignore_permissions=True)
		allocation.submit()
	return allocation.name


def _rows(claim, positive: bool | None = None) -> list:
	filters = [["custom_toil_claim", "=", claim.name], ["docstatus", "=", 1], ["is_expired", "=", 0]]
	if positive is not None:
		filters.append(["leaves", ">" if positive else "<", 0])
	return frappe.get_all(LEDGER, filters=filters, fields=["name", "leaves", "from_date", "transaction_name"])


def _move_totals(allocation: str, days: float) -> None:
	new, total = frappe.db.get_value(
		ALLOCATION, allocation, ["new_leaves_allocated", "total_leaves_allocated"]
	)
	frappe.db.set_value(
		ALLOCATION,
		allocation,
		{
			"new_leaves_allocated": round2(flt(new) + days),
			"total_leaves_allocated": round2(flt(total) + days),
		},
		update_modified=False,
	)


def credit(claim) -> None:
	"""Add the approved days to the person's balance. Does nothing if this claim was added already."""
	if _rows(claim, positive=True):
		return
	allocation = frappe.get_doc(ALLOCATION, _allocation_for(claim))
	with toil_ledger_writes():
		create_leave_ledger_entry(
			allocation,
			dict(
				leaves=claim.days_credited,
				from_date=getdate(today()),
				to_date=allocation.to_date,
				is_carry_forward=0,
				custom_toil_claim=claim.name,
			),
		)
		_move_totals(allocation.name, claim.days_credited)
	claim.db_set("leave_allocation", allocation.name, update_modified=False)


def reverse(claim) -> None:
	"""Take a cancelled claim's days back out of the balance, keeping both rows."""
	net = sum(flt(r.leaves) for r in _rows(claim))
	credits = _rows(claim, positive=True)
	if net <= 0 or not credits:
		return
	allocation = frappe.get_doc(ALLOCATION, credits[0].transaction_name)
	with toil_ledger_writes():
		create_leave_ledger_entry(
			allocation,
			dict(
				leaves=-net,
				from_date=credits[0].from_date,
				to_date=allocation.to_date,
				is_carry_forward=0,
				custom_toil_claim=claim.name,
			),
		)
		_move_totals(allocation.name, -net)


def credited_to(allocation: str) -> float:
	"""Net days that claims have added to an allocation."""
	value = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(leaves), 0) FROM `tabLeave Ledger Entry`
		WHERE transaction_type = 'Leave Allocation' AND transaction_name = %s AND docstatus = 1
		  AND is_expired = 0 AND IFNULL(custom_toil_claim, '') != ''
		""",
		allocation,
	)
	return flt(value[0][0]) if value else 0.0
