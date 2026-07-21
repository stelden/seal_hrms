# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Return Employee org-placement fields to permlevel 0.

The adopted permlevel scheme put twelve org-placement and name fields behind
permlevel 1 alongside genuinely personal data. Those twelve are what every
doctype linking to Employee has to read in order to show who a record is
about, or to filter Active staff by company — so restricting them broke
Employee links for any user without an HR role, in every app, not just the one
where it surfaced.

Personal contact and address data stays at permlevel 1, and bank, salary and
approver detail stays at permlevel 2. The distinction is now "where does this
person sit in the organisation" (open) versus "how do I contact or pay them"
(restricted).

Frappe does not remove a Property Setter when it disappears from a
customization file, so this deletes the rows explicitly. Idempotent.
"""

import frappe

ORG_FIELDS = (
	"status", "company", "department", "designation", "branch", "grade",
	"reports_to", "employee_number",
	"first_name", "middle_name", "last_name", "salutation",
)


def execute():
	names = frappe.get_all(
		"Property Setter",
		filters={"doc_type": "Employee", "property": "permlevel",
		         "field_name": ["in", ORG_FIELDS]},
		pluck="name",
	)
	if not names:
		print("[seal_hrms.v1_6] Employee org fields already at permlevel 0 — no-op")
		return

	for name in names:
		frappe.delete_doc("Property Setter", name, force=1, ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache(doctype="Employee")
	print(f"[seal_hrms.v1_6] returned {len(names)} Employee field(s) to permlevel 0")
