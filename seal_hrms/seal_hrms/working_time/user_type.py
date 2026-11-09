# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Let Employee Self Service users open their time off claims.

Users of Frappe HR's "Employee Self Service" User Type (mhc.local has six) can
open only the doctypes listed on it. Frappe HR adds its own the same way
(`hrms.setup.add_lending_docperms_to_ess`). Run after every migrate, because
Frappe HR rebuilds the list when it sets the User Type up again.

Saving a User Type copies the doctype's permissions into Custom DocPerm for
that site, as it already has for every Self Service doctype (Timesheet, Leave
Application): a later change to the claim's shipped permissions then needs a
patch on such sites (decision D18, WORKING_TIME_DESIGN.md).
"""

import frappe

USER_TYPE = "Employee Self Service"
DOCTYPES = {"Time Off in Lieu Claim": ("read", "write", "create", "delete")}


def allow_claims_for_self_service() -> None:
	"""after_migrate: list the claim on the Self Service User Type, if the site has one."""
	try:
		if not frappe.db.exists("User Type", USER_TYPE):
			return
		doc = frappe.get_doc("User Type", USER_TYPE)
		listed = {row.document_type for row in doc.user_doctypes}
		missing = [dt for dt in DOCTYPES if dt not in listed and frappe.db.exists("DocType", dt)]
		if not missing:
			return
		for doctype in missing:
			doc.append("user_doctypes", {"document_type": doctype, **{perm: 1 for perm in DOCTYPES[doctype]}})
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
	except Exception:
		# Optional work: a failure here must not stop the migrate (it is logged for App Health).
		frappe.log_error(
			title="seal_hrms: Self Service user type not updated", message=frappe.get_traceback()
		)
