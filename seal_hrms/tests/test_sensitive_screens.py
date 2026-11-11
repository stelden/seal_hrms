# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Screens that ask "is it still you?" first (seal_hrms/seal_hrms/sensitive.py; Keith, 2026-11-11).

Baraka Mutua's phone is left signed in on a desk (`_phone_cast`). Pinned: a session not checked lately is
refused his payslips (list, slip and PDF) and his payout request, and My Details holds back
where he is paid; a freshly checked one sees them; a screen HR turns off in SEAL HRMS Settings
shows without asking; a switch never saved reads as on; the check lasts as long as the
setting says; and App Health speaks up where the site cannot ask at all.

seal_common's step-up is replaced by a stand-in (`step_up._recent`), so these run whichever
seal_common is on the path. Rows are rolled back per test. Also here: every amount the phone
shows or asks for is in the company's own currency (Wairimu Gitau, at a company keeping its
books in Kenya shillings).
"""

from types import SimpleNamespace
from unittest.mock import patch

import frappe

from seal_hrms.my_desk import api
from seal_hrms.seal_hrms import sensitive
from seal_hrms.tests._phone_cast import CastTestCase, as_user, person


class NeedsCheck(frappe.PermissionError):
	"""Stands in for seal_common's VerificationNeeded."""


class SensitiveTestCase(CastTestCase):
	def setUp(self):
		super().setUp()
		self.asked = []  # the minutes each check was asked for
		self.fresh = False
		recent = SimpleNamespace(is_recent=self._is_recent, VerificationNeeded=NeedsCheck)
		p = patch("seal_hrms.seal_hrms.step_up._recent", return_value=recent)
		p.start()
		self.addCleanup(p.stop)

	def _is_recent(self, minutes):
		self.asked.append(minutes)
		return self.fresh

	def as_baraka(self, fn, *args, **kwargs):
		return as_user(self.baraka_user, fn, *args, **kwargs)

	def _set(self, **values):
		for field, value in values.items():
			frappe.db.set_single_value(sensitive.SETTINGS, field, value)

	def _forget(self, *fields):
		"""As on a site that has never saved these switches (no row at all)."""
		frappe.db.delete("Singles", {"doctype": sensitive.SETTINGS, "field": ["in", list(fields)]})


class TestPayslips(SensitiveTestCase):
	def test_a_stale_session_is_refused_every_payslip_screen(self):
		for fn, args in ((api.payslips, ()), (api.payslip_record, ("Sal Slip/HR-EMP-00031/00010",)), (api.payslip_pdf, ("Sal Slip/HR-EMP-00031/00010",))):
			with self.subTest(fn=fn.__name__), self.assertRaises(NeedsCheck):
				self.as_baraka(fn, *args)

	def test_a_fresh_session_sees_them(self):
		self.fresh = True
		self.assertIsInstance(self.as_baraka(api.payslips), list)

	def test_off_in_settings_shows_without_asking(self):
		self._set(confirm_before_payslips=0)
		self.assertIsInstance(self.as_baraka(api.payslips), list)
		self.assertEqual(self.asked, [])

	def test_the_check_lasts_as_long_as_the_setting_says(self):
		self._set(confirm_window_minutes=2)
		self.fresh = True
		self.as_baraka(api.payslips)
		self.assertEqual(self.asked, [2])
		self._set(confirm_window_minutes=500)  # out of bounds: held to the longest allowed
		self.as_baraka(api.payslips)
		self.assertEqual(self.asked[-1], sensitive.MAX_MINUTES)

	def test_confirm_screen_is_how_the_phone_asks_before_a_pdf(self):
		with self.assertRaises(NeedsCheck):
			self.as_baraka(api.confirm_screen, sensitive.PAYSLIPS)
		self.fresh = True
		self.assertEqual(self.as_baraka(api.confirm_screen, sensitive.PAYSLIPS), {"ok": True})
		with self.assertRaises(frappe.ValidationError):
			self.as_baraka(api.confirm_screen, "salary_register")


class TestPayoutDetails(SensitiveTestCase):
	def test_my_details_holds_back_where_pay_goes_until_checked(self):
		stale = self.as_baraka(api.my_details)
		self.assertTrue(stale["payout_locked"])
		self.assertIsNone(stale["payout"])
		self.assertEqual(stale["payout_requests"], [])
		self.assertEqual(stale["employee"]["name"], self.baraka)  # the rest of the screen still shows
		self.fresh = True
		fresh = self.as_baraka(api.my_details)
		self.assertFalse(fresh["payout_locked"])
		self.assertIn("bank", fresh["payout"])

	def test_a_payout_request_is_refused_to_a_stale_session(self):
		with self.assertRaises(NeedsCheck):
			self.as_baraka(api.payout_request_record, "PCR-2026-00001")

	def test_off_in_settings_shows_without_asking(self):
		self._set(confirm_before_payout_details=0)
		self.assertFalse(self.as_baraka(api.my_details)["payout_locked"])


class TestTheSettings(SensitiveTestCase):
	def test_a_switch_never_saved_reads_as_on(self):
		self._forget(*sensitive.DEFAULTS)
		self.assertTrue(sensitive.asks(sensitive.PAYSLIPS))
		self.assertTrue(sensitive.asks(sensitive.PAYOUT_DETAILS))
		self.assertEqual(sensitive.minutes(), 5)
		with self.assertRaises(NeedsCheck):
			self.as_baraka(api.payslips)

	def test_seeding_writes_only_what_was_never_saved(self):
		self._forget(*sensitive.DEFAULTS)
		self._set(confirm_before_payslips=0)
		sensitive.seed_defaults()
		# Read raw: before the site is migrated the form's meta does not know these fields yet.
		self.assertEqual(sensitive._saved(), {"confirm_before_payslips": "0", "confirm_before_payout_details": "1", "confirm_window_minutes": "5"})

	def test_the_form_refuses_a_check_longer_than_an_hour(self):
		doc = frappe.get_doc(sensitive.SETTINGS)
		doc.confirm_window_minutes = 90
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)


class TestAppHealth(SensitiveTestCase):
	def test_said_when_the_site_cannot_ask(self):
		from seal_hrms.health import my_desk

		with patch("seal_hrms.seal_hrms.step_up._recent", return_value=None):
			self.assertEqual(sorted(sensitive.unprotected()), sorted(sensitive.SWITCHES))
			finding = my_desk.sensitive_screens_without_a_check()
			self.assertTrue(finding)
			# and with nothing set to ask, nothing to say
			self._set(confirm_before_payslips=0, confirm_before_payout_details=0)
			self.assertEqual(my_desk.sensitive_screens_without_a_check(), [])
		self.assertEqual(sensitive.unprotected(), [])


class TestAmountsInTheCompanysCurrency(CastTestCase):
	"""Keith saw "Amount (INR)" on dev.local: its _Test Company really keeps INR. Every amount label and
	figure takes the person's company's currency (or the record's own), never a fixed or system one."""

	def test_a_kenya_shilling_company_asks_and_shows_in_kes(self):
		company = frappe.db.get_value("Company", {"default_currency": "KES"}, "name")
		if not company:
			self.skipTest("no company keeping Kenya shillings on this site")
		user, _employee = person("wairimu", company=company)
		self.assertEqual(as_user(user, api.expense_options)["currency"], "KES")
		self.assertEqual(as_user(user, api.travel_options)["currency"], "KES")
		self.assertEqual(api._currency(company), "KES")
		# _Test Company, by contrast, is what Keith saw.
		self.assertEqual(as_user(self.baraka_user, api.expense_options)["currency"], frappe.get_cached_value("Company", "_Test Company", "default_currency"))
