# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""COPY of seal_desk P3's e2e/phone/seed.py (unchanged below), kept for the schema borrowing seed.py uses.

What the phone suite needs on dev.local, made inside the harness's one transaction.

Nothing here is committed (``harness.py``): the borrowed schema, the people, the workflow and
its documents, the desk page, every Notification Log and passkey vanish when the harness stops.
Records are made through the ORM (SEAL_DEV_RULES §1.9) with Kenyan names.

People: **Wambui Njoroge**, Field Operations Manager, approves field travel; **Kipchumba
Rotich**, Field Officer, asks for it. Both are staff (System Users) with a mobile number, so
password and code sign-in works for them.
"""

import json
import os

import frappe
from frappe.utils.password import update_password

HERE = os.path.dirname(os.path.abspath(__file__))

MANAGER = "wambui.njoroge@phone-e2e.example.co.ke"
OFFICER = "kipchumba.rotich@phone-e2e.example.co.ke"
PASSWORD = "Nyeri-Hills#2026"
MANAGER_ROLE = "Field Operations Manager"
OFFICER_ROLE = "Field Officer"
DOCTYPE = "Field Travel Request"
WORKFLOW = "Field Travel Request Approval"
PAGE = "Field Operations"
REQUESTS = [
	# (title, traveller, destination, nights, amount, purpose)
	("Mombasa port inspection", "Kipchumba Rotich", "Mombasa", 3, 48600, "Inspect the county's consignment of borehole pumps at Kilindini."),
	("Garissa borehole site survey", "Kipchumba Rotich", "Garissa", 2, 36250, "Survey the three borehole sites approved in the ward plan."),
	("Kisumu stores audit", "Kipchumba Rotich", "Kisumu", 4, 71400, "Count the regional stores before the year-end audit."),
	("Nanyuki fleet check", "Kipchumba Rotich", "Nanyuki", 1, 15800, "Check the field vehicles before the long rains."),
]

#: Read by the suite through /__harness/seeded.
SEEDED: dict = {}


# --- schema this branch needs and dev.local lacks -----------------------------------------


def borrow_schema() -> set[str]:
	"""Borrow seal_common P2's DocTypes and seal_desk's new column. Returns the temporary tables made."""
	from seal_common.seal_common.tests.borrowed_doctypes import borrow_doctype
	from seal_common.seal_common.tests.passkey_fixtures import install_login_passkey
	from seal_common.seal_common.tests.push_fixtures import install_push_doctypes

	made = set()
	if install_login_passkey():
		made.add("tabLogin Passkey")
	if install_push_doctypes():
		made |= {"tabPush Private Document Type", "tabPush Subscription"}
	_teach_options("OTP Log", "purpose", frappe.get_app_path("seal_common", "otp", "doctype", "otp_log", "otp_log.json"))
	path = frappe.get_app_path("seal_desk", "seal_desk", "doctype", "desk_page_item", "desk_page_item.json")
	made |= shadow_with_new_columns("Desk Page Item", path)
	if borrow_doctype(os.path.join(HERE, "field_travel_request.json")):
		made.add(f"tab{DOCTYPE}")
	return made


def _teach_options(doctype: str, fieldname: str, path: str) -> None:
	"""A Select field's options as this branch ships them (an option added, no column change)."""
	with open(path) as handle:
		field = next(f for f in json.load(handle)["fields"] if f["fieldname"] == fieldname)
	frappe.db.sql(
		"update `tabDocField` set options = %s where parent = %s and fieldname = %s",
		(field.get("options"), doctype, fieldname),
	)
	frappe.clear_cache(doctype=doctype)


def shadow_with_new_columns(doctype: str, path: str) -> set[str]:
	"""Give ``doctype`` the fields its JSON at ``path`` adds, for this connection only.

	The DocField rows go into the transaction; the table is shadowed by a TEMPORARY table of
	the same name, built from the new meta and filled with the real table's rows (MariaDB
	lets a temporary table hide a permanent one; creating it does not commit). Returns the
	shadowed table, or nothing when the site already has every column.
	"""
	from frappe.database.mariadb.schema import MariaDBTable
	from frappe.model import no_value_fields

	table = f"tab{doctype}"
	real = {row[0] for row in frappe.db.sql(f"show columns from `{table}`")}
	with open(path) as handle:
		definition = json.load(handle)
	missing = [f for f in definition["fields"] if f["fieldname"] not in real and f["fieldtype"] not in no_value_fields]
	if not missing:
		return set()
	known = set(frappe.get_all("DocField", filters={"parent": doctype}, pluck="fieldname"))
	for idx, field in enumerate(definition["fields"], start=1):
		if field["fieldname"] in known:
			continue
		row = frappe.get_doc({"doctype": "DocField", "parent": doctype, "parenttype": "DocType", "parentfield": "fields", "idx": idx, **field})
		row.name = frappe.generate_hash(length=10)
		row.db_insert()
	frappe.clear_cache(doctype=doctype)
	rows = frappe.db.sql(f"select * from `{table}`", as_dict=True)
	captured = []
	real_ddl = frappe.db.sql_ddl
	frappe.db.sql_ddl = lambda query, *a, **k: captured.append(query)
	try:
		MariaDBTable(doctype, meta=frappe.get_meta(doctype, cached=False)).create()
	finally:
		frappe.db.sql_ddl = real_ddl
	ddl = captured[0].replace("create table", "create temporary table", 1)
	assert ddl.lstrip().lower().startswith("create temporary table"), ddl
	frappe.db._cursor.execute(ddl)
	columns = {row[0] for row in frappe.db.sql(f"show columns from `{table}`")}
	for row in rows:
		values = {k: v for k, v in row.items() if k in columns}
		names = ", ".join(f"`{k}`" for k in values)
		marks = ", ".join(["%s"] * len(values))
		frappe.db.sql(f"insert into `{table}` ({names}) values ({marks})", tuple(values.values()))
	return {table}


# --- people, the workflow, a desk page ----------------------------------------------------


def _role(name: str) -> None:
	if not frappe.db.exists("Role", name):
		frappe.new_doc("Role").update({"role_name": name, "desk_access": 1}).insert(ignore_permissions=True)


def _person(email: str, first: str, last: str, mobile: str, role: str) -> None:
	user = frappe.new_doc("User")
	user.update({"email": email, "first_name": first, "last_name": last, "mobile_no": mobile, "send_welcome_email": 0, "user_type": "System User"})
	user.append("roles", {"role": role})
	user.insert(ignore_permissions=True)
	update_password(email, PASSWORD)


def _workflow() -> None:
	for state in ("Draft", "Pending Approval", "Approved", "Rejected"):
		if not frappe.db.exists("Workflow State", state):
			frappe.new_doc("Workflow State").update({"workflow_state_name": state}).insert(ignore_permissions=True)
	for action in ("Submit", "Approve", "Reject"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.new_doc("Workflow Action Master").update({"workflow_action_name": action}).insert(ignore_permissions=True)
	flow = frappe.new_doc("Workflow")
	flow.update({"workflow_name": WORKFLOW, "document_type": DOCTYPE, "is_active": 1, "workflow_state_field": "workflow_state", "send_email_alert": 0})
	for state, editor in (("Draft", OFFICER_ROLE), ("Pending Approval", MANAGER_ROLE), ("Approved", MANAGER_ROLE), ("Rejected", OFFICER_ROLE)):
		flow.append("states", {"state": state, "doc_status": "0", "allow_edit": editor})
	# Draft -> Submit (the officer) -> Pending Approval -> Approve / Reject (the manager, never their own).
	flow.append("transitions", {"state": "Draft", "action": "Submit", "next_state": "Pending Approval", "allowed": OFFICER_ROLE, "allow_self_approval": 1})
	for action, nxt in (("Approve", "Approved"), ("Reject", "Rejected")):
		flow.append("transitions", {"state": "Pending Approval", "action": action, "next_state": nxt, "allowed": MANAGER_ROLE, "allow_self_approval": 0})
	flow.insert(ignore_permissions=True)


def _requests() -> list[str]:
	from frappe.model.workflow import apply_workflow

	names = []
	frappe.set_user(OFFICER)
	try:
		for title, traveller, destination, nights, amount, purpose in REQUESTS:
			doc = frappe.new_doc(DOCTYPE)
			doc.update({"title": title, "traveller": traveller, "destination": destination, "nights": nights, "amount": amount, "purpose": purpose})
			doc.insert()
			apply_workflow(doc, "Submit")  # the officer sends it on, as in the desk
			names.append(doc.name)
	finally:
		frappe.set_user("Administrator")
	return names


def _widget(title: str, widget_type: str, **values) -> str:
	doc = frappe.new_doc("Desk Widget")
	doc.update({"title": title, "widget_type": widget_type, **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def _page() -> str:
	from seal_desk.role_center import publish

	block = "Field Travel Notice"
	if not frappe.db.exists("Custom HTML Block", block):
		frappe.new_doc("Custom HTML Block").update({"name": block, "private": 0, "html": "<p>Claims close on the 25th.</p>"}).insert(ignore_permissions=True)
	parts = [
		_widget("Field Operations Headline", "Headline"),
		_widget("Waiting for My Approval", "Standard Group", standard_group="approvals"),
		_widget("Field Travel", "Cue Group", cues=[
			{"caption": "Travel waiting", "document_type": DOCTYPE, "filters": '[["workflow_state", "=", "Pending Approval"]]'},
			{"caption": "All travel requests", "document_type": DOCTYPE},
		]),
		_widget("Latest Travel Requests", "List Part", document_type=DOCTYPE, columns='["traveller", "amount"]', page_length=5),
		_widget("Travel Notice Board", "Card Part", custom_block=block),
		_widget("Travel Policy", "Text", body="Book travel at least five working days ahead."),
	]
	page = frappe.new_doc("Desk Page")
	page.update({"title": PAGE, "priority": 90})
	page.append("roles", {"role": MANAGER_ROLE})
	for widget in parts:
		page.append("items", {"widget": widget})
	page.insert(ignore_permissions=True)
	publish.publish(page.name)
	return page.name


def seed() -> None:
	"""Everything the suite reads, in the harness's transaction (as Administrator)."""
	frappe.flags.in_test = True  # governance and similar guards let fixtures in; reset below
	try:
		for role in (MANAGER_ROLE, OFFICER_ROLE):
			_role(role)
		_person(MANAGER, "Wambui", "Njoroge", "0798614207", MANAGER_ROLE)
		_person(OFFICER, "Kipchumba", "Rotich", "0798614208", OFFICER_ROLE)
		_workflow()
		names = _requests()
		page = _page()
		from seal_common.messaging import push

		push.ensure_keys()
	finally:
		frappe.flags.in_test = False
	frappe.clear_cache()
	items = frappe.get_all("Desk Page Item", filters={"parent": page}, fields=["widget", "widget_type", "hide_on_phone"], order_by="idx")
	SEEDED.update(
		{
			"manager": MANAGER,
			"manager_name": "Wambui Njoroge",
			"officer": OFFICER,
			"password": PASSWORD,
			"doctype": DOCTYPE,
			"requests": dict(zip([r[0] for r in REQUESTS], names, strict=True)),
			"page": page,
			"page_title": PAGE,
			"page_items": items,
		}
	)


# --- asked for by the suite ---------------------------------------------------------------


def notify(user: str = MANAGER, title: str = "Garissa borehole site survey", kind: str = "Assignment") -> dict:
	"""Kipchumba assigns the manager one of his requests: Frappe's Notification Log (its hooks run)."""
	name = SEEDED["requests"][title]
	subject = f"Kipchumba Rotich assigned you {DOCTYPE} {name}: {title}"
	log = frappe.new_doc("Notification Log")
	log.update({"for_user": user, "from_user": OFFICER, "type": kind, "subject": subject, "email_content": f"<p>{title}, KES {dict((r[0], r[4]) for r in REQUESTS)[title]:,}.</p>",
	            "document_type": DOCTYPE, "document_name": name})
	log.insert(ignore_permissions=True)
	return {"log": log.name, "doctype": DOCTYPE, "name": name, "subject": subject}


def push_subscriptions() -> list[dict]:
	return frappe.get_all("Push Subscription", fields=["name", "user", "endpoint", "last_success"], order_by="creation")


def passkeys(user: str) -> list[dict]:
	return frappe.get_all("Login Passkey", filters={"user": user}, fields=["name", "label", "last_used"], order_by="creation")
