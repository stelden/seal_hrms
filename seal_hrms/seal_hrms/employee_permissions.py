# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Grant the Employee permlevels this app's field scheme requires.

Employee carries a permlevel scheme: personal contact and address data at
level 1, bank/salary/approver detail at level 2, everything else open. Those
levels need matching permissions or the restricted fields are readable by
nobody at all.

**Why this is code and not a `custom_perms` block in the customization file:**
shipping `custom_perms` REPLACES the doctype's entire permission set. A file
listing only the level-1 and level-2 rows therefore deletes the level-0 rows,
and once any Custom DocPerm exists it supersedes the DocType's own — so nobody
can read Employee at all. That is exactly what happened. This adds rows
without ever removing one, and restores level 0 from the DocType's own
DocPerms if it finds it missing.
"""

import frappe

LEVEL_GRANTS = (
	# role, permlevel, write
	("HR Manager", 1, 1),
	("HR Manager", 2, 1),
	("HR User", 1, 1),
	("HR User", 2, 0),
	("System Manager", 1, 1),
	("System Manager", 2, 1),
)


def _has(role, permlevel):
	return frappe.db.exists("Custom DocPerm", {
		"parent": "Employee", "role": role, "permlevel": permlevel,
	})


def _add(role, permlevel, write):
	frappe.get_doc({
		"doctype": "Custom DocPerm", "parent": "Employee", "parenttype": "DocType",
		"parentfield": "permissions", "role": role, "permlevel": permlevel,
		"read": 1, "write": write, "report": 1,
	}).insert(ignore_permissions=True)


def ensure_employee_permlevels() -> None:
	"""Idempotent; runs on install and on every migrate."""
	if not frappe.db.exists("DocType", "Employee"):
		return

	custom_rows = frappe.get_all(
		"Custom DocPerm", filters={"parent": "Employee"}, fields=["role", "permlevel"],
	)
	restored = []

	# If Custom DocPerms exist but level 0 is absent, the base permissions have
	# been wiped and Employee is unreadable. Rebuild level 0 from the DocType.
	if custom_rows and not any(r.permlevel == 0 for r in custom_rows):
		# Read tabDocPerm directly: frappe.get_meta returns the CUSTOM perms once
		# any exist, so the originals are invisible through meta at this point.
		originals = frappe.get_all(
			"DocPerm",
			filters={"parent": "Employee", "permlevel": 0},
			fields=["role", "read", "write", "create", "delete", "submit", "cancel",
			        "amend", "report", "export", "share", "print", "email"],
		)
		for perm in originals:
			if _has(perm.role, 0):
				continue
			doc = frappe.get_doc({
				"doctype": "Custom DocPerm", "parent": "Employee",
				"parenttype": "DocType", "parentfield": "permissions",
				"role": perm.role, "permlevel": 0,
			})
			for field in ("read", "write", "create", "delete", "submit", "cancel",
			              "amend", "report", "export", "share", "print", "email"):
				doc.set(field, perm.get(field) or 0)
			doc.insert(ignore_permissions=True)
			restored.append(perm.role)

	granted = []
	for role, permlevel, write in LEVEL_GRANTS:
		if not frappe.db.exists("Role", role) or _has(role, permlevel):
			continue
		_add(role, permlevel, write)
		granted.append(f"{role}@{permlevel}")

	if restored or granted:
		frappe.db.commit()
		frappe.clear_cache(doctype="Employee")
		if restored:
			print(f"[seal_hrms] restored level-0 Employee permissions for: {', '.join(restored)}")
		if granted:
			print(f"[seal_hrms] granted Employee permlevels: {', '.join(granted)}")
	else:
		print("[seal_hrms] Employee permissions already correct — no-op")
