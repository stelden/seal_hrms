# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""seal_hrms's subscription to My Desk (`seal_desk`).

An ADAPTER and nothing more. What a handover needs from each person is answered
by `seal_hrms.seal_hrms.handover_work`, which returns plain records and runs on
any site. Here each record becomes a row of a My Desk "Waiting for you" list
(seal_desk DESIGN §18.2: a standard group declared through `seal_desk_cue_groups`,
`renders_as: "list"`), which an admin places on any desk page.

**Nothing at module level may import `seal_desk`.** The desk is optional, and
most sites running this app do not have it. These functions are only ever
called by the desk itself, so an import inside them only runs where the desk
exists (SEAL_DEV_RULES §3.15). `tests/test_task_assignment_surfaces.py` enforces
it. Nothing else in seal_hrms imports this module.

Since 1.23.0 it also translates `seal_hrms.my_desk` (approvals, balances, cover,
headlines) into `ApprovalItem`, `CueValue`, `ListRow` and `Headline`; the whitelisted
`act_on_*` functions the approval sources name live in `my_desk/approvals.py`, because
they return plain dicts and need no seal_desk type.
"""

from frappe import _


def handover_rows(ctx):
	"""What leave handovers are waiting on the person looking for."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import ListRow

	from seal_hrms.seal_hrms.handover_work import work_for

	rows = []
	for w in sorted(work_for(ctx.user), key=lambda w: w.due or "9999"):
		meta = " · ".join(p for p in (w.subtitle, _("due {0}").format(w.due) if w.due else "") if p)
		rows.append(ListRow(title=w.title, meta=meta, target=Target("URL", w.route, w.route, None, True)))
	return rows


def self_service(ctx):
	"""Self-Service: the person's own leave, claims, advances and timesheets in flight."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import CueValue

	from seal_hrms.seal_hrms.self_service_status import self_service

	return [
		CueValue(
			cue_key=f.key,
			caption=f.caption,
			value=f.count,
			target=Target("List", f.doctype, ["List", f.doctype], f.route_options(), True),
		)
		for f in self_service(ctx.user, ctx.readable)
	]


def time_rows(ctx):
	"""What time off in lieu is waiting on the person looking for: claims to decide, to correct, to send."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import ListRow

	from seal_hrms.seal_hrms.toil.work import work_for

	rows = []
	for w in work_for(ctx.user):
		meta = " · ".join(p for p in (w.subtitle, w.due or "") if p)
		rows.append(ListRow(title=w.title, meta=meta, target=Target("URL", w.route, w.route, None, True)))
	return rows


def timesheet_rows(ctx):
	"""Timesheets waiting on the person looking: to approve, or returned to them."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import ListRow

	from seal_hrms.seal_hrms.timesheets.work import work_for

	rows = []
	for w in work_for(ctx.user):
		meta = " · ".join(p for p in (w.subtitle, w.due or "") if p)
		rows.append(ListRow(title=w.title, meta=meta, target=Target("URL", w.route, w.route, None, True)))
	return rows


# ---------------------------------------------------------------- My Desk phone app, desk side (P4)
#
# The answers live in `seal_hrms.my_desk` as plain records; these functions only translate
# them into the desk's types (HR_ON_MY_DESK.md §2).


def _target(t):
	"""A plain target record from `my_desk.figures` as the desk's Target."""
	from seal_desk.role_center.routes import Target

	if t.kind == "Report":
		return Target("Report", t.name, ["query-report", t.name], t.filters or None, True)
	return Target("List", t.name, ["List", t.name], t.filters or None, True)


def _approval_items(records):
	from seal_desk.role_center.schema import ApprovalAction, ApprovalItem

	return [
		ApprovalItem(
			doctype=r.doctype,
			name=r.name,
			title=r.title,
			meta=r.meta,
			sender=r.sender,
			since=r.since,
			amount=r.amount,
			currency=r.currency,
			on_behalf_of=r.on_behalf_of,
			actions=[
				ApprovalAction(a.key, a.label, a.tone, needs_reason=bool(a.needs_reason), verify=bool(a.verify))
				for a in r.actions
			],
		)
		for r in records
	]


def leave_approvals(ctx):
	"""Approval source `seal_hrms.leave`: leave waiting for the person as approver or stand-in."""
	from seal_hrms.my_desk import approvals

	return _approval_items(approvals.leave_items(ctx.user))


def expense_approvals(ctx):
	"""Approval source `seal_hrms.expense`: expense claims waiting for the person."""
	from seal_hrms.my_desk import approvals

	return _approval_items(approvals.expense_items(ctx.user))


def toil_approvals(ctx):
	"""Approval source `seal_hrms.toil`: time off claims waiting for the person's decision."""
	from seal_hrms.my_desk import approvals

	return _approval_items(approvals.toil_items(ctx.user))


def timesheet_approvals(ctx):
	"""Approval source `seal_hrms.timesheets`: timesheets waiting for the person's approval."""
	from seal_hrms.my_desk import approvals

	return _approval_items(approvals.timesheet_items(ctx.user))


def balances(ctx):
	"""Balances: leave left per type, time off in lieu left and lapsing."""
	from seal_desk.role_center.schema import CueValue

	from seal_hrms.my_desk import figures

	return [
		CueValue(cue_key=f.key, caption=f.caption, value=f.value, target=_target(f.target))
		for f in figures.balances(ctx.user, ctx.readable or None, ctx.today)
	]


def cover_rows(ctx):
	"""Cover: who covers the person, whom they cover, whose approvals they give."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import ListRow

	from seal_hrms.my_desk import figures

	return [
		ListRow(title=r.title, meta=r.meta, target=Target("URL", r.route, r.route, None, True))
		for r in figures.cover(ctx.user)
	]


def hr_work(ctx):
	"""HR's figures: payout changes waiting to be confirmed."""
	from seal_desk.role_center.schema import CueValue

	from seal_hrms.seal_hrms import payout_change

	if ctx.readable and payout_change.DOCTYPE not in ctx.readable:
		return []
	figure = payout_change.waiting_figure(ctx.user)
	if figure is None:
		return []
	return [CueValue(cue_key=figure.key, caption=figure.caption, value=figure.value, target=_target(figure.target))]


def headlines(ctx):
	"""At most three lines: approving for someone, time off lapsing, last week's timesheet not sent."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import Headline

	from seal_hrms.my_desk import figures

	return [
		Headline(payload=h.text, emphasize=list(h.emphasize or []), route=Target("URL", h.route, h.route, None, True))
		for h in figures.headlines(ctx.user, ctx.today)
	]


def team_away_rows(ctx):
	"""Who's Away This Week: the viewer's team's leave this week, as far as they may read it."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import ListRow

	from seal_hrms.seal_hrms.line_manager import away_rows

	out = []
	for r in away_rows(ctx.user, ctx.today, ctx.company):  # seal_desk D143: the chosen company
		target = Target("Form", f"{r.doctype}::{r.name}", ["Form", r.doctype, r.name], None, True) if r.name else None
		out.append(ListRow(title=r.title, meta=r.meta, target=target))
	return out
