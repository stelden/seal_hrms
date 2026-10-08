# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""This app's place in Frappe's v16 navigation: Apps screen tile, dock, module sidebars.

The same module ships in every seal_* app with only `APP` changed, so a fix here
belongs in all of them (dev_notes/navigation_v16/). It reads the files the app
ships rather than the site's tables, because a site's own arrangement of its
sidebars and dock is the site's business, not something the app can promise.
"""

import json
import pathlib
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

APP = "seal_hrms"

# What each sidebar link type must name for the entry to open anything.
LINK_TARGETS = {
	"DocType": "DocType",
	"Report": "Report",
	"Page": "Page",
	"Workspace": "Workspace",
	"Dashboard": "Dashboard",
}


def _package() -> pathlib.Path:
	return pathlib.Path(frappe.get_app_path(APP))


def _shipped_sidebars() -> list[dict]:
	"""Every `Sidebar` export under the app's module folders."""
	found = []
	for path in _package().glob("*/sidebar/*/*.json"):
		doc = json.loads(path.read_text())
		if doc.get("doctype") == "Sidebar":
			found.append({**doc, "_path": str(path.relative_to(_package()))})
	return found


def _shipped_dock() -> dict | None:
	path = _package() / "dock" / APP / f"{APP}.json"
	return json.loads(path.read_text()) if path.exists() else None


def _required_apps() -> set[str]:
	return {entry.split("/")[-1] for entry in frappe.get_hooks("required_apps", app_name=APP) or []}


def _apps_screen() -> list[dict]:
	return frappe.get_hooks("add_to_apps_screen", app_name=APP) or []


class TestDeskNavigation(IntegrationTestCase):
	def test_app_has_a_way_in(self):
		"""Without a tile or a mount, the Apps screen offers nobody a way to this app."""
		dock = _shipped_dock()
		self.assertIsNotNone(dock, f"{APP} ships no dock/{APP}/{APP}.json")
		self.assertTrue(
			_apps_screen() or dock.get("mount_on"),
			f"{APP} has neither an add_to_apps_screen tile nor a dock mount_on",
		)

	def test_a_companion_mounts_on_an_app_it_requires(self):
		"""A mount onto a host that is not installed silently drops every entry."""
		host = (_shipped_dock() or {}).get("mount_on")
		if not host:
			return
		self.assertTrue(
			host == "frappe" or host in _required_apps(),
			f"{APP} mounts on {host}, which is not in required_apps",
		)

	def test_dock_entries_open_this_apps_sidebars(self):
		dock = _shipped_dock() or {}
		titles = {sidebar["title"] for sidebar in _shipped_sidebars()}
		for row in dock.get("items", []):
			self.assertTrue(row.get("icon") and row.get("title"), f"dock row needs icon and title: {row}")
			if row["link_type"] == "Sidebar":
				self.assertIn(row["link_to"], titles, f"dock row opens a sidebar {APP} does not ship")
			elif row["link_type"] == "Workspace":
				self.assertTrue(frappe.db.exists("Workspace", row["link_to"]), row)

	def test_every_workspace_module_ships_a_sidebar(self):
		"""A workspace in a module with no shipped sidebar lands in a generated one."""
		modules = set(frappe.get_module_list(APP))
		with_sidebar = {sidebar["module"] for sidebar in _shipped_sidebars()}
		workspaces = frappe.get_all(
			"Workspace", filters={"module": ["in", list(modules)], "public": 1}, pluck="module"
		)
		self.assertEqual(set(workspaces) - with_sidebar, set())

	def test_sidebar_entries_resolve(self):
		"""Every link opens something that exists, and none opens a child table."""
		self.assertTrue(_shipped_sidebars(), f"{APP} ships no module sidebar")
		broken = []
		for sidebar in _shipped_sidebars():
			self.assertIn(sidebar["module"], frappe.get_module_list(APP), sidebar["_path"])
			for item in sidebar.get("items", []):
				if item.get("type") != "Link":
					continue
				doctype = LINK_TARGETS.get(item.get("link_type"))
				if item.get("link_type") == "URL":
					ok = bool(item.get("url"))
				elif doctype:
					ok = bool(frappe.db.exists(doctype, item.get("link_to")))
					if ok and doctype == "DocType":
						ok = not frappe.get_meta(item["link_to"]).istable
				else:
					ok = False
				if not ok:
					broken.append(f"{sidebar['title']}: {item.get('label')} -> {item.get('link_to')}")
		self.assertEqual(broken, [])

	def test_tile_points_at_real_things(self):
		for tile in _apps_screen():
			logo = tile.get("logo", "")
			self.assertTrue(logo.startswith(f"/assets/{APP}/"), logo)
			asset = _package() / "public" / logo.removeprefix(f"/assets/{APP}/")
			self.assertTrue(asset.exists(), f"tile logo missing on disk: {asset}")
			self.assertTrue(tile.get("route", "").startswith("/desk/"), tile)
			self.assertTrue(callable(frappe.get_attr(tile["has_permission"])), tile)

	def test_tile_follows_document_access(self):
		"""Anyone who reads one of the app's documents gets the tile; nobody else does."""
		for tile in _apps_screen():
			gate = frappe.get_attr(tile["has_permission"])

			frappe.set_user("Guest")
			self.assertFalse(gate(), "a website visitor was offered the tile")

			user = frappe.new_doc("User")
			user.update(
				{"email": "wanjiru.kamau@stelden.co.ke", "first_name": "Wanjiru", "last_name": "Kamau"}
			)
			user.append("roles", {"role": "System Manager"})
			user.insert(ignore_permissions=True, ignore_if_duplicate=True)

			frappe.set_user(user.name)
			try:
				self.assertTrue(gate())
				with patch("frappe.permissions.get_doctypes_with_read", return_value=[]):
					self.assertFalse(gate(), "a user who reads none of the app's documents got the tile")
			finally:
				frappe.set_user("Administrator")

	def test_the_gate_never_raises(self):
		"""A gate that throws is not a missing tile — it is a dead desk.

		`frappe.boot.load_desktop_data` calls it inside session boot, so an
		exception answers `/desk` with 500 SessionBootFailed for every user of
		the site. That is what an ImportError in this module did on 2026-10-08,
		across every site on a Frappe older than 16.50.
		"""
		user = frappe.new_doc("User")
		user.update(
			{"email": "njeri.wambui@stelden.co.ke", "first_name": "Njeri", "last_name": "Wambui"}
		)
		user.append("roles", {"role": "System Manager"})
		user.insert(ignore_permissions=True, ignore_if_duplicate=True)

		for tile in _apps_screen():
			gate = frappe.get_attr(tile["has_permission"])
			# As a plain desk user, not Administrator: the gate answers early for
			# Administrator and would never reach the failing call.
			frappe.set_user(user.name)
			try:
				with patch("frappe.get_module_list", side_effect=RuntimeError("boom")):
					self.assertTrue(gate(), "the gate hid the tile instead of failing open")
			except Exception as raised:  # noqa: BLE001 — the point of the test
				self.fail(f"the app tile gate raised inside boot: {raised!r}")
			finally:
				frappe.set_user("Administrator")

	def test_the_gate_uses_no_version_specific_import(self):
		"""`frappe.utils.modules` gained and lost names between 16.29 and 16.50.

		Importing one of them inside a boot hook makes the desk's survival a
		question of which Frappe a site happens to run. Read `User.block_modules`
		instead: it has been there for years.
		"""
		source = (_package() / "desk_navigation.py").read_text()
		self.assertNotIn(
			"from frappe.utils.modules import", source,
			"the Apps-screen gate imports from a module whose contents vary by Frappe version",
		)
