# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Give `ToDo.assigned_by` back its stock optional-ness.

A Customize Form tick on 2024-08-25 left a Property Setter making the field
mandatory for every ToDo on the site. Nothing in this app ever needed it:
`task_assignment.py` and `leave_application.py` both set `assigned_by`
explicitly, and `overrides/todo.get_permission_query_conditions` only READS it
-- a null there simply means the row is matched by `owner` or `allocated_to`
instead.

What it did do was break things nobody connected to it, because ToDo is
Frappe's, not ours, and the framework creates them on paths we do not control:

  * `frappe.desk.form.assign_to.add` and every feature built on assignment;
  * Frappe's own test-record preload, which inserts a stock ToDo carrying no
    assigner -- so `bench run-tests --module` died before loading a single test
    for any doctype whose dependency graph reaches ToDo. Whole suites across
    this bench were unrunnable, and the failure named ToDo rather than them.

This is the trap in SEAL_DEV_RULES about `reqd` on a SHARED doctype: the tick is
made in one app's Customize Form and lands on every app's writes.

Removing the entry from `custom/todo.json` is not enough on its own -- a
Customize Form export that no longer mentions a Property Setter does not delete
the record that a previous migrate created. This does.

Idempotent: a site that never had it, or has already run this, is a no-op.
"""

import frappe

SETTER = "ToDo-assigned_by-reqd"


def execute():
	if not frappe.db.exists("Property Setter", SETTER):
		print(f"[todo] no-op -- {SETTER} is not present")
		return

	frappe.delete_doc("Property Setter", SETTER, ignore_permissions=True,
	                  ignore_missing=True, force=True)
	frappe.clear_cache(doctype="ToDo")
	print(f"[todo] removed {SETTER}: assigned_by is optional again, as Frappe ships it")
