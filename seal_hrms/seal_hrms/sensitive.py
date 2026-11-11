# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Screens that ask "is it still you?" before they show anything (Keith, 2026-11-11).

A phone left unlocked on a desk is signed in. Payslips and where a person is paid are
the screens a colleague should not be able to read off it, so the server refuses to
send them unless the session proved who holds it in the last few minutes (seal_common's
step-up, through `step_up`). The phone answers the refusal by asking for a fingerprint
or the password, then reads again.

Which screens ask, and how long one check lasts, are SEAL HRMS Settings ("Confirm It Is
You" section). Both screens ask by default. A Check added to an existing Single reads 0
until the site saves it, so a switch never saved here counts as its default (on), and
patch `v1_27.seed_sensitive_screen_defaults` writes the defaults on sites that predate it.

Where the site cannot ask (no seal_common, or one without step-up) the screens show as
before and App Health says so (`health/my_desk.sensitive_screens_without_a_check`).
"""

from __future__ import annotations

import frappe
from frappe.utils import cint

from seal_hrms.seal_hrms import step_up

SETTINGS = "SEAL HRMS Settings"
PAYSLIPS, PAYOUT_DETAILS = "payslips", "payout_details"
#: screen -> the settings switch that makes it ask
SWITCHES = {PAYSLIPS: "confirm_before_payslips", PAYOUT_DETAILS: "confirm_before_payout_details"}
WINDOW = "confirm_window_minutes"
#: what a switch or the window reads as until the site saves it
DEFAULTS = {"confirm_before_payslips": 1, "confirm_before_payout_details": 1, WINDOW: step_up.MINUTES}
#: the shortest and longest a check may last, whatever is typed
MIN_MINUTES, MAX_MINUTES = 1, 60


def _saved() -> dict:
	"""The raw saved values: a field never saved has no row at all (unlike get_single_value's 0)."""
	rows = frappe.db.sql(
		"select field, value from `tabSingles` where doctype=%s and field in %s",
		(SETTINGS, tuple(DEFAULTS)),
	)
	return dict(rows)


def setting(field: str):
	"""A switch or the window as the site set it, else its default."""
	saved = _saved()
	value = saved.get(field)
	if value in (None, ""):
		return DEFAULTS[field]
	return cint(value)


def asks(screen: str) -> bool:
	"""Whether `screen` is set to ask for a fresh check (whether or not the site can ask)."""
	return bool(setting(SWITCHES[screen]))


def minutes() -> int:
	"""How long one check lasts for these screens, kept within sensible bounds."""
	return min(max(cint(setting(WINDOW)) or step_up.MINUTES, MIN_MINUTES), MAX_MINUTES)


def require(screen: str) -> None:
	"""Refuse to show `screen` unless the session was checked lately, where the setting asks and the site can.

	:raises seal_common.otp.recent.VerificationNeeded: the phone asks the person, then reads again.
	"""
	if asks(screen):
		step_up.require_fresh_check(minutes())


def is_fresh(screen: str) -> bool:
	"""Whether `screen` may be shown now (no check asked, the site cannot ask, or the check is recent)."""
	if not asks(screen):
		return True
	try:
		step_up.require_fresh_check(minutes())
	except frappe.PermissionError:
		frappe.clear_last_message()
		return False
	return True


def unprotected() -> list[str]:
	"""The screens set to ask that are shown without a check because the site cannot ask."""
	if step_up.available():
		return []
	return [screen for screen in SWITCHES if asks(screen)]


def seed_defaults() -> None:
	"""Write each default the site has never saved, so the form shows what the server does."""
	saved = _saved()
	for field, value in DEFAULTS.items():
		if saved.get(field) in (None, ""):
			frappe.db.set_single_value(SETTINGS, field, value)
