# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What this app is allowed to change on doctypes it does not own.

ToDo belongs to Frappe. Ticking `reqd` on one of its fields in Customize Form
is a one-click edit whose blast radius is every app on the bench and the
framework itself -- `assign_to.add`, anything built on assignment, and Frappe's
own test-record preload, which inserts a ToDo with no assigner.

That last one is why this file exists rather than a note in a review: with
`assigned_by` mandatory, `bench run-tests --module` died in the preload before
loading a single test for ANY doctype whose dependency graph reaches ToDo. The
failure said "[ToDo, xxxx]: assigned_by" and named neither the suite it killed
nor the app that caused it, so suites across this bench sat unrunnable and the
cause looked like a bench problem.

See `patches/v1_10/restore_todo_assigned_by_optional.py`.
"""

import json
import os
import unittest

import frappe

#: Doctypes this app customises but does not own, and the properties it must
#: never tighten on them. Reads are fine; requiring a value is not, because the
#: writers are code this app has never seen.
FOREIGN_DOCTYPES = {
	"ToDo": ("reqd", "mandatory_depends_on"),
}


def _export_path(doctype: str) -> str:
	return os.path.join(
		frappe.get_app_path("seal_hrms"), "seal_hrms", "custom",
		frappe.scrub(doctype) + ".json",
	)


class TestNoMandatoryTicksOnForeignDoctypes(unittest.TestCase):

	def test_the_shipped_export_tightens_nothing(self):
		for doctype, properties in FOREIGN_DOCTYPES.items():
			path = _export_path(doctype)
			if not os.path.exists(path):
				continue
			with open(path, encoding="utf-8") as fh:
				export = json.load(fh)
			offenders = [
				ps["name"] for ps in export.get("property_setters", [])
				if ps.get("property") in properties and str(ps.get("value")) not in ("0", "", "None")
			]
			self.assertEqual(
				offenders, [],
				f"{doctype} is Frappe's, and code this app has never seen writes "
				f"it. Making a field mandatory there breaks those writers, not "
				f"ours: {offenders}",
			)

	def test_the_site_agrees_with_the_export(self):
		"""Removing the entry from the export does not delete the record a
		previous migrate created -- which is what the patch is for."""
		for doctype, properties in FOREIGN_DOCTYPES.items():
			live = frappe.get_all(
				"Property Setter",
				filters={"doc_type": doctype, "property": ["in", list(properties)]},
				fields=["name", "field_name", "property", "value"],
			)
			offenders = [
				r for r in live if str(r.value) not in ("0", "", "None")
			]
			self.assertEqual(
				offenders, [],
				f"a mandatory tick is still live on {doctype}; the export was "
				f"cleaned but the record was not removed: {offenders}",
			)

	def test_a_todo_can_still_be_raised_without_an_assigner(self):
		"""The shape Frappe's own preload uses, and `assign_to` before it
		stamps: a bare ToDo with a description."""
		todo = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Confirm the payroll cut-off with Wote finance",
		})
		todo.insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc(
			"ToDo", todo.name, force=True, ignore_permissions=True,
		))
		self.assertTrue(todo.name)


def run_all():
	suite = unittest.TestLoader().loadTestsFromModule(
		__import__(__name__, fromlist=["*"])
	)
	result = unittest.TextTestRunner(verbosity=1).run(suite)
	if not result.wasSuccessful():
		raise SystemExit(1)
