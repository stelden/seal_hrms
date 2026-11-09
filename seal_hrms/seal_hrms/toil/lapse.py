# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Rolling lapse of time off in lieu: each claim's time lapses on its own date.

Frappe HR's year-end job never lapses an allocation with more than one ledger
row (WORKING_TIME_DESIGN.md F1), and cancelling any leave application can
delete an unrelated lapse row (F3). So lapses are never written once and
trusted: `reconcile` works out from scratch what every claim's lapse should be
(`fifo.simulate`) and changes only the rows that differ. Running it twice
changes nothing, and it repairs whatever F3 deleted.

It runs when a claim is approved or cancelled, after every leave application of
the time off type is submitted or cancelled, and daily. A lapse row is dated
the claim's last usable day and counts from the day after, as Frappe HR's own
lapse rows do (pinned by tests/test_hrms_time_behaviour.py, S3).

Time on the allocation that no claim added (a Compensatory Leave Request from
before the company switched time off in lieu on) can be used until the end of
the leave year but is not lapsed here; a health check reports it.

Nothing here is whitelisted; the callers check who is asking (SEAL_DEV_RULES §2.15).
"""

import frappe
from frappe import _
from frappe.utils import flt, formatdate, get_link_to_form, getdate, today

from seal_hrms.seal_hrms.toil import fifo
from seal_hrms.seal_hrms.toil.ledger import ALLOCATION, LEDGER, toil_ledger_writes
from seal_hrms.seal_hrms.working_time.policy import toil_leave_types

CLAIM = "Time Off in Lieu Claim"
UNTAGGED = ""  # the lot for time no claim added


def _allocation(name: str) -> frappe._dict:
	return frappe.db.get_value(
		ALLOCATION,
		name,
		["name", "employee", "leave_type", "from_date", "to_date", "docstatus"],
		as_dict=True,
	)


def load(allocation: str, without_claim: str | None = None, without_application: str | None = None):
	"""(lots, uses) for one allocation, as they stand in the ledger."""
	alloc = _allocation(allocation)
	start, end = getdate(alloc.from_date), getdate(alloc.to_date)
	credits = frappe.db.sql(
		"""
		SELECT IFNULL(custom_toil_claim, '') AS claim, SUM(leaves) AS days, MIN(from_date) AS available_from
		FROM `tabLeave Ledger Entry`
		WHERE transaction_type = 'Leave Allocation' AND transaction_name = %s
		  AND docstatus = 1 AND is_expired = 0
		GROUP BY IFNULL(custom_toil_claim, '')
		""",
		allocation,
		as_dict=True,
	)
	keys = [c.claim for c in credits if c.claim]
	lapses_on = (
		dict(
			frappe.get_all(CLAIM, filters={"name": ["in", keys]}, fields=["name", "lapses_on"], as_list=True)
		)
		if keys
		else {}
	)
	lots = []
	for c in credits:
		if c.claim and c.claim == without_claim:
			continue
		if c.claim:
			lapse = lapses_on.get(c.claim)
			valid_through = min(getdate(lapse), end) if lapse else end
			available_from = getdate(c.available_from)
		else:
			valid_through, available_from = end, start
		lots.append(fifo.Lot(c.claim, flt(c.days), available_from, valid_through))

	uses = [
		fifo.Use(row.transaction_name, getdate(row.from_date), -flt(row.leaves))
		for row in frappe.get_all(
			LEDGER,
			filters=[
				["employee", "=", alloc.employee],
				["leave_type", "=", alloc.leave_type],
				["transaction_type", "=", "Leave Application"],
				["docstatus", "=", 1],
				["leaves", "<", 0],
				["from_date", ">=", start],
				["from_date", "<=", end],
			],
			fields=["transaction_name", "from_date", "leaves"],
		)
		if row.transaction_name != without_application
	]
	return lots, uses


def outcome(allocation: str, extra_uses=(), **without) -> fifo.Outcome:
	lots, uses = load(allocation, **without)
	return fifo.simulate(lots, [*uses, *extra_uses], getdate(today()))


def _cancel_row(name: str) -> None:
	row = frappe.get_doc(LEDGER, name)
	row.flags.ignore_permissions = True
	with toil_ledger_writes():
		row.cancel()


def reconcile(allocation: str) -> fifo.Outcome:
	"""Make the allocation's lapse rows and claims' figures match the FIFO outcome. Idempotent."""
	# Serialise approval, cancellation, leave and the daily job on this allocation (§3.3).
	frappe.db.get_value(ALLOCATION, allocation, "name", for_update=True)
	alloc = _allocation(allocation)
	if not alloc or alloc.docstatus != 1:
		return fifo.Outcome(lots=[])
	result = outcome(allocation)
	written = frappe.get_all(
		LEDGER,
		filters={
			"transaction_type": "Leave Allocation",
			"transaction_name": allocation,
			"docstatus": 1,
			"is_expired": 1,
		},
		fields=["name", "leaves", "to_date", "custom_toil_claim"],
	)
	by_claim: dict[str, list] = {}
	for row in written:
		by_claim.setdefault(row.custom_toil_claim or UNTAGGED, []).append(row)

	# Lapses nobody here wrote (the stock year-end job, "Expire Allocation") are undone:
	# time off in lieu lapses only by its own dates.
	for row in by_claim.pop(UNTAGGED, []):
		_cancel_row(row.name)
		frappe.get_doc(ALLOCATION, allocation).add_comment(
			"Info",
			_("A lapse of {0} days was undone: time off in lieu lapses claim by claim.").format(
				-flt(row.leaves)
			),
		)

	targets = {lot.key: lot for lot in result.lots if lot.key}
	for key in set(by_claim) | set(targets):
		lot = targets.get(key)
		target = lot.lapsed if lot else 0.0
		rows = by_claim.get(key, [])
		if (
			len(rows) == 1
			and target > fifo.EPS
			and abs(-flt(rows[0].leaves) - target) < fifo.EPS
			and getdate(rows[0].to_date) == lot.valid_through
		):
			continue
		for row in rows:
			_cancel_row(row.name)
		if target > fifo.EPS:
			from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry

			with toil_ledger_writes():
				create_leave_ledger_entry(
					frappe.get_doc(ALLOCATION, allocation),
					dict(
						leaves=-target,
						from_date=lot.valid_through,
						to_date=lot.valid_through,
						is_expired=1,
						is_carry_forward=0,
						custom_toil_claim=key,
					),
				)

	for lot in result.lots:
		if lot.key:
			frappe.db.set_value(
				CLAIM,
				lot.key,
				{"days_used": round(lot.used, 2), "days_lapsed": lot.lapsed, "days_left": lot.left},
				update_modified=False,
			)
	settled = getdate(alloc.to_date) < getdate(today()) and all(
		not lot.left for lot in result.lots if lot.key
	)
	frappe.db.set_value(ALLOCATION, allocation, "expired", 1 if settled else 0, update_modified=False)
	return result


def allocations_of(employee: str, leave_type: str) -> list[str]:
	return frappe.get_all(
		ALLOCATION, filters={"employee": employee, "leave_type": leave_type, "docstatus": 1}, pluck="name"
	)


def allocation_on(employee: str, leave_type: str, day) -> str | None:
	return frappe.db.get_value(
		ALLOCATION,
		[
			["employee", "=", employee],
			["leave_type", "=", leave_type],
			["docstatus", "=", 1],
			["from_date", "<=", day],
			["to_date", ">=", day],
		],
		"name",
	)


# ---------------------------------------------------------------- leave applications


def leave_uses_live_time(doc, method=None) -> None:
	"""Leave Application validate: refuse leave that relies on time lapsing first, or that others rely on."""
	if doc.leave_type not in toil_leave_types() or doc.status in ("Rejected", "Cancelled"):
		return
	allocation = allocation_on(doc.employee, doc.leave_type, doc.from_date)
	if not allocation or not flt(doc.total_leave_days):
		return  # Frappe HR refuses leave with no allocation on its own
	use = fifo.Use(doc.name or "new", getdate(doc.from_date), flt(doc.total_leave_days))
	before = outcome(allocation, without_application=doc.name)
	after = outcome(allocation, extra_uses=[use], without_application=doc.name)
	for broken, short in fifo.newly_unfunded(before, after):
		if broken.key == use.key:
			frappe.throw(
				_(
					"Only {0} of these {1} days of time off in lieu can be used for leave starting {2}: "
					"the rest lapses before then, or is already taken by other leave."
				).format(
					round(flt(doc.total_leave_days) - short, 2),
					doc.total_leave_days,
					formatdate(doc.from_date),
				),
				title=_("Not Enough Time Off"),
			)
		frappe.throw(
			_("This leave would use time off that {0} (starting {1}) already relies on.").format(
				get_link_to_form("Leave Application", broken.key), formatdate(broken.on)
			),
			title=_("Not Enough Time Off"),
		)


def after_leave_change(doc, method=None) -> None:
	"""Leave Application on_submit / on_cancel: bring the person's time off lapses back in line.

	Runs after Frappe HR's own handler, which on cancel may have deleted a lapse row it
	had nothing to do with (F3). A failure is logged, not raised: the leave itself is
	fine, and the daily run repairs the ledger.
	"""
	if doc.leave_type not in toil_leave_types():
		return
	for allocation in allocations_of(doc.employee, doc.leave_type):
		try:
			reconcile(allocation)
		except Exception:
			frappe.log_error(
				title="Time off in lieu: lapses not brought in line",
				message=frappe.get_traceback(),
				reference_doctype=ALLOCATION,
				reference_name=allocation,
			)


# ---------------------------------------------------------------- claims


def check_can_cancel(claim) -> None:
	"""Refuse to take back a claim's time that leave already relies on."""
	if not claim.leave_allocation:
		return
	before = outcome(claim.leave_allocation)
	after = outcome(claim.leave_allocation, without_claim=claim.name)
	broken = fifo.newly_unfunded(before, after)
	if broken:
		use, _short = broken[0]
		frappe.throw(
			_("This time is used by {0} (starting {1}). Cancel that leave first.").format(
				get_link_to_form("Leave Application", use.key), formatdate(use.on)
			),
			title=_("Time Already Used"),
		)


# ---------------------------------------------------------------- daily


def allocations_to_watch() -> list[str]:
	types = list(toil_leave_types())
	if not types:
		return []
	return frappe.get_all(
		ALLOCATION,
		filters=[
			["leave_type", "in", types],
			["docstatus", "=", 1],
			["to_date", "is", "set"],
			["to_date", ">=", frappe.utils.add_days(today(), -7)],
		],
		pluck="name",
	)


def daily(allocations: list[str] | None = None, commit: bool = True) -> list[str]:
	"""Scheduled daily: write the lapses that fell due. Tests pass `allocations` and `commit=False`."""
	failed = []
	for allocation in allocations if allocations is not None else allocations_to_watch():
		try:
			reconcile(allocation)
			if commit:
				frappe.db.commit()  # nosemgrep: one allocation at a time, so one failure loses nothing else
		except Exception:
			if commit:
				frappe.db.rollback()
			failed.append(allocation)
			frappe.log_error(
				title="Time off in lieu: daily lapse failed",
				message=frappe.get_traceback(),
				reference_doctype=ALLOCATION,
				reference_name=allocation,
			)
	return failed
