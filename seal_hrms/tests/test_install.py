# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A new site gets what a migrated site gets.

Records a site may change afterwards (the claims workflow, the email templates,
the Self Service list) are created by code, not shipped as fixtures, and that
code ran only after migrate: a brand-new site had none of them until its first
migrate (found 1.20.0). They now also run on install, from `after_sync`, which
Frappe runs after the app's fixtures; `after_install` runs before them
(SEAL_DEV_RULES §2.24). These tests keep the hooks in step and the steps
repeatable.
"""

import unittest

import frappe

APP = "seal_hrms"
CLAIM = "Time Off in Lieu Claim"


def _hook(name: str) -> list[str]:
	value = frappe.get_hooks(name, app_name=APP) or []
	return [value] if isinstance(value, str) else list(value)


class TestANewSiteIsSetUp(unittest.TestCase):
	def test_every_migrate_step_also_runs_on_install(self):
		on_install = set(_hook("after_install")) | set(_hook("after_sync"))
		self.assertEqual([step for step in _hook("after_migrate") if step not in on_install], [])

	def test_install_steps_that_need_fixtures_run_after_them(self):
		# after_install runs before fixtures sync: only the permission-level repair, which
		# reads the Employee doctype alone, may run there.
		self.assertEqual(
			_hook("after_install"), ["seal_hrms.seal_hrms.employee_permissions.ensure_employee_permlevels"]
		)

	def test_every_step_resolves(self):
		for step in {*_hook("after_install"), *_hook("after_sync"), *_hook("after_migrate")}:
			with self.subTest(step=step):
				self.assertTrue(callable(frappe.get_attr(step)))


class TestSelfServiceOnASiteWithNoCustomPermissions(unittest.TestCase):
	"""The fresh-site failure of 1.20.0: the claim not yet customised, nor on the Self Service list."""

	SAVEPOINT = "seal_hrms_test_install"

	def setUp(self):
		from seal_hrms.seal_hrms.working_time import user_type

		if not frappe.db.exists("User Type", user_type.USER_TYPE):
			self.skipTest("this site has no Self Service user type")
		self.user_type = user_type
		frappe.set_user("Administrator")
		frappe.db.savepoint(self.SAVEPOINT)
		frappe.db.before_commit.add(self._refuse_commit)

	def tearDown(self):
		frappe.db.before_commit.reset()
		frappe.db.rollback(save_point=self.SAVEPOINT)
		frappe.clear_cache(doctype=CLAIM)

	@staticmethod
	def _refuse_commit():
		raise AssertionError("a commit here would make the test's changes permanent")

	def test_the_claim_is_listed_without_an_error(self):
		frappe.db.delete("User Document Type", {"parent": self.user_type.USER_TYPE, "document_type": CLAIM})
		frappe.db.delete("Custom DocPerm", {"parent": CLAIM})
		errors = frappe.db.count("Error Log")
		self.user_type.allow_claims_for_self_service()
		self.assertEqual(frappe.db.count("Error Log"), errors, "the step logged a failure")
		self.assertTrue(
			frappe.db.exists(
				"User Document Type", {"parent": self.user_type.USER_TYPE, "document_type": CLAIM}
			)
		)
