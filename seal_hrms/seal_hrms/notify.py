# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A Notification Log beside each email seal_hrms sends to a person (My Desk PUSH.md §1).

The desk's bell and the phone's push both come from Notification Log, so an email
alone (a handover to answer, a timesheet to approve, a time off claim returned) never
reached either. Each email helper calls `log` with the same subject.

- Type **Alert**: Frappe sends no email of its own for an Alert, so nobody gets the
  message twice (`notification_skip_email_types`).
- Subject only, no email content: the phone shows the summary line on a locked screen,
  and HR emails can carry pay or leave reasons (P4-8, `[unsupervised — review]`).
- Never raises: the email already went, and a missing bell entry must not undo it.
"""

import frappe
from frappe.utils import strip_html


def log(user: str | None, subject: str, doctype: str | None = None, name: str | None = None) -> None:
	"""Create one Notification Log for `user` (a User name or email) about a document."""
	if not (user and subject):
		return
	try:
		for_user = user if frappe.db.exists("User", {"name": user, "enabled": 1}) else frappe.db.get_value(
			"User", {"email": user, "enabled": 1}, "name"
		)
		if not for_user or for_user in ("Guest",):
			return
		log_doc = frappe.new_doc("Notification Log")
		log_doc.update({
			"type": "Alert",
			"subject": strip_html(subject)[:140],
			"for_user": for_user,
			"from_user": frappe.session.user if frappe.session.user != for_user else None,
			"document_type": doctype,
			"document_name": name,
		})
		log_doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="HR notification not added to the bell", reference_doctype=doctype, reference_name=name)
