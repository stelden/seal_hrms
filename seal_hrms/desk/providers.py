# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""seal_hrms's subscription to My Desk (`seal_desk`).

An ADAPTER and nothing more. What a handover needs from each person is answered
by `seal_hrms.seal_hrms.handover_work`, which returns plain records and runs on
any site. Here each record becomes a desk `Item`.

**Nothing at module level may import `seal_desk`.** The desk is optional, and
most sites running this app do not have it. These functions are only ever
called by the desk's own runner, so an import inside them only runs where the
desk exists (SEAL_DEV_RULES §3.15). `tests/test_desk_subscription.py` enforces
it. Nothing else in seal_hrms imports this module.
"""

import frappe


def handover_work(user, ctx):
	"""What leave handovers are waiting on `user` for."""
	from seal_desk.desk.schema import Item

	from seal_hrms.seal_hrms.handover_work import work_for

	group = ctx.memo("seal_hrms:group", lambda: frappe.db.get_value("DocType", "Task Assignment", "module") or "")
	return [
		Item(
			kind=w.kind,
			source="",  # the runner stamps the provider id
			doctype=w.doctype,
			name=w.name,
			title=w.title,
			subtitle=w.subtitle,
			group=group,
			due=w.due,
			priority=ctx.priority_from_due(w.due),
			route=w.route,
		)
		for w in work_for(user)
	]
