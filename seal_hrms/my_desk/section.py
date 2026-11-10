# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Who sees the My HR section of the My Desk phone app (SECTIONS_CONTRACT.md §1, `visible`).

seal_desk asks this once per boot for the person signing in, so it is one indexed read and
nothing else. Plain data in, a bool out; nothing imports seal_desk.
"""

import frappe


def visible(user: str) -> bool:
	"""Anyone whose login is linked to an active Employee: My HR is their own HR, and only theirs."""
	if not user or user == "Guest":
		return False
	return bool(frappe.db.exists("Employee", {"user_id": user, "status": "Active"}))
