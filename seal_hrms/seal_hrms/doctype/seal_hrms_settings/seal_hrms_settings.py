# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SEALHRMSSettings(Document):
	"""Site-wide Self Service settings: the banner image, and which phone screens ask
	"is it still you?" before they show anything (`seal_hrms.sensitive`).

	Leave planning settings moved to seal_leave_planning; their checks went with
	them, since a check on a field the form no longer has stops every save.
	"""

	def validate(self):
		from seal_hrms.seal_hrms.sensitive import MAX_MINUTES, MIN_MINUTES

		minutes = int(self.confirm_window_minutes or 0)
		if minutes and not MIN_MINUTES <= minutes <= MAX_MINUTES:  # blank reads as the default
			frappe.throw(
				_("A check can last between {0} and {1} minutes.").format(MIN_MINUTES, MAX_MINUTES),
				title=_("Check Lasts (Minutes)"),
			)
