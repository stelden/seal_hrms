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
