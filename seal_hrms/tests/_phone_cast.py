# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""A small cast of its own for the 1.27.0 tests (travel requests, screens that ask first, currency).

A team at a Nairobi health NGO: Baraka Mutua is a field officer who travels; Zawadi Njoroge is
his line manager; Kiprop Chebet is a colleague with no part in his requests; Amina Hassan
manages another team. Each is a login with an Employee record, made through the ORM, so Frappe
HR gives them the usual User Permission on their own Employee record (and company), exactly as
on a client site.

Why not the Otieno and Achieng of the older tests: the phone walk's harness (`e2e/phone`) holds
those people's rows in one long transaction while it runs, so tests that save them wait for its
locks. This cast is created per class, inside the test transaction, and rolled back with it, and
each Employee is given a place of its own in the reporting tree so that inserting it touches no
one else's row.
"""

import frappe
from frappe.tests import IntegrationTestCase

COMPANY = "_Test Company"
DOMAIN = "mvua-health.co.ke"
PEOPLE = {
	"baraka": ("Baraka", "Mutua", "Male", "254722310457"),
	"zawadi": ("Zawadi", "Njoroge", "Female", "254733618204"),
	"kiprop": ("Kiprop", "Chebet", "Male", "254711904376"),
	"amina": ("Amina", "Hassan", "Female", "254745287013"),
	# a nurse at a company that keeps its books in Kenya shillings (the currency tests)
	"wairimu": ("Wairimu", "Gitau", "Female", "254726504183"),
}
SAVEPOINT = "phone_cast"


def email(key: str) -> str:
	first, last, _gender, _phone = PEOPLE[key]
	return f"{first.lower()}.{last.lower()}@{DOMAIN}"


def person(key: str, company: str = COMPANY, roles=("Employee",)) -> tuple[str, str]:
	"""A login and its active Employee record in `company`. Returns (user, employee)."""
	first, last, gender, phone = PEOPLE[key]
	user = email(key)
	if not frappe.db.exists("User", user):
		doc = frappe.new_doc("User")
		doc.update({"email": user, "first_name": first, "last_name": last, "send_welcome_email": 0})
		doc.insert(ignore_permissions=True)
	missing = [r for r in roles if r not in frappe.get_roles(user)]
	if missing:
		frappe.get_doc("User", user).add_roles(*missing)
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		doc = frappe.new_doc("Employee")
		doc.update(
			{
				"first_name": first,
				"last_name": last,
				"gender": gender,
				"date_of_birth": "1991-03-02",
				"date_of_joining": "2023-01-09",
				"status": "Active",
				"company": company,
				"cell_number": phone,
				"user_id": user,
				# A place in the reporting tree of its own, far from everyone else's: a new Employee
				# otherwise renumbers the whole tree (`update_add_node`), which waits on any row another
				# open transaction holds (the harness's people). The tests read reports_to, never the tree.
				"lft": 9_000_000 + 10 * list(PEOPLE).index(key),
				"rgt": 9_000_001 + 10 * list(PEOPLE).index(key),
			}
		)
		doc.insert(ignore_permissions=True)
		employee = doc.name
	return user, employee


def as_user(user: str, fn, *args, **kwargs):
	"""Call `fn` as `user`, and always come back as Administrator."""
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


def _refuse_commit():
	raise AssertionError("A commit inside these tests would make their records permanent")


class CastTestCase(IntegrationTestCase):
	"""The cast made once per class; each test's rows rolled back to a savepoint; no commit allowed."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", COMPANY):
			raise cls.skipTest(cls, f"{COMPANY} is not on this site")
		frappe.set_user("Administrator")
		cls.baraka_user, cls.baraka = person("baraka")
		cls.zawadi_user, cls.zawadi = person("zawadi")
		cls.kiprop_user, cls.kiprop = person("kiprop")
		cls.amina_user, cls.amina = person("amina")
		frappe.db.set_value("Employee", cls.baraka, "reports_to", cls.zawadi)
		frappe.db.set_value("Employee", cls.kiprop, "reports_to", cls.amina)

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.savepoint(SAVEPOINT)
		frappe.db.before_commit.add(_refuse_commit)
		for user in (self.baraka_user, self.zawadi_user, self.kiprop_user, self.amina_user):
			self.addCleanup(frappe.clear_cache, user=user)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.before_commit.reset()
		frappe.db.rollback(save_point=SAVEPOINT)
