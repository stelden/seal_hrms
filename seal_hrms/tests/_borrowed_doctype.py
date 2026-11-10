# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Use a DocType this branch adds before the site is migrated (as seal_common's P2b passkey tests do).

On a shared development site `bench migrate` is not the test's to run. Where the
DocType is missing, :func:`borrow` puts its DocType rows into the open transaction
(rolled back with the test class) and makes a TEMPORARY table from the DocType's own
JSON: MariaDB does not commit for a temporary table, and it lives only on this
connection. While borrowed, a commit fails the test, since it would keep the rows.
On a migrated site nothing is borrowed and the real table is used.
"""

import json
from unittest.mock import patch

import frappe


def borrow(doctype: str, json_path: str, test_class) -> bool:
	"""Make `doctype` usable for `test_class`'s tests. True when it had to be borrowed."""
	if frappe.db.exists("DocType", doctype):
		return False
	from frappe.database.mariadb.schema import MariaDBTable

	with open(json_path) as f:
		definition = json.load(f)
	doc = frappe.get_doc(definition)
	doc.set_parent_in_children()
	doc.db_insert()
	for idx, child in enumerate(doc.get_all_children(), start=1):
		child.name = child.name or frappe.generate_hash(length=10)
		child.idx = child.idx or idx
		child.db_insert()
	frappe.clear_cache(doctype=doctype)

	captured = []
	with patch.object(frappe.db, "sql_ddl", side_effect=lambda query, *a, **k: captured.append(query)):
		MariaDBTable(doctype, meta=frappe.get_meta(doctype, cached=False)).create()
	ddl = captured[0].replace("create table", "create temporary table if not exists", 1)
	assert ddl.lstrip().lower().startswith("create temporary table"), ddl
	# Through the cursor: frappe.db.sql refuses DDL inside a transaction, rightly for a real table.
	frappe.db._cursor.execute(ddl)

	real_columns, real_exists = frappe.db.get_db_table_columns, frappe.db.table_exists

	def columns(table):
		# information_schema does not list temporary tables; SHOW COLUMNS does.
		if table == f"tab{doctype}":
			return [row[0] for row in frappe.db.sql(f"show columns from `{table}`")]
		return real_columns(table)

	def exists(name, cached=True):
		return True if name in (doctype, f"tab{doctype}") else real_exists(name, cached=cached)

	for borrowed in (
		patch.object(frappe.db, "commit", side_effect=AssertionError(f"a commit would keep the borrowed {doctype} DocType")),
		patch.object(frappe.db, "get_db_table_columns", side_effect=columns),
		patch.object(frappe.db, "table_exists", side_effect=exists),
	):
		borrowed.start()
		test_class.addClassCleanup(borrowed.stop)
	test_class.addClassCleanup(frappe.clear_cache, doctype=doctype)
	return True
