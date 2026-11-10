# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Payout Change Request (seal_hrms/seal_hrms/payout_change.py, HR_ON_MY_DESK.md §2.7).

Otieno asks to be paid into a new account at his bank, or to a new Safaricom number.
Halima Abdi is the HR Manager who confirms (an HR officer with no employee record of her
own here, so no User Permission ties her to one); Njeri is a colleague. Pinned: staff ask only
for themselves and see only their own; sending needs the evidence, a name that
matches and (where the site can) a fresh check, and tells the old number and address;
nothing on the employee record moves until an HR Manager who is not the requester
approves; the old bank account is kept; a refusal needs a reason.

Before the site is migrated the DocType is borrowed into a temporary table
(`_borrowed_doctype`); no SMS or email leaves the process.
"""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.utils import add_days, today

from seal_hrms.seal_hrms import payout_change as pc
from seal_hrms.tests import _handover_fixtures as fx
from seal_hrms.tests._borrowed_doctype import borrow
from seal_hrms.tests.test_toil_claim import ToilTestCase

BANK = "Kilimani Cooperative Bank"
OLD_ACCOUNT = "01109384756200"
NEW_ACCOUNT = "01109384756311"
NEW_NUMBER = "0712 345 678"
HR_USER = "halima.abdi@kilimani-office.co.ke"
TEXT_JOB = "seal_hrms.seal_hrms.payout_change.send_text_notice"


class PayoutChangeTestCase(ToilTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		borrow(pc.DOCTYPE, frappe.get_app_path("seal_hrms", "seal_hrms", "doctype", "payout_change_request", "payout_change_request.json"), cls)
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.hr_user = HR_USER
		if not frappe.db.exists("User", HR_USER):
			user = frappe.new_doc("User")
			user.update({"email": HR_USER, "first_name": "Halima", "last_name": "Abdi", "send_welcome_email": 0})
			user.insert(ignore_permissions=True)
		frappe.get_doc("User", HR_USER).add_roles("HR Manager")

	def setUp(self):
		super().setUp()
		self.sent_mail, self.queued = [], []
		for target, record in (("frappe.sendmail", self.sent_mail), ("frappe.enqueue", self.queued)):
			p = patch(target, side_effect=lambda *a, _r=record, **k: _r.append({**k, "args": a}))
			p.start()
			self.addCleanup(p.stop)
		self.addCleanup(frappe.clear_cache, user=self.hr_user)
		if not frappe.db.exists("Bank", BANK):
			frappe.get_doc({"doctype": "Bank", "bank_name": BANK}).insert(ignore_permissions=True)
		self.old_account = self._account(OLD_ACCOUNT)

	def _account(self, number):
		account = frappe.new_doc("Bank Account")
		account.update({"account_name": "Otieno Ochieng", "bank": BANK, "bank_account_no": number, "party_type": "Employee", "party": self.otieno, "is_default": 1})
		account.insert(ignore_permissions=True)
		emp = frappe.get_doc("Employee", self.otieno)
		emp.custom_salary_bank_account = account.name
		emp.save(ignore_permissions=True)
		return account.name

	def _request(self, change="Bank Account", as_user=None, **values):
		doc = frappe.new_doc(pc.DOCTYPE)
		doc.employee = self.otieno
		# Permission is checked before links fetch, so a blank company would be the creator's default.
		doc.company = frappe.db.get_value("Employee", self.otieno, "company")
		doc.change = change
		if change == "Bank Account":
			doc.update({"bank": BANK, "bank_account_no": NEW_ACCOUNT, "account_name": "Otieno Ochieng", "evidence": "/private/files/otieno-bank-letter.pdf"})
		else:
			doc.mobile_no = NEW_NUMBER
		doc.reason = "Moved my salary account to the Westlands branch"
		doc.update(values)
		fx.as_user(as_user or self.otieno_user, doc.insert)
		return doc

	def _sent(self, change="Bank Account", **values):
		doc = self._request(change, **values)
		fx.as_user(self.otieno_user, pc.send, doc.name)
		doc.reload()
		return doc


class TestAsking(PayoutChangeTestCase):
	def test_staff_ask_only_for_themselves(self):
		doc = frappe.new_doc(pc.DOCTYPE)
		doc.employee = self.wanjiku
		doc.company = frappe.db.get_value("Employee", self.wanjiku, "company")
		doc.change = "Mobile Money"
		doc.mobile_no = NEW_NUMBER
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, doc.insert)

	def test_a_colleague_cannot_see_or_send_it(self):
		doc = self._request()
		self.assertFalse(fx.as_user(self.njeri_user, frappe.has_permission, pc.DOCTYPE, "read", doc.name))
		self.assertNotIn(doc.name, fx.as_user(self.njeri_user, frappe.get_list, pc.DOCTYPE, pluck="name"))
		self.assertIn(doc.name, fx.as_user(self.otieno_user, frappe.get_list, pc.DOCTYPE, pluck="name"))
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, pc.send, doc.name)

	def test_a_mobile_number_is_checked_and_its_provider_found(self):
		doc = self._request("Mobile Money")
		self.assertEqual(doc.mobile_no, "254712345678")
		with self.assertRaises(frappe.ValidationError):
			self._request("Mobile Money", mobile_no="0812 99")

	def test_a_bank_change_needs_evidence(self):
		doc = self._request(evidence=None)
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, pc.send, doc.name)
		self.assertIn("Evidence", str(caught.exception))

	def test_the_account_must_be_in_their_name(self):
		doc = self._request(account_name="Kamau Hardware Supplies")
		with self.assertRaises(frappe.ValidationError) as caught:
			fx.as_user(self.otieno_user, pc.send, doc.name)
		self.assertIn("does not match", str(caught.exception))
		self.assertTrue(pc.names_match("OTIENO OCHIENG", "Otieno Ochieng"))
		self.assertTrue(pc.names_match("Ochieng Otieno B", "Otieno Ochieng"))
		self.assertFalse(pc.names_match("Otieno Kamau", "Otieno Ochieng"))

	def test_sending_snapshots_and_tells_the_old_number_old_address_and_hr(self):
		doc = self._sent()
		self.assertEqual(doc.status, pc.WAITING)
		self.assertEqual((doc.previous_bank_account, doc.previous_bank_account_no), (self.old_account, OLD_ACCOUNT))
		old_number = doc.previous_mobile_no
		self.assertTrue(old_number)
		texts = [q for q in self.queued if q["args"] and q["args"][0] == TEXT_JOB]
		self.assertEqual([q.get("number") for q in texts], [old_number])
		self.assertTrue(all(q.get("enqueue_after_commit") for q in texts))
		recipients = [r for m in self.sent_mail for r in m["recipients"]]
		self.assertIn(self.otieno_user, recipients)
		self.assertIn(self.hr_user, recipients)
		notice = next(m for m in self.sent_mail if self.otieno_user in m["recipients"])
		self.assertNotIn(NEW_ACCOUNT, notice["message"], "the notice never names the new details")
		self.assertTrue(frappe.db.exists("Notification Log", {"for_user": self.hr_user, "document_name": doc.name}))
		# Nothing is paid differently yet.
		self.assertEqual(frappe.db.get_value("Employee", self.otieno, "custom_salary_bank_account"), self.old_account)

	def test_a_sent_request_cannot_be_edited(self):
		doc = self._sent()
		doc.bank_account_no = "99999999999"
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, doc.save)

	def test_status_cannot_be_set_by_hand(self):
		doc = self._request()
		doc.status = pc.APPROVED
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.otieno_user, doc.save)

	def test_one_request_waiting_at_a_time(self):
		self._sent()
		second = self._request("Mobile Money")
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.otieno_user, pc.send, second.name)

	def test_sending_asks_for_a_fresh_check_where_the_site_can(self):
		doc = self._request()

		class Stale(frappe.PermissionError):
			pass

		recent = SimpleNamespace(is_recent=lambda minutes: False, VerificationNeeded=Stale)
		with patch("seal_hrms.seal_hrms.step_up._recent", return_value=recent):
			with self.assertRaises(Stale):
				fx.as_user(self.otieno_user, pc.send, doc.name)
		recent.is_recent = lambda minutes: True
		with patch("seal_hrms.seal_hrms.step_up._recent", return_value=recent):
			fx.as_user(self.otieno_user, pc.send, doc.name)
		self.assertEqual(frappe.db.get_value(pc.DOCTYPE, doc.name, "status"), pc.WAITING)


class TestDeciding(PayoutChangeTestCase):
	def test_only_an_hr_manager_decides(self):
		doc = self._sent()
		for user in (self.njeri_user, self.otieno_user):
			with self.assertRaises(frappe.PermissionError):
				fx.as_user(user, pc.approve, doc.name)

	def test_an_hr_manager_cannot_approve_their_own(self):
		frappe.get_doc("User", self.otieno_user).add_roles("HR Manager")
		doc = self._sent()
		with self.assertRaises(frappe.PermissionError) as caught:
			fx.as_user(self.otieno_user, pc.approve, doc.name)
		self.assertIn("about you", str(caught.exception))

	def test_approving_a_bank_change_keeps_the_old_account(self):
		doc = self._sent()
		fx.as_user(self.hr_user, pc.approve, doc.name)
		doc.reload()
		self.assertEqual(doc.status, pc.APPROVED)
		self.assertTrue(doc.applied_on)
		new = frappe.db.get_value("Employee", self.otieno, "custom_salary_bank_account")
		self.assertEqual(new, doc.new_bank_account)
		self.assertEqual(frappe.db.get_value("Bank Account", new, ["bank_account_no", "is_default", "party"]), (NEW_ACCOUNT, 1, self.otieno))
		self.assertTrue(frappe.db.exists("Bank Account", self.old_account), "the old account is kept")
		self.assertEqual(frappe.db.get_value("Bank Account", self.old_account, "is_default"), 0)
		self.assertTrue(any(self.otieno_user in m["recipients"] for m in self.sent_mail[-1:]))

	def test_approving_a_mobile_change_sets_the_contact_and_cell_number(self):
		contact = frappe.db.get_value("Employee", self.otieno, "custom_contact")
		if not contact:
			self.skipTest("Otieno has no contact on this site")
		doc = self._sent("Mobile Money")
		fx.as_user(self.hr_user, pc.approve, doc.name)
		self.assertEqual(frappe.db.get_value("Contact", contact, "mobile_no"), "254712345678")
		self.assertEqual(frappe.db.get_value("Employee", self.otieno, "cell_number"), "254712345678")

	def test_a_later_date_waits_for_the_daily_pass(self):
		doc = self._sent()
		later = add_days(today(), 5)
		fx.as_user(self.hr_user, pc.approve, doc.name, later)
		doc.reload()
		self.assertFalse(doc.applied_on)
		self.assertEqual(frappe.db.get_value("Employee", self.otieno, "custom_salary_bank_account"), self.old_account)
		self.assertEqual(pc.apply_due([doc.name]), [])
		with patch.object(pc, "today", return_value=later):
			self.assertEqual(pc.apply_due([doc.name]), [doc.name])
		self.assertEqual(frappe.db.get_value("Employee", self.otieno, "custom_salary_bank_account"), frappe.db.get_value(pc.DOCTYPE, doc.name, "new_bank_account"))

	def test_a_past_date_is_refused(self):
		doc = self._sent()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.hr_user, pc.approve, doc.name, add_days(today(), -1))

	def test_rejecting_needs_a_reason_and_changes_nothing(self):
		doc = self._sent()
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.hr_user, pc.reject, doc.name, "  ")
		fx.as_user(self.hr_user, pc.reject, doc.name, "The letter is for a different account number")
		doc.reload()
		self.assertEqual((doc.status, doc.decision_note), (pc.REJECTED, "The letter is for a different account number"))
		self.assertEqual(frappe.db.get_value("Employee", self.otieno, "custom_salary_bank_account"), self.old_account)
		self.assertTrue(frappe.db.exists("Notification Log", {"for_user": self.otieno_user, "document_name": doc.name}))

	def test_a_decided_request_is_not_decided_again(self):
		doc = self._sent()
		fx.as_user(self.hr_user, pc.reject, doc.name, "Wrong branch code")
		with self.assertRaises(frappe.ValidationError):
			fx.as_user(self.hr_user, pc.approve, doc.name)

	def test_the_requester_withdraws_and_others_cannot(self):
		doc = self._sent()
		with self.assertRaises(frappe.PermissionError):
			fx.as_user(self.njeri_user, pc.withdraw, doc.name)
		fx.as_user(self.otieno_user, pc.withdraw, doc.name)
		self.assertEqual(frappe.db.get_value(pc.DOCTYPE, doc.name, "status"), pc.WITHDRAWN)

	def test_hr_sees_the_waiting_figure_and_staff_do_not(self):
		self._sent()
		figure = fx.as_user(self.hr_user, pc.waiting_figure, self.hr_user)
		self.assertGreaterEqual(figure.value, 1)
		self.assertIsNone(pc.waiting_figure(self.njeri_user))


class TestHealth(PayoutChangeTestCase):
	def test_a_request_waiting_long_is_reported(self):
		from seal_hrms.health import my_desk

		doc = self._sent()
		frappe.db.set_value(pc.DOCTYPE, doc.name, "sent_on", add_days(today(), -10), update_modified=False)
		finding = my_desk.payout_changes_waiting()
		self.assertTrue(finding and finding.count >= 1)

	def test_working_days_skip_weekends(self):
		self.assertEqual(str(pc.working_days_ago(3, "2026-11-10")), "2026-11-05")  # a Tuesday: back past the weekend

	def test_no_fresh_check_is_reported(self):
		from seal_hrms.health import my_desk

		with patch("seal_hrms.seal_hrms.step_up._recent", return_value=None):
			self.assertTrue(my_desk.payout_change_without_fresh_check())
		with patch("seal_hrms.seal_hrms.step_up._recent", return_value=SimpleNamespace()):
			self.assertEqual(my_desk.payout_change_without_fresh_check(), [])
