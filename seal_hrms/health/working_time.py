# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Health checks for time off in lieu, shown on App Health and on the Working Time Policy form.

Each is a company that switched time off on but cannot use it: no leave type to
add the time to, a leave type that would misbehave, no leave period to add it
in, no grade allowed to claim, or staff with nobody to approve. Nothing errors
in any of these cases until someone tries to claim, so they are reported here,
where HR fixes them (SEAL_DEV_RULES §1.18). Cheap: they run as the form opens.

seal_common is optional for seal_hrms, so its import is guarded; where it is
absent nothing reads these checks.
"""

import frappe
from frappe import _
from frappe.utils import today

try:
	from seal_common.app_health import Finding, Severity, State, health_check
except ImportError:  # pragma: no cover - only on sites without seal_common

	def health_check(*args, **kwargs):
		return lambda fn: fn


POLICY = "Working Time Policy"
FORMS = (POLICY,)


def _enabled() -> list:
	if not frappe.db.table_exists(POLICY):
		return []
	return frappe.get_all(POLICY, filters={"toil_enabled": 1}, fields=["name", "company", "leave_type"])


def _link(company: str | None = None) -> str:
	return f"/app/working-time-policy/{company}" if company else "/app/working-time-policy"


@health_check(label="Time off in lieu: leave type", category="Configuration", forms=FORMS)
def time_off_has_a_leave_type():
	"""Switched on with nowhere to add the time."""
	missing = [p.company for p in _enabled() if not p.leave_type]
	if not missing:
		return []
	return Finding(
		severity=Severity.BLOCKING,
		title=_("Time off in lieu is on, but no leave type is chosen for it"),
		detail=_("Approved claims cannot be added to anyone's balance until one is picked for: {0}.").format(
			", ".join(missing)
		),
		count=len(missing),
		state=State.MISSING,
		link=_link(missing[0]),
	)


@health_check(label="Time off in lieu: leave type settings", category="Configuration", forms=FORMS)
def time_off_leave_type_fits():
	"""The leave type would carry time over, let people go negative, pay it out, or ask for a leave plan."""
	problems = []
	for policy in _enabled():
		if not policy.leave_type:
			continue
		fields = ["is_compensatory", "is_carry_forward", "allow_negative", "allow_encashment"]
		plannable = frappe.get_meta("Leave Type").has_field("custom_is_plannable")
		if plannable:
			fields.append("custom_is_plannable")
		values = frappe.db.get_value("Leave Type", policy.leave_type, fields, as_dict=True) or {}
		wrong = []
		if not values.get("is_compensatory"):
			wrong.append(_("is not marked as compensatory"))
		if values.get("is_carry_forward"):
			wrong.append(_("carries unused days into next year"))
		if values.get("allow_negative"):
			wrong.append(_("lets people take time they have not earned"))
		if values.get("allow_encashment"):
			wrong.append(_("can be paid out"))
		if plannable and values.get("custom_is_plannable"):
			wrong.append(_("needs a leave plan before it is taken"))
		if wrong:
			problems.append(f"{policy.leave_type} ({policy.company}): " + ", ".join(wrong))
	if not problems:
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("The leave type used for time off in lieu is set up in a way that works against it"),
		detail=_("Change these on the leave type: {0}.").format("; ".join(problems)),
		count=len(problems),
		state=State.MISCONFIGURED,
		link="/app/leave-type",
	)


@health_check(label="Time off in lieu: leave period", category="Configuration", forms=FORMS)
def time_off_has_a_leave_period():
	"""No active leave period covering today: approvals are refused."""
	from hrms.hr.utils import get_leave_period

	missing = [p.company for p in _enabled() if not get_leave_period(today(), today(), p.company)]
	if not missing:
		return []
	return Finding(
		severity=Severity.BLOCKING,
		title=_("No leave period covers today, so approved time off cannot be added"),
		detail=_("Set up an active leave period for: {0}.").format(", ".join(missing)),
		count=len(missing),
		state=State.MISSING,
		link="/app/leave-period",
	)


@health_check(label="Time off in lieu: who can claim", category="Configuration", forms=FORMS)
def time_off_has_grades():
	"""Switched on with no grade allowed to claim."""
	missing = [
		p.company
		for p in _enabled()
		if not frappe.db.exists("Working Time Policy Grade", {"parent": p.name, "parenttype": POLICY})
	]
	if not missing:
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("Time off in lieu is on, but no grade is allowed to claim it"),
		detail=_("Nobody can send a claim until grades are chosen for: {0}.").format(", ".join(missing)),
		count=len(missing),
		state=State.MISCONFIGURED,
		link=_link(missing[0]),
	)


@health_check(label="Time off in lieu: approvers", category="Data", forms=FORMS)
def time_off_has_approvers():
	"""Staff who may claim, with nobody to approve: their claims cannot be sent."""
	total = stranded = 0
	for policy in _enabled():
		grades = frappe.get_all(
			"Working Time Policy Grade", filters={"parent": policy.name, "parenttype": POLICY}, pluck="grade"
		)
		if not grades:
			continue
		staff = frappe.get_all(
			"Employee",
			filters={"company": policy.company, "status": "Active", "grade": ["in", grades]},
			fields=["leave_approver", "department"],
		)
		total += len(staff)
		for person in staff:
			if person.leave_approver:
				continue
			if person.department and frappe.db.exists(
				"Department Approver", {"parent": person.department, "parentfield": "leave_approvers"}
			):
				continue
			stranded += 1
	if not stranded:
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("Some staff who can claim time off have nobody to approve it"),
		detail=_("Give them a leave approver, on their own record or their department's."),
		count=stranded,
		total=total,
		state=State.MISCONFIGURED,
		link="/app/employee",
	)


# ---------------------------------------------------------------- lapses (1.13.0)


def _watched() -> list[str]:
	from seal_hrms.seal_hrms.toil.lapse import allocations_to_watch

	return allocations_to_watch()


@health_check(label="Time off in lieu: lapses up to date", category="Data")
def time_off_lapses_in_step():
	"""Lapse rows that differ from what the claims' dates say: the daily run has not caught up."""
	from frappe.utils import flt, getdate

	from seal_hrms.seal_hrms.toil import lapse

	allocations = _watched()
	behind = 0
	for allocation in allocations:
		result = lapse.outcome(allocation)
		written = {}
		for row in frappe.get_all(
			"Leave Ledger Entry",
			filters={
				"transaction_type": "Leave Allocation",
				"transaction_name": allocation,
				"docstatus": 1,
				"is_expired": 1,
			},
			fields=["custom_toil_claim", "leaves", "to_date"],
		):
			written.setdefault(row.custom_toil_claim or "", []).append(row)
		if written.get(""):
			behind += 1
			continue
		for lot in result.lots:
			if not lot.key:
				continue
			rows = written.get(lot.key, [])
			due = lot.lapsed
			have = -sum(flt(r.leaves) for r in rows)
			if abs(due - have) > 0.005 or (rows and due and getdate(rows[0].to_date) != lot.valid_through):
				behind += 1
				break
	if not behind:
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("Some time off balances do not yet show time that has lapsed"),
		detail=_(
			"The daily run brings them in line; if this stays, check the error log for 'Time off in lieu'."
		),
		count=behind,
		total=len(allocations),
		state=State.STALE,
		link="/app/error-log?method=%25Time%20off%20in%20lieu%25",
	)


@health_check(label="Time off in lieu: leave covered", category="Data")
def time_off_leave_is_covered():
	"""Approved leave of the time off type that no banked time covers."""
	from seal_hrms.seal_hrms.toil import lapse

	allocations = _watched()
	short = sum(1 for a in allocations if lapse.outcome(a).unfunded)
	if not short:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Some approved time off in lieu leave is not covered by banked time"),
		detail=_(
			"Usually leave approved before the time it relied on lapsed or was cancelled. "
			"The person's balance shows below zero; HR decides whether to change the leave."
		),
		count=short,
		total=len(allocations),
		state=State.MISCONFIGURED,
		link="/app/query-report/Time Off in Lieu",
	)


@health_check(label="Time off in lieu: time not from claims", category="Data")
def time_off_not_from_claims():
	"""Time on a time off allocation that no claim added: it never lapses on its own."""
	allocations = _watched()
	if not allocations:
		return []
	rows = frappe.db.sql(
		"""
		SELECT COUNT(DISTINCT transaction_name) FROM `tabLeave Ledger Entry`
		WHERE transaction_type = 'Leave Allocation' AND transaction_name IN %(allocations)s
		  AND docstatus = 1 AND is_expired = 0 AND leaves > 0 AND IFNULL(custom_toil_claim, '') = ''
		""",
		{"allocations": allocations},
	)
	count = rows[0][0] if rows else 0
	if not count:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Some time off in lieu was added without a claim"),
		detail=_(
			"Probably from before the company switched time off in lieu on. It can be used until the end "
			"of the leave year but does not lapse on its own date."
		),
		count=count,
		total=len(allocations),
		state=State.MISCONFIGURED,
		link="/app/leave-allocation",
	)


@health_check(label="Time off in lieu: next leave year", category="Configuration", forms=FORMS)
def time_off_has_next_leave_year():
	"""The leave year ends within 30 days and the next one is not set up: approvals will stop."""
	from frappe.utils import add_days, getdate, today
	from hrms.hr.utils import get_leave_period

	missing = []
	for policy in _enabled():
		period = get_leave_period(today(), today(), policy.company)
		if not period or getdate(period[0].to_date) > getdate(add_days(today(), 30)):
			continue
		following = add_days(period[0].to_date, 1)
		if not get_leave_period(following, following, policy.company):
			missing.append(
				f"{policy.company} ({frappe.format_value(period[0].to_date, {'fieldtype': 'Date'})})"
			)
	if not missing:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("The leave year ends soon and the next one is not set up"),
		detail=_("Claims approved after it ends will be refused until it is: {0}.").format(
			", ".join(missing)
		),
		count=len(missing),
		state=State.MISSING,
		link="/app/leave-period",
	)


@health_check(label="Time off in lieu: claims waiting", category="Data", forms=FORMS)
def time_off_claims_waiting():
	"""Claims waiting for a decision longer than the company allows: someone is stuck."""
	from frappe.utils import add_days, now_datetime

	if not frappe.db.table_exists("Time Off in Lieu Claim"):
		return []
	stuck, total = 0, 0
	for policy in _enabled():
		alert = frappe.db.get_value(POLICY, policy.name, "toil_waiting_alert_days")
		waiting = [
			["company", "=", policy.company],
			["docstatus", "=", 0],
			["status", "in", ["Waiting for Authorisation", "Waiting for Approval"]],
		]
		total += frappe.db.count("Time Off in Lieu Claim", waiting)
		if not alert:
			continue
		stuck += frappe.db.count(
			"Time Off in Lieu Claim",
			[*waiting, ["sent_on", "is", "set"], ["sent_on", "<", add_days(now_datetime(), -int(alert))]],
		)
	if not stuck:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Some time off claims have waited a long time for a decision"),
		detail=_(
			"The approver may be away with nobody standing in. Their claims stay with them until decided."
		),
		count=stuck,
		total=total,
		state=State.STALE,
		link="/app/time-off-in-lieu-claim?status=Waiting%20for%20Approval",
	)


# ---------------------------------------------------------------- timesheet approval (1.16.0)


def _approval_companies() -> list[str]:
	if not frappe.db.table_exists(POLICY):
		return []
	return frappe.get_all(POLICY, filters={"timesheet_approval": 1}, pluck="company")


@health_check(label="Timesheets: approvers", category="Data", forms=FORMS)
def timesheets_have_approvers():
	"""Staff whose timesheets need approval, with nobody to approve them."""
	from seal_hrms.seal_hrms.timesheets.approval import approver_for

	companies = _approval_companies()
	if not companies:
		return []
	staff = frappe.get_all(
		"Employee", filters={"company": ["in", companies], "status": "Active"}, fields=["name", "company"]
	)
	stranded = sum(1 for person in staff if not approver_for(person.name, person.company))
	if not stranded:
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("Some staff cannot send their timesheets: nobody approves them"),
		detail=_(
			"Give them a leave approver (or a line manager with a login, where the line manager approves)."
		),
		count=stranded,
		total=len(staff),
		state=State.MISCONFIGURED,
		link="/app/employee",
	)


@health_check(label="Timesheets: waiting", category="Data", forms=FORMS)
def timesheets_waiting():
	"""Timesheets waiting for approval longer than the company allows."""
	from frappe.utils import add_days, now_datetime

	if not frappe.db.table_exists(POLICY) or not frappe.get_meta("Timesheet").has_field(
		"custom_approval_state"
	):
		return []
	stuck = total = 0
	for policy in frappe.get_all(
		POLICY, filters={"timesheet_approval": 1}, fields=["company", "timesheet_waiting_alert_days"]
	):
		waiting = [
			["company", "=", policy.company],
			["docstatus", "=", 0],
			["custom_approval_state", "=", "Waiting for Approval"],
		]
		total += frappe.db.count("Timesheet", waiting)
		if policy.timesheet_waiting_alert_days:
			stuck += frappe.db.count(
				"Timesheet",
				[
					*waiting,
					["custom_sent_on", "is", "set"],
					[
						"custom_sent_on",
						"<",
						add_days(now_datetime(), -int(policy.timesheet_waiting_alert_days)),
					],
				],
			)
	if not stuck:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Some timesheets have waited a long time for approval"),
		detail=_("The approver may be away with nobody standing in."),
		count=stuck,
		total=total,
		state=State.STALE,
		link="/app/timesheet?custom_approval_state=Waiting%20for%20Approval",
	)


@health_check(label="Time off in lieu: approval steps", category="Configuration", forms=FORMS)
def time_off_workflow_in_place():
	"""Claims move by a Frappe Workflow; without it, or with one missing a step, none can be sent."""
	if not _enabled():
		return []
	from seal_hrms.seal_hrms.toil.workflow import problems

	found = problems()
	if not found:
		return []
	return Finding(
		severity=Severity.BLOCKING,
		title=_("Time off claims cannot be sent or decided"),
		detail=" ".join(found)
		+ " "
		+ _("Running Migrate puts the standard steps back if there is no workflow."),
		count=len(found),
		state=State.MISCONFIGURED,
		link="/app/workflow?document_type=Time%20Off%20in%20Lieu%20Claim",
	)


@health_check(label="Timesheets: approval by workflow", category="Configuration", forms=FORMS)
def timesheet_approval_by_site_workflow():
	"""A company asks for timesheet approval, but the site approves timesheets with its own workflow."""
	from seal_hrms.seal_hrms.timesheets.approval import site_workflow

	companies = _approval_companies()
	workflow = site_workflow() if companies else None
	if not workflow:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Timesheets are approved by the site's own workflow"),
		detail=_(
			"The workflow {0} decides timesheets, so the approval set on this policy is not used for: {1}. "
			"Turn one of them off to avoid confusion."
		).format(workflow, ", ".join(companies)),
		count=len(companies),
		state=State.MISCONFIGURED,
		link=f"/app/workflow/{workflow}",
	)


@health_check(label="Timesheets: deadline and approval", category="Configuration", forms=FORMS)
def timesheet_cutoff_with_approval():
	"""A submission deadline on timesheets judges the approver's approval, not the person's sending.

	The deadline (seal_common's Document Submission Cutoff) checks the moment of
	submitting, and with approval that is when the approver approves, so a
	timesheet sent on time is refused if approved late. Until the deadline can
	count from when it was sent (an add-only seal_common change, decision D11),
	a company should not use both. `[unsupervised — review]`
	"""
	if not frappe.db.exists("DocType", "Document Submission Cutoff"):
		return []
	companies = _approval_companies()
	if not companies:
		return []
	clashing = frappe.get_all(
		"Document Submission Cutoff",
		filters={"document_type": "Timesheet", "company": ["in", companies], "enabled": 1},
		pluck="company",
	)
	if not clashing:
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("A timesheet deadline is on where timesheets need approval"),
		detail=_(
			"The deadline is checked when the approver approves, so timesheets sent on time can be refused. "
			"Turn the deadline off for: {0}."
		).format(", ".join(clashing)),
		count=len(clashing),
		state=State.MISCONFIGURED,
		link="/app/document-submission-cutoff",
	)
