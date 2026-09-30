# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Handover emails come from editable Email Templates; the pre-leave reminder goes once.

Frappe renders Jinja with DebugUndefined: a variable the code forgets to pass
is printed literally as "{{ name }}" rather than failing. So every shipped
template is rendered with the real context and checked for leftovers. An HR
edit must take effect, and a broken template must fall back rather than stop
the mail.
"""

import json
import pathlib
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from seal_hrms.seal_hrms import handover_jobs, handover_notifications as notes
from seal_hrms.tests import _handover_fixtures as fx


def _shipped():
	root = pathlib.Path(frappe.get_app_path("seal_hrms"))
	return json.loads((root / "fixtures" / "email_template.json").read_text())


class TestTemplates(IntegrationTestCase):
	def test_every_email_the_code_sends_ships_a_template(self):
		shipped = {t["name"] for t in _shipped()}
		self.assertEqual(shipped, set(notes.ALL_TEMPLATES))

	def test_every_email_the_code_sends_fills_its_template(self):
		"""Through the real senders, so a variable the CODE forgets to pass shows up as "{{ x }}"."""
		row = frappe._dict(description="Reconcile the Westlands petty cash", reference_type=None, reference_name=None,
		                   due_date=None, row_status="Handed Back", decline_reason=None)
		assignment = frappe._dict(
			doctype="Task Assignment", name="HR-TA-2610-00007", employee="HR-EMP-1", employee_name="Wanjiku Kamau",
			task_assignee_name="Otieno Ochieng", leave_from="2026-10-12", leave_to="2026-10-16",
			return_date="2026-10-19", return_summary="<p>Mwangi Hardware called twice.</p>",
			decline_reason="At the Kisumu audit", assignment_todos=[row], authorities=[],
		)
		leave = frappe._dict(name="HR-LAP-2026-00321", employee="HR-EMP-1", from_date="2026-10-12", to_date="2026-10-16")
		sent = []
		with patch.object(notes, "user_for_employee", return_value="wanjiku.kamau@kilimani-office.co.ke"), \
		     patch.object(frappe, "sendmail", side_effect=lambda **kw: sent.append(kw)), \
		     patch.object(notes, "render", wraps=notes.render) as rendered:
			notes.asked_to_cover(assignment, "HR-EMP-2", [row])
			notes.work_handed_over(assignment, "HR-EMP-2", [row])
			notes.answered(assignment, "Accepted")
			notes.answered(assignment, "Declined")
			notes.return_note_due(assignment, "HR-EMP-2")
			notes.welcome_back(assignment)
			notes.assignment_withdrawn(assignment, "HR-EMP-2")
			notes.prepare_your_handover(leave, "Wanjiku Kamau", 5)
			notes.stranded_work_returned(assignment, "a@kilimani-office.co.ke", ["Stock count"], to_owner=True)
			notes.stranded_work_returned(assignment, "b@kilimani-office.co.ke", ["Stock count"], to_owner=False)
		self.assertEqual({c.args[0] for c in rendered.call_args_list}, set(notes.ALL_TEMPLATES),
		                 "every template is used, and by its own sender")
		for mail in sent:
			for text in (mail["subject"], mail["message"]):
				self.assertNotIn("{{", text, f"{mail['subject']}: a variable was not passed")

	def test_user_text_is_escaped_before_it_reaches_a_template(self):
		context = notes._context(items=["<script>alert(1)</script>"])
		self.assertNotIn("<script>", context["items"][0])

	def test_an_hr_edit_takes_effect(self):
		name = notes.WITHDRAWN
		doc = frappe.get_doc("Email Template", name)
		original = doc.subject
		doc.subject = "Cover no longer needed: {{ employee_name }}"
		doc.save(ignore_permissions=True)
		try:
			subject, _ = notes.render(name, notes._context(employee_name="Wanjiku Kamau"), "fallback", "fallback")
			self.assertEqual(subject, "Cover no longer needed: Wanjiku Kamau")
		finally:
			doc.reload()
			doc.subject = original
			doc.save(ignore_permissions=True)

	def test_a_missing_or_broken_template_falls_back(self):
		self.assertEqual(notes.render("Task Assignment - Nonexistent", {}, "S", "M"), ("S", "M"))
		# A template that fails to render (a variable that raises, a filter gone) still sends the fallback.
		with patch.object(frappe, "render_template", side_effect=RuntimeError("bad filter")), \
		     patch.object(frappe, "log_error") as logged:
			self.assertEqual(notes.render(notes.WITHDRAWN, notes._context(), "S", "M"), ("S", "M"))
		self.assertTrue(logged.called)

	def test_hr_cannot_save_a_template_that_would_not_render(self):
		doc = frappe.get_doc("Email Template", notes.WITHDRAWN)
		doc.response = "{% for x in %}broken"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)


class TestPreLeaveReminder(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", fx.COMPANY):
			raise cls.skipTest(cls, f"{fx.COMPANY} is not on this site")
		cls.wanjiku = fx.ensure_employee("wanjiku")
		cls.otieno = fx.ensure_employee("otieno")
		cls.wanjiku_user = fx.email("wanjiku")

	def setUp(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno])
		self._drop_policy()

	def tearDown(self):
		frappe.set_user("Administrator")
		fx.cleanup([self.wanjiku, self.otieno])
		self._drop_policy()

	def _drop_policy(self):
		if frappe.db.exists("Task Assignment Policy", fx.COMPANY):
			frappe.delete_doc("Task Assignment Policy", fx.COMPANY, force=1, ignore_permissions=True)

	def _policy(self, email=1, days=7):
		doc = frappe.new_doc("Task Assignment Policy")
		doc.company = fx.COMPANY
		doc.requirement = "Off"  # the reminder does not depend on the approval rule
		doc.prep_reminder_days = days
		doc.email_prep_reminder = email
		doc.insert(ignore_permissions=True)

	def _mail_to(self, user):
		return frappe.db.count("Email Queue Recipient", {"recipient": user})

	def test_leave_coming_up_with_nobody_covering_is_reminded_once(self):
		self._policy()
		la = fx.leave(self.wanjiku, 4, 3)
		before = self._mail_to(self.wanjiku_user)
		self.assertEqual(handover_jobs.remind_to_prepare(), [la.name])
		self.assertGreater(self._mail_to(self.wanjiku_user), before)
		self.assertEqual(handover_jobs.remind_to_prepare(), [], "once per leave (§3.7)")

	def test_no_reminder_once_a_handover_exists(self):
		self._policy()
		la = fx.leave(self.wanjiku, 4, 3)
		fx.handover(self.wanjiku, self.otieno, la, [{"description": "Stock count"}], submit=False)
		self.assertEqual(handover_jobs.remind_to_prepare(), [])

	def test_no_reminder_beyond_the_window_or_with_the_email_off(self):
		self._policy(days=7)
		far = fx.leave(self.wanjiku, 20, 2)
		self.assertNotIn(far.name, handover_jobs.remind_to_prepare())
		self._drop_policy()
		self._policy(email=0)
		near = fx.leave(self.wanjiku, 3, 2)
		self.assertNotIn(near.name, handover_jobs.remind_to_prepare())

	def test_a_company_with_no_policy_gets_no_email(self):
		la = fx.leave(self.wanjiku, 3, 2)
		self.assertNotIn(la.name, handover_jobs.remind_to_prepare())
