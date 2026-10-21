# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""This app's place in Frappe's v16 desk navigation: its tile on the Apps screen.

The dock and the sidebar ship as files (`dock/`, `<module>/sidebar/`) and need no
code. Only the tile's gate does, because `add_to_apps_screen` names a function.

The tile is "My HR" and opens Self Service, the page every member of staff uses, which
is gated on Employee Self Service. Most of what the page lists is Frappe HR's, so the gate
asks the question Frappe asks before drawing a workspace
(`frappe.desk.desktop.Workspace.is_permitted`): may this user open one of the app's
pages? A role-free page is open to every desk user; a page with roles needs one.
"""

import frappe

APP = "seal_hrms"


def has_app_permission() -> bool:
	"""Whether the session user gets this app's tile on the Apps screen.

	**Never raises.** `frappe.boot.load_desktop_data` calls this inside session
	boot, so an exception here is not a missing tile -- it is `/desk` answering
	500 `SessionBootFailed` for every user of the site. Frappe shows a tile for
	an app that declares no gate at all, so that is the answer when the gate
	cannot work one out.
	"""
	try:
		return _tile_is_reachable()
	except Exception:
		frappe.logger("desk").warning(
			f"{APP}: app tile gate failed, showing the tile", exc_info=True
		)
		return True


def _tile_is_reachable() -> bool:
	"""Shown to any desk user who may open at least one of the app's public
	workspaces, in a module they have not blocked. Website users never reach the
	desk, so they never get a tile.

	Called by `frappe.apps.get_apps` once per boot, so it stays to two queries.
	"""
	user = frappe.session.user
	if user == "Administrator":
		return True
	if frappe.get_cached_value("User", user, "user_type") != "System User":
		return False

	# "Visible" means the user has not blocked the module. Read from the User
	# rather than through `frappe.utils.modules.is_module_visible`, which only
	# exists from Frappe 16.50: live runs 16.29, where that import raised
	# ImportError inside boot and took the whole desk down (2026-10-08).
	blocked = set(frappe.get_cached_doc("User", user).get_blocked_modules() or [])
	modules = [m for m in frappe.get_module_list(APP) if m not in blocked]
	if not modules:
		return False

	pages = frappe.get_all("Workspace", filters={"module": ["in", modules], "public": 1}, pluck="name")
	if not pages:
		return False

	allowed: dict[str, set[str]] = {page: set() for page in pages}
	for row in frappe.get_all(
		"Has Role",
		filters={"parenttype": "Workspace", "parent": ["in", pages]},
		fields=["parent", "role"],
	):
		allowed[row.parent].add(row.role)

	roles = set(frappe.get_roles(user))
	return any(not needed or needed & roles for needed in allowed.values())

