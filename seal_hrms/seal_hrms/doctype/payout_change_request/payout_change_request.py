# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Payout Change Request: staff ask to be paid somewhere else; HR confirms first (My Desk PWA-9).

The rules live in `seal_hrms.seal_hrms.payout_change`; the controller only hands over.
"""

from frappe.model.document import Document


class PayoutChangeRequest(Document):
	def validate(self):
		from seal_hrms.seal_hrms import payout_change

		payout_change.validate(self)

	def onload(self):
		from seal_hrms.seal_hrms import payout_change

		payout_change.onload(self)

	def on_trash(self):
		from seal_hrms.seal_hrms import payout_change

		payout_change.on_trash(self)
