# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""SEAL HRMS Settings can be saved.

Leave planning moved to seal_leave_planning and its fields were removed from
these settings, but the controller kept checking them, so every save raised
before it reached the database.
"""

import frappe
from frappe.tests import IntegrationTestCase


class TestSealHrmsSettings(IntegrationTestCase):
	def test_the_settings_can_be_saved(self):
		settings = frappe.get_single("SEAL HRMS Settings")
		banner = settings.ess_banner_image

		settings.save()

		self.assertEqual(frappe.db.get_single_value("SEAL HRMS Settings", "ess_banner_image"), banner)
