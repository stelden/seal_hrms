# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A fresh check before a sensitive action (My Desk SIGN_IN.md §6), where the site has one.

seal_common's step-up (`seal_common.otp.recent`, 1.35.0) refuses a session whose
holder has not proved who they are in the last few minutes; the phone and the desk
answer by asking for a fingerprint or the password, then try again. seal_common is
optional for seal_hrms and older releases have no step-up, so the import is guarded:
where it is missing the action goes ahead and App Health says so
(`health/my_desk.payout_change_without_fresh_check`).
"""

import frappe

MINUTES = 5


def _recent():
	if "seal_common" not in frappe.get_installed_apps():
		return None
	try:
		from seal_common.otp import recent
	except ImportError:
		return None
	return recent


def available() -> bool:
	"""Whether this site can ask for a fresh check at all."""
	return _recent() is not None


def require_fresh_check(minutes: int = MINUTES) -> bool:
	"""Refuse unless the session was verified within `minutes`. False when the site has no step-up.

	:raises seal_common.otp.recent.VerificationNeeded: the session must prove who holds it again.
	"""
	recent = _recent()
	if recent is None:
		return False
	if not recent.is_recent(minutes):
		raise recent.VerificationNeeded(frappe._("Confirm it is you to continue."))
	return True
