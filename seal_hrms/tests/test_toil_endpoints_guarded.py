# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Every whitelisted function in the time off code checks its caller first (SEAL_DEV_RULES §2.15).

Read from the source (AST), so a new endpoint that forgets fails here, and from
`frappe.whitelisted` (§2.13), so the list of endpoints is Frappe's own.
"""

import ast
import importlib
import inspect
import pathlib
import textwrap
import unittest

import frappe

PACKAGES = ("toil", "working_time")
GUARDS = {"require_self_or_hr", "require_decider"}


def _modules():
	root = pathlib.Path(frappe.get_app_path("seal_hrms", "seal_hrms"))
	for package in PACKAGES:
		for path in sorted((root / package).glob("*.py")):
			if path.name != "__init__.py":
				yield importlib.import_module(f"seal_hrms.seal_hrms.{package}.{path.stem}")


def _calls(fn) -> set[str]:
	tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
	names = set()
	for node in ast.walk(tree):
		if isinstance(node, ast.Call):
			func = node.func
			names.add(func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", ""))
	return names


class TestEndpointsAreGuarded(unittest.TestCase):
	def test_every_whitelisted_function_calls_a_guard(self):
		endpoints, unguarded = [], []
		for module in _modules():
			for name, fn in inspect.getmembers(module, inspect.isfunction):
				if fn.__module__ != module.__name__ or fn not in frappe.whitelisted:
					continue
				endpoints.append(f"{module.__name__}.{name}")
				if not _calls(fn) & GUARDS:
					unguarded.append(f"{module.__name__}.{name}")
		self.assertTrue(endpoints, "the scan found no endpoints: it is looking in the wrong place")
		self.assertEqual(unguarded, [], f"whitelisted with no caller check: {unguarded}")

	def test_the_ledger_is_never_whitelisted(self):
		from seal_hrms.seal_hrms.toil import ledger

		exposed = [
			n
			for n, fn in inspect.getmembers(ledger, inspect.isfunction)
			if fn.__module__ == ledger.__name__ and fn in frappe.whitelisted
		]
		self.assertEqual(exposed, [], "the ledger writes around the ORM and must stay internal")
