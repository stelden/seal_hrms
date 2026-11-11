# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Where a Frappe HR phone-app link opens instead (`/hrms`, PWA-4; HR_ON_MY_DESK.md §5, pwa DESIGN §6.12).

Frappe HR's own app lives at `/hrms/...` and its push messages link there
(`hrms/hr/doctype/pwa_notification/pwa_notification.py`). Where seal_hrms is installed,
`hooks.website_redirects` sends every such address to `/my-hr-go?to=<the rest>`
(`www/my-hr-go.py`), which asks `target()` where to go: My Desk where seal_desk is
installed, else the desk. hrms itself is never touched: Frappe resolves redirects before
pages (`frappe/website/path_resolver.py`).

`target()` is pure, so the mapping is tested against the links Frappe HR builds and the
routes of its app (`tests/test_hrms_redirect.py`).
"""

from __future__ import annotations

from urllib.parse import quote

MY_DESK = "/my-desk"
MY_HR = "/my-desk/apps/my-hr"
SELF_SERVICE = "/desk/self-service"

#: Frappe HR's list routes → (DocType, the Self Service screen for a new one, or None).
COLLECTIONS = {
	"leave-applications": ("Leave Application", "leave/new"),
	"expense-claims": ("Expense Claim", "expenses/new"),
	"employee-advances": ("Employee Advance", "advances/new"),
	"attendance-requests": ("Attendance Request", "attendance/new"),
	"shift-requests": ("Shift Request", "shifts/new"),
	"shift-assignments": ("Shift Assignment", None),
	"salary-slips": ("Salary Slip", None),
}

#: Frappe HR's other screens → the My Desk screen that does the same job.
SCREENS = {
	"": MY_HR,
	"home": MY_HR,
	"dashboard/leaves": f"{MY_HR}/leave",
	"dashboard/expense-claims": f"{MY_HR}/expenses",
	"dashboard/salary-slips": f"{MY_HR}/pay",
	"dashboard/attendance": f"{MY_HR}/attendance",
	"employee-checkins": f"{MY_HR}/check-in",
	"notifications": f"{MY_DESK}/notifications",
	"profile": f"{MY_HR}/me",
	"settings": f"{MY_DESK}/settings",
	"change-password": f"{MY_DESK}/settings",
	"login": f"{MY_DESK}/sign-in",
	"forgot-password": f"{MY_DESK}/sign-in",
	"invalid-employee": MY_HR,
}


def _desk_slug(doctype: str) -> str:
	return doctype.lower().replace(" ", "-")


def target(path: str | None, has_my_desk: bool) -> str:
	"""The address a Frappe HR link `path` (what followed `/hrms`) opens on this site.

	With My Desk: a record opens at `/my-desk/r/<DocType>/<name>` (the Self Service section draws it,
	else the shell's own view), a list at `/my-desk/l/<DocType>`, "new" in the section's own
	form, and the rest at the matching My Desk screen or Self Service's home. Without it: a record opens
	its desk form (P5-7), anything else Self Service.
	"""
	parts = [p for p in (path or "").split("?")[0].split("#")[0].strip("/").split("/") if p]
	head = parts[0] if parts else ""
	if head in COLLECTIONS:
		doctype, new = COLLECTIONS[head]
		rest = parts[1:]
		if len(rest) == 1 and rest[0] == "new":
			return f"{MY_HR}/{new}" if has_my_desk and new else (f"{MY_DESK}/l/{quote(doctype)}" if has_my_desk else SELF_SERVICE)
		if rest:
			# A record's name may hold slashes (Salary Slip: "Sal Slip/HR-EMP-00012/00003").
			name = "/".join(rest)
			if has_my_desk:
				return f"{MY_DESK}/r/{quote(doctype)}/{quote(name, safe='')}"
			return f"/desk/{_desk_slug(doctype)}/{quote(name, safe='')}"
		return f"{MY_DESK}/l/{quote(doctype)}" if has_my_desk else SELF_SERVICE
	if not has_my_desk:
		return SELF_SERVICE
	return SCREENS.get("/".join(parts), MY_HR)
