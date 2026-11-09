# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Per company: the working day, and how extra hours are banked as time off.

Read through `seal_hrms.seal_hrms.working_time.policy.policy_for`, never directly.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class WorkingTimePolicy(Document):
	def validate(self):
		if self.hours_per_day is not None and self.hours_per_day <= 0:
			frappe.throw(_("Enter the hours in a normal working day."))
		if self.toil_enabled and self.leave_type:
			if not frappe.db.get_value("Leave Type", self.leave_type, "is_compensatory"):
				frappe.throw(
					_(
						"{0} is not a leave type for time off in lieu. Pick one with 'Is Compensatory' ticked."
					).format(self.leave_type),
					title=_("Wrong Leave Type"),
				)
