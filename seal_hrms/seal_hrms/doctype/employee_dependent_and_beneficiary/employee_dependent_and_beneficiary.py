# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
import datetime
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta

class EmployeeDependentandBeneficiary(Document):
	def validate(self):
		set_full_name(self)
		set_age(self)

def set_age(doc):
	if doc.date_of_birth:
		doc.age = relativedelta(datetime.today(), doc.date_of_birth).years
	else:
		doc.age = 0

def set_full_name(doc):
	doc.full_name = " ".join(filter(None, [doc.first_name, getattr(doc, "middle_name", None), getattr(doc, "last_name", None)]))

