# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Travel requests in Self Service (seal_hrms/seal_hrms/travel.py, my_desk/api.py travel_*; Keith 2026-11-11).

Baraka Mutua asks to travel from Nairobi to Kisumu for a field visit; he reports to Zawadi
Njoroge, his line manager, who decides it. Kiprop Chebet is a colleague with no part in it;
Amina Hassan manages another team (`_phone_cast`). Each has Frappe HR's usual User Permission on
their own Employee record. Pinned: the request is Baraka's own, in his company; nobody else on
staff sees it; it moves by the shipped Frappe Workflow; Zawadi sees and decides it despite her
own User Permission; Amina cannot; Baraka never decides his own; the set-up is created once and
a site's later edits to it stand.

The workflow keeps its state in a `workflow_state` column. Before the site is migrated that
column does not exist, so the class borrows it: the Custom Field row goes into the open
transaction and a TEMPORARY copy of the table carries the column for this connection only
(MariaDB does not commit for a temporary table). Rows are rolled back per test.
"""

from unittest.mock import patch

import frappe
from frappe.model.workflow import apply_workflow

from seal_hrms.my_desk import api
from seal_hrms.seal_hrms import travel
from seal_hrms.tests._phone_cast import CastTestCase, as_user

PURPOSE = "Field Visit"
JOURNEY = [{"travel_from": "Nairobi", "travel_to": "Kisumu", "mode_of_travel": "Flight", "departure_date": "2026-12-03 07:30:00", "lodging_required": 1}]
COSTS = [{"expense_type": "Travel", "total_amount": 14500, "comments": "Return flight, Jambojet"}]


def _borrow_state_column(test_class) -> None:
	"""Give Travel Request its workflow state column for this connection, without a commit."""
	from frappe.database.mariadb.schema import MariaDBTable

	if frappe.get_meta(travel.DOCTYPE).has_field(travel.STATE_FIELD):
		return
	field = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": travel.DOCTYPE,
			"fieldname": travel.STATE_FIELD,
			"label": "Workflow State",
			"fieldtype": "Link",
			"options": "Workflow State",
			"hidden": 1,
			"allow_on_submit": 1,
			"no_copy": 1,
		}
	)
	field.name = f"{travel.DOCTYPE}-{travel.STATE_FIELD}"
	field.db_insert()  # the row only: inserting it properly would alter the real table (a commit)
	frappe.clear_cache(doctype=travel.DOCTYPE)
	captured = []
	with patch.object(frappe.db, "sql_ddl", side_effect=lambda query, *a, **k: captured.append(query)):
		MariaDBTable(travel.DOCTYPE, meta=frappe.get_meta(travel.DOCTYPE, cached=False)).create()
	ddl = captured[0].replace("create table if not exists", "create temporary table", 1).replace("create table", "create temporary table", 1)
	assert ddl.lstrip().lower().startswith("create temporary table"), ddl
	table = f"tab{travel.DOCTYPE}"
	assert not frappe.db.sql(f"select name from `{table}` limit 1"), "the real table has rows: not shadowing it"
	frappe.db._cursor.execute(ddl)  # shadows the real, empty table on this connection only
	real_columns = frappe.db.get_db_table_columns

	def columns(name):
		if name == table:
			return [row[0] for row in frappe.db.sql(f"show columns from `{table}`")]
		return real_columns(name)

	borrowed = patch.object(frappe.db, "get_db_table_columns", side_effect=columns)
	borrowed.start()
	test_class.addClassCleanup(frappe.clear_cache, doctype=travel.DOCTYPE)
	test_class.addClassCleanup(lambda: frappe.db._cursor.execute(f"drop temporary table if exists `{table}`"))
	test_class.addClassCleanup(borrowed.stop)


class TravelTestCase(CastTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_borrow_state_column(cls)
		cls.company = frappe.db.get_value("Employee", cls.baraka, "company")

	def setUp(self):
		super().setUp()
		if not frappe.db.exists("Purpose of Travel", PURPOSE):
			frappe.get_doc({"doctype": "Purpose of Travel", "purpose_of_travel": PURPOSE}).insert(ignore_permissions=True)
		if not frappe.db.exists("Expense Claim Type", "Travel"):
			frappe.get_doc({"doctype": "Expense Claim Type", "expense_type": "Travel"}).insert(ignore_permissions=True)
		travel.ensure_permissions()
		travel.ensure_workflow()
		for user in (self.zawadi_user, self.amina_user):
			frappe.get_doc("User", user).add_roles(travel.LINE_MANAGER)
		frappe.clear_cache(doctype=travel.DOCTYPE)
		self.addCleanup(frappe.clear_cache, doctype=travel.DOCTYPE)

	def _request(self, send=0, user=None):
		return as_user(user or self.baraka_user, api.request_travel, "Domestic", PURPOSE, JOURNEY, COSTS, None, "Kisumu county health outreach review", send)

	def _decide(self, user, name, action):
		return as_user(user, apply_workflow, frappe.get_doc(travel.DOCTYPE, name), action)

	def _listed(self, user):
		return as_user(user, frappe.get_list, travel.DOCTYPE, pluck="name")


class TestTheRequestIsBarakasOwn(TravelTestCase):
	def test_company_comes_from_the_employee(self):
		answer = self._request()
		row = frappe.db.get_value(travel.DOCTYPE, answer["name"], ["employee", "company", "docstatus"], as_dict=True)
		self.assertEqual((row.employee, row.company, row.docstatus), (self.baraka, self.company, 0))
		self.assertEqual(answer["state"], travel.DRAFT)
		doc = frappe.get_doc(travel.DOCTYPE, answer["name"])
		self.assertEqual([(r.travel_from, r.travel_to, r.lodging_required) for r in doc.itinerary], [("Nairobi", "Kisumu", 1)])
		self.assertEqual([(r.expense_type, r.total_amount) for r in doc.costings], [("Travel", 14500)])

	def test_company_is_never_the_logins_default(self):
		other = frappe.db.get_value("Company", {"name": ["!=", self.company]}, "name")
		if not other:
			self.skipTest("one company only")
		frappe.defaults.set_user_default("company", other, self.baraka_user)
		self.addCleanup(frappe.defaults.clear_user_default, "company", self.baraka_user)
		name = self._request()["name"]
		self.assertEqual(frappe.db.get_value(travel.DOCTYPE, name, "company"), self.company)

	def test_a_journey_is_required(self):
		with self.assertRaises(frappe.ValidationError):
			as_user(self.baraka_user, api.request_travel, "Domestic", PURPOSE, [{"travel_from": "", "travel_to": ""}])

	def test_nobody_else_on_staff_sees_it(self):
		name = self._request()["name"]
		self.assertIn(name, [r.name for r in as_user(self.baraka_user, api.travel_list)])
		self.assertNotIn(name, [r.name for r in as_user(self.kiprop_user, api.travel_list)])
		self.assertNotIn(name, self._listed(self.kiprop_user))
		with self.assertRaises(frappe.PermissionError):
			as_user(self.kiprop_user, api.travel_record, name)
		with self.assertRaises(frappe.PermissionError):
			as_user(self.kiprop_user, api.travel_action, name, travel.SEND)
		# Another team's manager is no more than a colleague here.
		self.assertNotIn(name, self._listed(self.amina_user))
		with self.assertRaises(frappe.PermissionError):
			as_user(self.amina_user, api.travel_record, name)

	def test_the_list_says_where_and_when(self):
		name = self._request()["name"]
		row = next(r for r in as_user(self.baraka_user, api.travel_list) if r.name == name)
		self.assertEqual((row["travel_from"], row["travel_to"], row["state"]), ("Nairobi", "Kisumu", travel.DRAFT))

	def test_options_name_the_line_manager_and_the_companys_currency(self):
		options = as_user(self.baraka_user, api.travel_options)
		self.assertEqual(options["approver_name"], "Zawadi Njoroge")
		self.assertEqual(options["currency"], frappe.get_cached_value("Company", self.company, "default_currency"))
		self.assertIn(PURPOSE, options["purposes"])
		self.assertIsNone(as_user(self.zawadi_user, api.travel_options)["approver_name"])  # nobody set over her


class TestTheLineManagerDecides(TravelTestCase):
	def test_sent_it_waits_for_zawadi_who_approves_it(self):
		answer = self._request(send=1)
		self.assertEqual(answer["state"], travel.WAITING)
		# Her own Employee User Permission does not hide her team's requests.
		self.assertTrue(frappe.db.exists("User Permission", {"user": self.zawadi_user, "allow": "Employee"}))
		self.assertIn(answer["name"], self._listed(self.zawadi_user))
		record = as_user(self.zawadi_user, api.travel_record, answer["name"])
		self.assertFalse(record["mine"])
		self.assertFalse(record["can_send"])
		self._decide(self.zawadi_user, answer["name"], travel.APPROVE)
		row = frappe.db.get_value(travel.DOCTYPE, answer["name"], ["docstatus", travel.STATE_FIELD], as_dict=True)
		self.assertEqual((row.docstatus, row.get(travel.STATE_FIELD)), (1, travel.APPROVED))

	def test_she_may_reject_it(self):
		name = self._request(send=1)["name"]
		self._decide(self.zawadi_user, name, travel.REJECT)
		self.assertEqual(frappe.db.get_value(travel.DOCTYPE, name, travel.STATE_FIELD), travel.REJECTED)

	def test_a_draft_is_sent_from_its_record(self):
		name = self._request()["name"]
		self.assertTrue(as_user(self.baraka_user, api.travel_record, name)["can_send"])
		self.assertEqual(as_user(self.baraka_user, api.travel_action, name, travel.SEND), travel.WAITING)
		with self.assertRaises(frappe.ValidationError):
			as_user(self.baraka_user, api.travel_action, name, travel.APPROVE)  # decisions are made from Approvals

	def test_another_teams_manager_cannot_decide_it(self):
		name = self._request(send=1)["name"]
		with self.assertRaises(frappe.PermissionError):
			self._decide(self.amina_user, name, travel.APPROVE)

	def test_the_traveller_never_decides_their_own(self):
		# HR raised it for him, so Frappe's own "not the owner" rule does not stop him; ours does.
		doc = frappe.new_doc(travel.DOCTYPE)
		doc.update({"employee": self.baraka, "company": self.company, "travel_type": "Domestic", "purpose_of_travel": PURPOSE})
		doc.append("itinerary", JOURNEY[0])
		doc.insert()
		apply_workflow(doc, travel.SEND)
		frappe.get_doc("User", self.baraka_user).add_roles(travel.LINE_MANAGER)
		with self.assertRaises(frappe.PermissionError):
			self._decide(self.baraka_user, doc.name, travel.APPROVE)

	def test_a_waiting_request_is_an_approval_for_zawadi_only(self):
		from seal_hrms.my_desk import push

		name = self._request(send=1)["name"]
		self.assertTrue(push.waiting_for(self.zawadi_user, travel.DOCTYPE, name))
		self.assertFalse(push.waiting_for(self.kiprop_user, travel.DOCTYPE, name))
		self.assertFalse(push.waiting_for(self.amina_user, travel.DOCTYPE, name))
		self.assertFalse(push.waiting_for(self.baraka_user, travel.DOCTYPE, name))


class TestSetUpIsTheSites(TravelTestCase):
	def test_created_once_and_a_sites_edit_stands(self):
		frappe.db.set_value("Custom DocPerm", {"parent": travel.DOCTYPE, "role": "Employee", "permlevel": 0}, "delete", 0)
		travel.ensure_permissions()
		travel.ensure_workflow()
		self.assertEqual(frappe.db.count("Custom DocPerm", {"parent": travel.DOCTYPE, "role": "Employee", "permlevel": 0}), 1)
		self.assertEqual(frappe.db.get_value("Custom DocPerm", {"parent": travel.DOCTYPE, "role": "Employee", "permlevel": 0}, "delete"), 0)
		self.assertEqual(frappe.db.count("Workflow", {"document_type": travel.DOCTYPE}), 1)
		self.assertEqual(frappe.db.count("Property Setter", {"doc_type": travel.DOCTYPE, "property": "ignore_user_permissions"}), 1)
		self.assertEqual(travel.problems(), [])

	def test_the_shipped_rules_survive_the_new_ones(self):
		self.assertTrue(frappe.db.exists("Custom DocPerm", {"parent": travel.DOCTYPE, "role": "System Manager"}))

	def test_hr_is_not_narrowed(self):
		self.assertFalse(travel.is_narrowed("Administrator"))
		self.assertTrue(travel.is_narrowed(self.kiprop_user))
		self.assertEqual(travel.query_conditions("Administrator"), "")


class TestSelfServiceClaimsTravel(CastTestCase):
	def test_the_section_claims_travel_requests_under_its_new_name(self):
		entry = frappe.get_hooks("seal_desk_app_sections", app_name="seal_hrms")[0]
		self.assertIn(travel.DOCTYPE, entry["claims"])
		self.assertEqual(entry["label"], "Self Service")
		self.assertEqual(entry["key"], "seal_hrms.my_hr")  # kept: the phone's route /my-desk/apps/my-hr follows it
		self.assertIn("seal_hrms.seal_hrms.travel.ensure_setup", frappe.get_hooks("after_migrate", app_name="seal_hrms"))
