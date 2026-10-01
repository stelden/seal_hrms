# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""seal_hrms's subscription to My Desk (`seal_desk`).

An ADAPTER and nothing more. What a handover needs from each person is answered
by `seal_hrms.seal_hrms.handover_work`, which returns plain records and runs on
any site. Here each record becomes a row of a My Desk "Waiting for you" list
(seal_desk DESIGN §18.2: a standard group declared through `seal_desk_cue_groups`,
`renders_as: "list"`), which an admin places on any desk page.

**Nothing at module level may import `seal_desk`.** The desk is optional, and
most sites running this app do not have it. These functions are only ever
called by the desk itself, so an import inside them only runs where the desk
exists (SEAL_DEV_RULES §3.15). `tests/test_task_assignment_surfaces.py` enforces
it. Nothing else in seal_hrms imports this module.
"""

from frappe import _


def handover_rows(ctx):
	"""What leave handovers are waiting on the person looking for."""
	from seal_desk.role_center.routes import Target
	from seal_desk.role_center.schema import ListRow

	from seal_hrms.seal_hrms.handover_work import work_for

	rows = []
	for w in sorted(work_for(ctx.user), key=lambda w: w.due or "9999"):
		meta = " · ".join(p for p in (w.subtitle, _("due {0}").format(w.due) if w.due else "") if p)
		rows.append(ListRow(title=w.title, meta=meta, target=Target("URL", w.route, w.route, None, True)))
	return rows
