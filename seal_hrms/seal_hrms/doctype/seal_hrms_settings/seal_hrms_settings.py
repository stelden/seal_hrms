# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class SEALHRMSSettings(Document):
	"""Site-wide Self Service settings (the banner image).

	Leave planning settings moved to seal_leave_planning; their checks went with
	them, since a check on a field the form no longer has stops every save.
	"""
