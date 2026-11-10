# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""The Line Manager role, created once on sites that predate it (SEAL_DEV_RULES §1.23).

No existing role means "has people reporting to them" without granting anything: Leave Approver
and Expense Approver carry permissions on those DocTypes, Head of Department is a department's
head (seal_hrms 1.8.0), and a site's own "Supervisor" means whatever that site decided. So
seal_hrms ships its own, from a patch and not a fixture, so a site's later edits to it stand.
New sites get it from `after_sync`. The role is then kept on the right people by
`line_manager.sync_all` after every migrate.
"""

from seal_hrms.seal_hrms.line_manager import ensure_role


def execute():
	ensure_role()
