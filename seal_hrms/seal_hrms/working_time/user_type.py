# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Let Employee Self Service users open what Self Service (desk and phone) needs.

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
#: What staff on this user type need beyond Frappe HR's own list: their time off claims, and
#: what the Self Service section of the My Desk phone app reads or writes (MY_DESK_P5_PLAN.md §7).
#: A DocType already listed is given only the rights it lacks; nothing is ever taken away.
DOCTYPES = {
	"Time Off in Lieu Claim": ("read", "write", "create", "delete"),
	"Payout Change Request": ("read", "write", "create", "delete"),
	"Task Assignment": ("read", "write", "create", "submit", "cancel"),
	"Employee Checkin": ("read", "create"),
	"Leave Allocation": ("read",),
	"Employee Dependent and Beneficiary": ("read",),
	"Activity Type": ("read",),
	# Frappe HR lists it already; kept here so a site whose list lost it gets it back (Keith, 2026-11-11).
	"Travel Request": ("read", "write", "create", "delete"),
}
SAVEPOINT = "seal_hrms_ess_claims"


def allow_claims_for_self_service() -> None:
	"""On install and after migrate: list DOCTYPES on the Self Service User Type, if the site has one."""
	from frappe.permissions import setup_custom_perms

	if not frappe.db.exists("User Type", USER_TYPE):
		return
	frappe.db.savepoint(SAVEPOINT)
	try:
		doc = frappe.get_doc("User Type", USER_TYPE)
		listed = {row.document_type: row for row in doc.user_doctypes}
		changed = False
		for doctype, perms in DOCTYPES.items():
			if not frappe.db.exists("DocType", doctype):
				continue
			row = listed.get(doctype)
			if row is None:
				# Frappe's User Type save looks for the role's rule, and when there is none adds
				# one: that first copies the doctype's shipped rules, which already hold this role,
				# then finds the rule "already exists" and returns nothing, and the save fails
				# ("Custom DocPerm None not found"). Copying them first lets its lookup find it.
				# Bit every site whose claim had no customised permissions yet (found 1.20.1).
				setup_custom_perms(doctype)
				doc.append("user_doctypes", {"document_type": doctype, **{perm: 1 for perm in perms}})
				changed = True
				continue
			missing = [perm for perm in perms if not row.get(perm)]
			if missing:
				setup_custom_perms(doctype)
				for perm in missing:
					row.set(perm, 1)
				changed = True
		if not changed:
			return
		# The same trap for the DocTypes the new ones link to: the save gives the role "select" on
		# each, through the same lookup. Work the list out as the save will, and copy theirs first.
		doc.add_select_perm_doctypes()
		for row in [*doc.get("select_doctypes"), *doc.get("custom_select_doctypes")]:
			setup_custom_perms(row.document_type)
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
	except Exception:
		frappe.db.rollback(save_point=SAVEPOINT)
		# Optional work: a failure here must not stop the migrate (it is logged for App Health).
		frappe.log_error(
			title="seal_hrms: Self Service user type not updated", message=frappe.get_traceback()
		)
