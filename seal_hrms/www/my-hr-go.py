# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""`/my-hr-go?to=<path>`: where `/hrms/<path>` lands (`hooks.website_redirects`, PWA-4).

Sends the browser on at once (302: the answer depends on whether My Desk is installed, so it
must not be kept); the mapping is `seal_hrms.my_desk.links.target`.
"""

import frappe

from seal_hrms.my_desk.links import target

no_cache = 1


def get_context(context):
	"""Redirect to where the Frappe HR link should open on this site."""
	path = frappe.form_dict.get("to") or ""
	frappe.flags.redirect_location = target(path, "seal_desk" in frappe.get_installed_apps())
	raise frappe.Redirect(302)
