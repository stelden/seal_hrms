# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Health checks for payout change requests, on App Health and on the request's form (SEAL_DEV_RULES §1.18),
and for staff reaching the My Desk phone app.

Two things go wrong quietly: a request nobody in HR decides (the person keeps being
paid to the old details, which may be a closed account), and a site whose
seal_common cannot ask for a fresh check, so a request is sent on the strength of a
session alone. Cheap: they run as the form opens.

seal_common is optional for seal_hrms, so its import is guarded; where it is absent
nothing reads these checks.
"""

import frappe
from frappe import _

try:
	from seal_common.app_health import Finding, Severity, State, health_check
except ImportError:  # pragma: no cover - only on sites without seal_common

	def health_check(*args, **kwargs):
		return lambda fn: fn


DOCTYPE = "Payout Change Request"
FORMS = (DOCTYPE,)
#: A request waiting longer than this many working days is reported (HR_ON_MY_DESK §2.7).
WAITING_DAYS = 3


@health_check(label="Payout changes waiting", category="Data", forms=FORMS)
def payout_changes_waiting():
	"""Requests waiting for HR more than three working days: the person is still paid the old way."""
	from seal_hrms.seal_hrms.payout_change import WAITING, working_days_ago

	if not frappe.db.table_exists(DOCTYPE):
		return []
	total = frappe.db.count(DOCTYPE, {"status": WAITING})
	if not total:
		return []
	stuck = frappe.db.count(
		DOCTYPE,
		[["status", "=", WAITING], ["sent_on", "is", "set"], ["sent_on", "<", working_days_ago(WAITING_DAYS)]],
	)
	if not stuck:
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Some payout changes have waited more than {0} working days").format(WAITING_DAYS),
		detail=_("Until HR approves or rejects them, these people are paid to their old details. An HR Manager decides each one."),
		count=stuck,
		total=total,
		state=State.STALE,
		link="/app/payout-change-request?status=Waiting%20for%20HR",
	)


@health_check(label="Payout changes: fresh check", category="Configuration", forms=FORMS)
def payout_change_without_fresh_check():
	"""Staff can send a payout change without proving who they are again: this site's SEAL Common cannot ask."""
	from seal_hrms.seal_hrms import step_up

	if not frappe.db.table_exists(DOCTYPE) or step_up.available():
		return []
	return Finding(
		severity=Severity.DEGRADED,
		title=_("Payout changes are sent without a fresh check of who is asking"),
		detail=_(
			"Anyone holding a signed-in session can ask for pay to go elsewhere; HR's approval and the notice to the "
			"old number are the only safeguards. Update SEAL Common to a release with step-up (1.35.0 or later)."
		),
		state=State.MISCONFIGURED,
	)


@health_check(label="Phone app for staff", category="Configuration")
def phone_app_needs_my_desk():
	"""Staff cannot get the My Desk phone app: this site has seal_hrms but not My Desk (seal_desk).

	A deployment rule, not a dependency (Keith, 2026-11-11): seal_desk goes on every site where
	staff should have the app, and seal_hrms never requires or imports it (SEAL_DEV_RULES §3.15).
	"""
	if "seal_desk" in frappe.get_installed_apps():
		return []
	return Finding(
		severity=Severity.ADVISORY,
		title=_("Staff cannot get the phone app: install My Desk"),
		detail=_(
			"My HR on the phone, approvals and HR notices reach staff through the My Desk app. Install My Desk "
			"(seal_desk) on this site so staff can use them."
		),
		state=State.MISSING,
	)
