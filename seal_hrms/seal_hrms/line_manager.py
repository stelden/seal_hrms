# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Line managers: the people others report to, and the My Desk page made for them.

Keith, 2026-11-11 (HR_ON_MY_DESK.md §2.6): seal_hrms ships a standard desk page
`line-manager` for people with direct reports. seal_desk gives a page to Roles or Role
Profiles (its D116), so "has direct reports" is kept as a role, **Line Manager**:

  * granted to an enabled desk user (System User) whose Employee record is Active and has
    at least one Active employee reporting to it (`Employee.reports_to`);
  * kept in step when an Employee is saved or deleted (the employee's own user, and their
    old and new manager's), when a User is saved (a Role Profile rebuilds a user's roles on
    save and drops it), and by a daily pass over everyone;
  * removed only where this code granted it. Each grant is written down in a ledger
    (`DefaultValue` rows under the parent `LEDGER`, one per user). A Line Manager role
    given by hand or by a Role Profile is never in the ledger, so it is never taken away;
    nor is one the person's Role Profile now carries.

The role grants nothing by itself (no DocType permissions, no desk access): it only says who
the page is for. The page itself is the site's to publish (seal_desk D104); the first time
it is on a site with nobody chosen for it, this app offers it to the role (`offer_page`).

Everything shown on the page is worked out with the viewer's own permissions. "Their team"
is their direct reports and, one level down, those people's direct reports (P4-15).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, getdate

ROLE = "Line Manager"
PAGE = "line-manager"
#: `DefaultValue.parent` of the ledger of users this code granted the role to (key = user).
LEDGER = "seal_hrms:line_manager_role"
#: `DefaultValue` key under LEDGER saying the page has been offered to the role once.
PAGE_OFFERED = "__page_offered"
#: Fields whose change can make or unmake a line manager.
WATCHED = ("reports_to", "status", "user_id")


# ---------------------------------------------------------------- who is a line manager


def ensure_role() -> None:
	"""Create the role once if missing (patch v1_26, and after_sync on a new site); never changes it.
	It carries no permissions and no desk access. No existing role fits (SEAL_DEV_RULES §1.23): see the patch."""
	if frappe.db.exists("Role", ROLE):
		return
	role = frappe.new_doc("Role")
	role.update({"role_name": ROLE, "desk_access": 0})
	role.insert(ignore_permissions=True)


def _employee_of(user: str) -> str | None:
	return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")


def _user_of(employee: str | None) -> str | None:
	return frappe.db.get_value("Employee", employee, "user_id") if employee else None


def has_reports(employee: str | None) -> bool:
	"""Whether an Active employee reports to `employee`."""
	return bool(employee) and bool(frappe.db.exists("Employee", {"reports_to": employee, "status": "Active"}))


def should_have_role(user: str) -> bool:
	"""An enabled desk user whose own Active Employee has Active direct reports."""
	row = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
	if not row or not row.enabled or row.user_type != "System User":
		return False
	return has_reports(_employee_of(user))


def _holds(user: str) -> bool:
	return bool(frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": ROLE}))


def _granted_by_us(user: str) -> bool:
	return bool(frappe.db.exists("DefaultValue", {"parent": LEDGER, "defkey": user}))


def _from_profile(user: str) -> bool:
	"""Whether one of the user's Role Profiles carries the role."""
	profiles = frappe.get_all("User Role Profile", filters={"parent": user, "parenttype": "User"}, pluck="role_profile")
	return bool(profiles) and bool(
		frappe.db.exists("Has Role", {"parenttype": "Role Profile", "parent": ["in", profiles], "role": ROLE})
	)


def _note(user: str) -> None:
	if not _granted_by_us(user):
		frappe.get_doc({"doctype": "DefaultValue", "parent": LEDGER, "parenttype": "__default", "parentfield": "system_defaults", "defkey": user, "defvalue": "1"}).db_insert()


def _forget(user: str) -> None:
	frappe.db.delete("DefaultValue", {"parent": LEDGER, "defkey": user})


def sync_user(user: str | None) -> str | None:
	"""Give or take the role so it matches the person's reports. Returns "granted", "removed" or None.

	The Has Role row is added and removed directly rather than by saving the User: a save
	rebuilds the roles of a user with a Role Profile and would drop it again (as `acting`
	does for a stand-in's roles).
	"""
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("Role", ROLE):
		return None
	should, holds = should_have_role(user), _holds(user)
	if should and not holds:
		frappe.get_doc({"doctype": "Has Role", "parent": user, "parenttype": "User", "parentfield": "roles", "role": ROLE}).insert(
			ignore_permissions=True
		)
		_note(user)
		frappe.clear_cache(user=user)
		return "granted"
	if not should and _granted_by_us(user):
		_forget(user)
		if holds and not _from_profile(user):
			frappe.db.delete("Has Role", {"parent": user, "parenttype": "User", "role": ROLE})
			frappe.clear_cache(user=user)
			return "removed"
	return None


def sync_all() -> None:
	"""Daily, and after migrate: everyone who should hold the role, and everyone this code gave it to."""
	if not frappe.db.exists("Role", ROLE):
		return
	managers = frappe.get_all("Employee", filters={"status": "Active", "reports_to": ["is", "set"]}, pluck="reports_to", distinct=True)
	users = set(frappe.get_all("Employee", filters={"name": ["in", managers or [""]], "user_id": ["is", "set"]}, pluck="user_id"))
	users |= set(frappe.get_all("DefaultValue", filters={"parent": LEDGER, "defkey": ["!=", PAGE_OFFERED]}, pluck="defkey"))
	for user in sorted(users):
		try:
			sync_user(user)
		except Exception:
			frappe.log_error(title="Line Manager role not kept in step", message=f"{user}\n{frappe.get_traceback()}")
	offer_page()


# ---------------------------------------------------------------- document events


def on_employee_update(doc, method=None) -> None:
	"""Employee `on_update`: the employee's own user, and their old and new manager's."""
	before = doc.get_doc_before_save()
	if before is not None and not any(doc.get(f) != before.get(f) for f in WATCHED):
		return
	users = {doc.user_id, _user_of(doc.reports_to)}
	if before is not None:
		users |= {before.get("user_id"), _user_of(before.get("reports_to"))}
	for user in users - {None, ""}:
		sync_user(user)


def on_employee_delete(doc, method=None) -> None:
	"""Employee `after_delete`: their manager may have had no one else."""
	for user in {doc.user_id, _user_of(doc.reports_to)} - {None, ""}:
		sync_user(user)


def on_user_update(doc, method=None) -> None:
	"""User `on_update`: a Role Profile rebuilds roles on every save, so put the role back if it went."""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	sync_user(doc.name)


# ---------------------------------------------------------------- the page


def offer_page() -> None:
	"""Once per site: give the shipped Line Manager page to the role, if nobody was chosen for it.

	seal_desk ships every page to a site with nobody chosen and nothing published (its §5.2);
	who gets it and publishing stay the site's. The page arrives in seal_desk's own
	after_migrate, which runs after this app's on most sites, so this is tried again by the
	daily pass and the next migrate until the page is there. A page a Desk Manager already
	gave an audience is left alone. Publishing is left to the Desk Manager.
	"""
	if not frappe.db.exists("DocType", "Desk Page") or not frappe.db.exists("Desk Page", PAGE):
		return
	if frappe.db.exists("DefaultValue", {"parent": LEDGER, "defkey": PAGE_OFFERED}):
		return
	page = frappe.get_doc("Desk Page", PAGE)
	if not page.get("roles") and not page.get("role_profiles") and not page.get("published_version"):
		# The audience row alone, as a Desk Manager's choice would add it: saving the page would
		# also re-export a shipped page's file on a developer site.
		frappe.get_doc({"doctype": "Desk Page Role", "parent": PAGE, "parenttype": "Desk Page", "parentfield": "roles", "role": ROLE}).insert(
			ignore_permissions=True
		)
	frappe.get_doc({"doctype": "DefaultValue", "parent": LEDGER, "parenttype": "__default", "parentfield": "system_defaults", "defkey": PAGE_OFFERED, "defvalue": "1"}).db_insert()


# ---------------------------------------------------------------- the team


def team(user: str) -> list[str]:
	"""Active employees reporting to the user's Employee, and those reporting to them (P4-15)."""
	me = _employee_of(user)
	if not me:
		return []
	direct = frappe.get_all("Employee", filters={"reports_to": me, "status": "Active"}, pluck="name")
	below = frappe.get_all("Employee", filters={"reports_to": ["in", direct or [""]], "status": "Active"}, pluck="name") if direct else []
	return [e for e in dict.fromkeys(direct + below) if e != me]


def week_of(day=None) -> tuple:
	"""Monday and Sunday of the week `day` falls in."""
	day = getdate(day)
	start = add_days(day, -day.weekday())
	return getdate(start), getdate(add_days(start, 6))


def away_this_week(user: str, day=None, company: str | None = None) -> list[frappe._dict]:
	"""Team members with leave this week that the viewer may read (their own permissions).

	Approved and waiting leave both count; a cancelled or rejected application does not. A
	member whose leave the viewer may not read is left out, which is why the empty text
	speaks only of the leave the viewer can see. `company` follows the company chosen on
	My Desk (seal_desk D143).
	"""
	members = team(user)
	if not members:
		return []
	start, end = week_of(day)
	filters = [
		["employee", "in", members],
		["docstatus", "<", 2],
		["status", "in", ["Open", "Approved"]],
		["from_date", "<=", end],
		["to_date", ">=", start],
	]
	if company:
		filters.append(["company", "=", company])
	rows = frappe.get_list(
		"Leave Application",
		filters=filters,
		fields=["name", "employee", "employee_name", "leave_type", "from_date", "to_date", "status", "half_day"],
		order_by="from_date asc, employee_name asc",
		limit=50,
	)
	return [frappe._dict(r) for r in rows]


def _day(d) -> str:
	return f"{d.day} {d.strftime('%b')}"


def _span(start, end) -> str:
	""""12 Nov", "10–14 Nov" or "28 Nov – 3 Dec"."""
	start, end = getdate(start), getdate(end)
	if start == end:
		return _day(start)
	if (start.year, start.month) == (end.year, end.month):
		return f"{start.day}–{_day(end)}"
	return f"{_day(start)} – {_day(end)}"


def away_rows(user: str, day=None, company: str | None = None) -> list[frappe._dict]:
	"""Plain rows for My Desk's "Who's Away This Week": title, meta, the leave to open."""
	if not frappe.db.exists("DocType", "Leave Application"):
		return []
	if not team(user):
		return []
	rows = []
	for r in away_this_week(user, day, company):
		parts = [r.leave_type or _("Leave"), _span(r.from_date, r.to_date)]
		if r.half_day:
			parts.append(_("half day"))
		if r.status == "Open":
			parts.append(_("waiting for approval"))
		rows.append(frappe._dict(title=" ".join((r.employee_name or r.employee).split()), meta=" · ".join(parts), doctype="Leave Application", name=r.name))
	if not rows:
		rows.append(frappe._dict(title=_("Nobody away this week"), meta=_("Of the leave you can see for your team"), doctype=None, name=None))
	return rows
