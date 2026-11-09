# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Guards on Frappe HR records that time off in lieu shares.

  * Leave Allocation: the time off type is added to only by approved claims, and
    an allocation holding claimed time cannot be cancelled from under them.
  * Compensatory Leave Request: not on the time off type, which has its own claim.
  * Overtime Slip: a date banked as time off is not paid as well. A slip made
    by Payroll Entry in bulk drops such dates with a note, rather than failing,
    because one refused slip marks the whole payroll run as failed
    (WORKING_TIME_DESIGN.md F11). A date added by hand is refused.

Registered in hooks.py `doc_events`; each reads and throws only.
"""

import frappe
from frappe import _
from frappe.utils import flt, formatdate, get_link_to_form, getdate

from seal_hrms.seal_hrms.toil import ledger
from seal_hrms.seal_hrms.toil.rules import banked_dates
from seal_hrms.seal_hrms.working_time.policy import toil_leave_types

CLAIM = "Time Off in Lieu Claim"


def allocation(doc, method=None) -> None:
	"""Leave Allocation validate: no hand-made time off in lieu."""
	if ledger.is_ours() or doc.leave_type not in toil_leave_types():
		return
	if flt(doc.new_leaves_allocated) or flt(doc.unused_leaves) or doc.carry_forward:
		frappe.throw(
			_(
				"{0} is time off in lieu: it is added by approving a Time Off in Lieu Claim, not by allocating it."
			).format(doc.leave_type),
			title=_("Added by Claims"),
		)


def allocation_cancel(doc, method=None) -> None:
	"""Leave Allocation before_cancel: not while claims' time sits on it."""
	if ledger.is_ours():
		return
	if ledger.credited_to(doc.name) > 0:
		frappe.throw(
			_("Approved time off claims have added time to this allocation. Cancel those claims instead."),
			title=_("Holds Claimed Time"),
		)


def compensatory_request(doc, method=None) -> None:
	"""Compensatory Leave Request before_validate: not on the time off in lieu type."""
	if doc.leave_type and doc.leave_type in toil_leave_types():
		frappe.throw(
			_(
				"{0} is claimed with a Time Off in Lieu Claim, which counts hours and goes to the leave approver."
			).format(doc.leave_type),
			title=_("Use a Time Off in Lieu Claim"),
		)


def drop_banked_dates(doc, method=None) -> None:
	"""Overtime Slip before_validate: leave out dates banked as time off, and say so."""
	rows = doc.get("overtime_details") or []
	banked = banked_dates(doc.employee, [r.date for r in rows if r.date])
	if not banked:
		return
	# Only rows fetched from attendance, which is what Payroll Entry's bulk run makes.
	dropped = [r for r in rows if r.date and getdate(r.date) in banked and r.reference_document]
	if not dropped:
		return  # dates typed by hand: `no_banked_dates` refuses them by name
	for row in dropped:
		doc.remove(row)
	doc.total_overtime_duration = sum(flt(r.overtime_duration) for r in doc.overtime_details)
	doc.flags.seal_banked_dropped = [(r.date, banked[getdate(r.date)]) for r in dropped]


def no_banked_dates(doc, method=None) -> None:
	"""Overtime Slip validate: refuse a date banked as time off."""
	banked = banked_dates(doc.employee, [r.date for r in doc.get("overtime_details") or [] if r.date])
	for day, claim in banked.items():
		frappe.throw(
			_(
				"{0} was given as time off on {1}. A day is either paid or given as time off, not both."
			).format(formatdate(day), get_link_to_form(CLAIM, claim)),
			title=_("Given as Time Off"),
		)


def note_dropped_dates(doc, method=None) -> None:
	"""Overtime Slip on_update: record which dates were left out, and why."""
	dropped = doc.flags.pop("seal_banked_dropped", None) if doc.flags else None
	if not dropped:
		return
	doc.add_comment(
		"Info",
		"; ".join(
			_("{0} left out: given as time off on {1}").format(formatdate(day), claim)
			for day, claim in dropped
		),
	)
