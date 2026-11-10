# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""What the My HR section of the My Desk phone app calls (HR_ON_MY_DESK.md §3, MY_DESK_P5_PLAN.md §3).

Every endpoint answers for the person signed in. Nothing takes a `user`, and nothing that
writes takes an `employee`: the person's own Employee record, its company and its approvers
are read from the session (P5-2), so a member of staff can only ever file for themselves,
and a new record never takes the creator's default company (which fails User Permissions on
a group with several companies). Records are created through the ORM as the person, so
DocType permissions, Frappe HR's controllers and this app's hooks all run, exactly as on the
desk. A record read (`*_record`) loads the document and checks read permission, so an
approver opening a colleague's record from the Approvals inbox sees it, read only.

Frappe HR calls go through this one module, so an upstream change is absorbed here
(`tests/test_my_desk_section.py` pins what it relies on). The section's bundle is built
against these names: from release they are add-only (SEAL_DEV_RULES §1.15 in spirit, P5-1).
Reads are GET and change nothing; writes are POST.

Nothing here imports seal_desk (SEAL_DEV_RULES §3.15).
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_datetime, getdate, now_datetime, nowdate, strip_html, today

LIST_LIMIT = 50

# ---------------------------------------------------------------- who is asking


def me() -> frappe._dict:
	"""The person's own active Employee record, or a refusal a person can act on."""
	row = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "employee_name", "company", "department", "designation", "image", "user_id"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Your login is not linked to a member of staff. Ask HR to link it."), frappe.PermissionError)
	return row


def _payload(value):
	"""A list or dict the phone sent as JSON text (Frappe passes form values as strings)."""
	if isinstance(value, str):
		return json.loads(value) if value.strip() else None
	return value


def _record(doctype: str, name: str):
	"""The document, if the person may read it, with any field the site hides from them blanked."""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	doc.apply_fieldlevel_read_permissions()
	for fieldname in doc.meta.get_valid_columns():
		if fieldname not in doc.__dict__:
			doc.set(fieldname, None)  # removed as hidden: read as blank, never as an error
	return doc


def _fields(doctype: str, wanted: list[str]) -> list[str]:
	"""The fields of `wanted` the person may read: a site can put any field at a permission level
	staff lack (HR often hides payment fields), and asking for it would refuse the whole list."""
	from frappe.model import get_permitted_fields

	permitted = set(get_permitted_fields(doctype))
	return [f for f in wanted if f in permitted]


def _own_list(doctype: str, employee: str, wanted: list[str], **kwargs) -> list[dict]:
	"""The person's own rows of `doctype`, newest first, with only the fields they may read; a field
	they may not read comes back blank rather than refusing the list."""
	fields = _fields(doctype, wanted)
	filters = kwargs.pop("filters", None) or {}
	if isinstance(filters, dict):
		filters = {"employee": employee, **filters}
	else:
		filters = [["employee", "=", employee], *filters]
	rows = frappe.get_list(doctype, filters=filters, fields=fields, limit_page_length=kwargs.pop("limit", LIST_LIMIT), **kwargs)
	for row in rows:
		for field in wanted:
			row.setdefault(field, None)
	return rows


def _mine(doc, employee: str | None = None) -> bool:
	employee = employee or frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	return bool(employee) and doc.get("employee") == employee


def _currency(company: str) -> str:
	return frappe.get_cached_value("Company", company, "default_currency")


def _full_name(user: str | None) -> str | None:
	return frappe.utils.get_fullname(user) if user else None


def _department_approver(employee: str, field: str, parentfield: str) -> str | None:
	"""The employee's own approver for `field`, else their department's first (Frappe HR's rule)."""
	approver, department = frappe.db.get_value("Employee", employee, [field, "department"])
	if not approver and department:
		approver = frappe.db.get_value(
			"Department Approver", {"parent": department, "parentfield": parentfield, "idx": 1}, "approver"
		)
	return approver or None


# ---------------------------------------------------------------- home


@frappe.whitelist(methods=["GET"])
def home() -> dict:
	"""My HR's first screen: who, balances, what is in flight, and whether check-in is offered."""
	from seal_hrms.my_desk.figures import balances
	from seal_hrms.seal_hrms.self_service_status import self_service

	person = me()
	user = frappe.session.user
	return {
		"employee": person,
		"balances": [{"key": b.key, "label": b.caption, "value": flt(b.value, 2)} for b in balances(user)],
		"in_flight": [
			{"key": f.key, "label": f.caption, "count": f.count, "doctype": f.doctype}
			for f in self_service(user)
			if f.count
		],
		"checkin": _checkin_settings(),
	}


# ---------------------------------------------------------------- leave


@frappe.whitelist(methods=["GET"])
def leave_list() -> list[dict]:
	"""The person's leave applications, newest first, each with its handover's state."""
	person = me()
	rows = _own_list(
		"Leave Application",
		person.name,
		["name", "leave_type", "from_date", "to_date", "total_leave_days", "status", "docstatus", "half_day", "posting_date"],
		order_by="from_date desc",
	)
	handovers = {
		r.leave_application: r
		for r in frappe.get_all(
			"Task Assignment",
			filters={"employee": person.name, "leave_application": ["in", [r.name for r in rows] or [""]], "docstatus": ["<", 2]},
			fields=["name", "leave_application", "status", "task_assignee_name"],
		)
	}
	for row in rows:
		ta = handovers.get(row.name)
		row["handover"] = {"name": ta.name, "status": ta.status, "stand_in": ta.task_assignee_name} if ta else None
	return rows


@frappe.whitelist(methods=["GET"])
def leave_options(leave_type: str | None = None, from_date: str | None = None, to_date: str | None = None, half_day: int = 0) -> dict:
	"""What the Apply for Leave screen needs: leave types with what is left, the approver, and, for a
	chosen type and dates, how many days it is and whether the handover rule covers it."""
	from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver, get_leave_details

	from seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy import OFF, WARN, applies_to, policy_for

	person = me()
	details = get_leave_details(person.name, getdate(from_date or today()))
	types = [
		{"name": name, "left": flt(d.get("remaining_leaves"), 2), "allocated": flt(d.get("total_leaves"), 2)}
		for name, d in (details.get("leave_allocation") or {}).items()
	] + [{"name": name, "left": None, "allocated": None} for name in details.get("lwps") or []]
	approver = get_employee_leave_approver(person.name)
	answer = {
		"employee": person,
		"leave_types": types,
		"approver": approver,
		"approver_name": _full_name(approver),
		"days": None,
		"handover": {"needed": False, "required": False, "rule": None},
		"work": [],
		"approvals": [],
	}
	if not (leave_type and from_date and to_date):
		return answer
	from hrms.hr.doctype.leave_application.leave_application import get_number_of_leave_days

	days = get_number_of_leave_days(person.name, leave_type, from_date, to_date, cint(half_day), from_date if cint(half_day) else None)
	policy = policy_for(person.company)
	needed = applies_to(policy, leave_type, days)
	answer["days"] = flt(days, 2)
	answer["handover"] = {"needed": needed, "required": needed and policy.requirement not in (OFF, WARN), "rule": policy.requirement}
	if needed:
		answer["work"], answer["approvals"] = _open_work(person.name)
	return answer


def _open_work(employee: str) -> tuple[list, list]:
	from seal_hrms.seal_hrms.acting import suggest_authorities
	from seal_hrms.seal_hrms.doctype.task_assignment.task_assignment import get_employee_tasks

	try:
		work = [
			{"todo": t.name, "description": strip_html(t.description or ""), "due_date": t.date, "reference_type": t.reference_type, "reference_name": t.reference_name}
			for t in get_employee_tasks(employee)
		]
	except frappe.ValidationError:
		frappe.clear_last_message()  # no login, so no work list: the handover has notes only
		work = []
	return work, suggest_authorities(employee)


@frappe.whitelist(methods=["GET"])
def colleagues(txt: str | None = None) -> list[dict]:
	"""Who could cover: active, in the same company, not the person (Task Assignment's own rule)."""
	from seal_hrms.seal_hrms.doctype.task_assignment.task_assignment import get_assignable_employees

	person = me()
	rows = get_assignable_employees("Employee", txt or "", "employee_name", 0, 200, {"employee": person.name})
	return [{"name": name, "employee_name": employee_name} for name, employee_name in rows]


@frappe.whitelist(methods=["POST"])
def apply_for_leave(
	leave_type: str,
	from_date: str,
	to_date: str,
	description: str | None = None,
	half_day: int = 0,
	stand_in: str | None = None,
	handover_notes: str | None = None,
	todos=None,
	approvals=None,
) -> dict:
	"""Apply for leave and, in the same step, send the handover to the stand-in (P5-5).

	The application is saved as an Open draft for the leave approver, as on the desk. Where the
	company's handover rule covers this leave and requires cover, a stand-in is required; under
	"Warn" it is optional. One transaction: if the handover is refused, so is the application.
	"""
	from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

	from seal_hrms.seal_hrms.doctype.task_assignment_policy.task_assignment_policy import OFF, WARN, applies_to, policy_for

	person = me()
	doc = frappe.new_doc("Leave Application")
	doc.update({
		"employee": person.name,
		"company": person.company,
		"leave_type": leave_type,
		"from_date": from_date,
		"to_date": to_date,
		"half_day": cint(half_day),
		"half_day_date": from_date if cint(half_day) else None,
		"description": description,
		"posting_date": today(),
		"status": "Open",
		"leave_approver": get_employee_leave_approver(person.name),
	})
	doc.insert()
	policy = policy_for(person.company)
	if applies_to(policy, doc.leave_type, doc.total_leave_days) and policy.requirement not in (OFF, WARN) and not stand_in:
		frappe.throw(_("Your company asks for cover on this leave. Choose who will cover your work."), title=_("Stand-in Needed"))
	handover = _send_handover(doc.name, stand_in, handover_notes, _payload(todos) or [], _payload(approvals) or []) if stand_in else None
	return {"name": doc.name, "handover": handover}


def _send_handover(leave_application: str, stand_in: str, notes: str | None, todos: list, approvals: list) -> str:
	"""Prepare the handover from the leave, keep the work and approvals chosen, and send it."""
	from seal_hrms.seal_hrms.task_assignment_actions import prepare_from_leave

	name = prepare_from_leave(leave_application)
	ta = frappe.get_doc("Task Assignment", name)
	ta.task_assignee = stand_in
	ta.task_description = frappe.utils.escape_html((notes or "").strip()) or _("Notes are on the leave application.")
	chosen = set(todos)
	ta.set("assignment_todos", [row for row in ta.assignment_todos if row.todo in chosen])
	kinds = set(approvals)
	ta.set("authorities", [row for row in ta.get("authorities") or [] if row.authority in kinds])
	ta.save()
	ta.submit()
	return ta.name


@frappe.whitelist(methods=["GET"])
def leave_record(name: str) -> dict:
	"""One leave application and its handover."""
	doc = _record("Leave Application", name)
	ta = frappe.db.get_value(
		"Task Assignment", {"leave_application": doc.name, "docstatus": ["<", 2]}, ["name", "status", "task_assignee_name"], as_dict=True
	)
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"leave_type": doc.leave_type,
		"from_date": doc.from_date,
		"to_date": doc.to_date,
		"total_leave_days": doc.total_leave_days,
		"half_day": doc.half_day,
		"description": doc.description,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"leave_approver_name": _full_name(doc.leave_approver),
		"posting_date": doc.posting_date,
		"mine": _mine(doc),
		"handover": {"name": ta.name, "status": ta.status, "stand_in": ta.task_assignee_name} if ta else None,
	}


# ---------------------------------------------------------------- cover


@frappe.whitelist(methods=["GET"])
def cover() -> dict:
	"""Handovers that ask the person to cover, those they cover now, and their own."""
	from seal_hrms.seal_hrms.handover import Answer, Status, covered_by, stand_ins

	person = me()
	answerable = (Status.AWAITING, Status.ACCEPTED, Status.DECLINED)
	to_answer, covering = [], []
	for name in frappe.get_all(
		"Task Assignment",
		filters=[["docstatus", "=", 1], ["status", "in", [*answerable, Status.ACTIVE]], ["employee", "!=", person.name]],
		pluck="name",
		order_by="leave_from asc",
	):
		doc = frappe.get_doc("Task Assignment", name)
		if person.name not in stand_ins(doc):
			continue
		row = _cover_row(doc)
		if doc.status == Status.ACTIVE:
			covering.append(row)
			continue
		waiting = (doc.task_assignee == person.name and doc.acceptance == Answer.PENDING) or any(
			covered_by(doc, r) == person.name and r.get("acceptance") == Answer.PENDING
			for r in [*doc.assignment_todos, *(doc.get("authorities") or [])]
		)
		row["waiting_for_me"] = waiting
		to_answer.append(row)
	mine = [
		_cover_row(frappe.get_doc("Task Assignment", n))
		for n in frappe.get_all(
			"Task Assignment", filters={"employee": person.name, "docstatus": ["<", 2]}, pluck="name", order_by="leave_from desc", limit=20
		)
	]
	return {"to_answer": to_answer, "covering": covering, "mine": mine}


def _cover_row(doc) -> dict:
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"stand_in": doc.task_assignee_name,
		"leave_from": doc.leave_from,
		"leave_to": doc.leave_to,
		"return_date": doc.return_date,
		"status": doc.status,
		"docstatus": doc.docstatus,
	}


@frappe.whitelist(methods=["GET"])
def handover_record(name: str) -> dict:
	"""One handover, from where the person stands: owner, stand-in, or a reader (approver, HR)."""
	from seal_hrms.seal_hrms.handover import Answer, Status, covered_by, stand_ins

	doc = _record("Task Assignment", name)
	person = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	names = {}

	def who(employee):
		if employee and employee not in names:
			names[employee] = frappe.db.get_value("Employee", employee, "employee_name")
		return names.get(employee)

	answerable = doc.docstatus == 1 and doc.status in (Status.AWAITING, Status.ACCEPTED, Status.DECLINED)
	work = [
		{
			"row": r.name,
			"description": strip_html(r.description or ""),
			"due_date": r.due_date,
			"covered_by": who(covered_by(doc, r)),
			"mine": covered_by(doc, r) == person,
			"answers_itself": bool(r.get("task_assignee")) and r.task_assignee != doc.task_assignee,
			"acceptance": r.acceptance,
			"progress": r.row_status,
			"notes": r.stand_in_notes,
		}
		for r in doc.assignment_todos
	]
	approvals = [
		{
			"row": r.name,
			"label": r.authority_label or r.authority,
			"covered_by": who(covered_by(doc, r)),
			"mine": covered_by(doc, r) == person,
			"acceptance": r.acceptance,
		}
		for r in doc.get("authorities") or []
	]
	is_owner = doc.employee == person
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"leave_application": doc.leave_application,
		"leave_from": doc.leave_from,
		"leave_to": doc.leave_to,
		"return_date": doc.return_date,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"stand_in": doc.task_assignee_name,
		"main_stand_in_is_me": doc.task_assignee == person,
		"acceptance": doc.acceptance,
		"decline_reason": doc.decline_reason,
		"notes": strip_html(doc.task_description or ""),
		"return_note": strip_html(doc.return_summary or ""),
		"work": work,
		"approvals": approvals,
		"is_owner": is_owner,
		"is_stand_in": bool(person) and person in stand_ins(doc),
		"can_answer": answerable and (doc.task_assignee == person or any(w["mine"] for w in work) or any(a["mine"] for a in approvals)),
		"can_return": is_owner and doc.status == Status.ACTIVE,
		"answered": doc.task_assignee == person and doc.acceptance in (Answer.ACCEPTED, Answer.DECLINED),
	}


# ---------------------------------------------------------------- time off in lieu


@frappe.whitelist(methods=["GET"])
def toil_list() -> dict:
	"""The person's claims, what is left and lapsing, and how their company takes claims."""
	from seal_hrms.my_desk.figures import _toil_policy, lapsing

	person = me()
	policy = _toil_policy(person.name)
	claims = _own_list(
		"Time Off in Lieu Claim",
		person.name,
		["name", "status", "docstatus", "total_hours", "days", "days_left", "lapses_on", "creation"],
		filters={"docstatus": ["<", 2]},
		order_by="creation desc",
	)
	left = lapse = 0.0
	first = None
	if policy:
		from seal_hrms.seal_hrms.toil.ledger import held

		left = flt(held(person.name, policy.leave_type), 2)
		lapse, first = lapsing(person.name, getdate(), 30)
	return {
		"employee": person.name,
		"eligible": bool(policy),
		"leave_type": policy.leave_type if policy else None,
		"mode": policy.prior_authorisation if policy else None,
		"from_attendance": bool(policy and policy.evidence_attendance),
		"from_timesheets": bool(policy and policy.evidence_timesheets),
		"left": left,
		"lapsing": lapse,
		"first_lapse": first,
		"claims": claims,
	}


@frappe.whitelist(methods=["GET"])
def toil_record(name: str) -> dict:
	"""One claim with its lines, where it is (Now / Next / Do, as plain text) and what the person may do."""
	from frappe.model.workflow import get_transitions

	from seal_hrms.seal_hrms.toil import workflow as wf
	from seal_hrms.seal_hrms.toil.stage import where_it_is

	doc = _record("Time Off in Lieu Claim", name)
	stage = where_it_is(doc)
	mine = _mine(doc)
	try:
		actions = [t.action for t in get_transitions(doc)] if doc.docstatus == 0 else []
	except frappe.ValidationError:
		frappe.clear_last_message()
		actions = []
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"mode": doc.mode,
		"approver_name": doc.approver_name,
		"note": doc.note,
		"decision_note": doc.decision_note,
		"total_hours": doc.total_hours,
		"credited_hours": doc.credited_hours,
		"days": doc.days,
		"days_left": doc.days_left,
		"lapses_on": doc.lapses_on,
		"leave_type": doc.leave_type,
		"lines": [
			{
				"work_date": line.work_date,
				"hours": line.hours,
				"planned_hours": line.planned_hours,
				"work_done": line.work_done,
				"day_kind": line.day_kind,
				"credited_hours": line.credited_hours,
				"supported_by": line.supported_by,
			}
			for line in doc.lines
		],
		"stage": {"tone": stage.get("type"), "items": [{"label": i["label"], "text": strip_html(i["text"])} for i in stage.get("items", [])]},
		"mine": mine,
		"can_edit": mine and doc.docstatus == 0 and doc.status in (wf.DRAFT, wf.RETURNED, wf.AUTHORISED),
		"actions": [a for a in actions if a in (wf.SEND, wf.SEND_AUTH)] if mine else [],
	}


@frappe.whitelist(methods=["POST"])
def save_toil_claim(lines, note: str | None = None, name: str | None = None) -> str:
	"""Create the person's claim, or change their draft: a list of days, each with hours and what the work was."""
	lines = _payload(lines) or []
	person = me()
	if name:
		doc = frappe.get_doc("Time Off in Lieu Claim", name)
		if doc.employee != person.name:
			frappe.throw(_("You can only change your own claims."), frappe.PermissionError)
	else:
		doc = frappe.new_doc("Time Off in Lieu Claim")
		doc.employee = person.name
		doc.company = person.company
	doc.note = note
	doc.set("lines", [])
	for line in lines:
		doc.append("lines", {
			"work_date": line.get("work_date"),
			"hours": flt(line.get("hours")) or None,
			"planned_hours": flt(line.get("planned_hours")) or None,
			"work_done": line.get("work_done"),
		})
	doc.save()
	return doc.name


@frappe.whitelist(methods=["POST"])
def toil_action(name: str, action: str) -> str:
	"""Send the person's claim on: for authorisation or approval, through the claim's Frappe Workflow."""
	from frappe.model.workflow import apply_workflow

	from seal_hrms.seal_hrms.toil import workflow as wf

	if action not in (wf.SEND, wf.SEND_AUTH):
		frappe.throw(_("Decide claims from Approvals."))
	doc = frappe.get_doc("Time Off in Lieu Claim", name)
	if not _mine(doc):
		frappe.throw(_("You can only send your own claims."), frappe.PermissionError)
	return apply_workflow(doc, action).status


# ---------------------------------------------------------------- timesheets


@frappe.whitelist(methods=["GET"])
def timesheets() -> dict:
	"""The person's recent timesheets, and whether their company keeps them by the week."""
	from seal_hrms.seal_hrms.working_time.policy import policy_for

	person = me()
	policy = policy_for(person.company)
	fields = ["name", "start_date", "end_date", "total_hours", "status", "docstatus"]
	meta = frappe.get_meta("Timesheet")
	fields += [f for f in ("custom_week_start", "custom_approval_state") if meta.has_field(f)]
	return {
		"weekly": bool(policy.weekly_timesheets),
		"timesheets": _own_list("Timesheet", person.name, fields, filters={"docstatus": ["<", 2]}, order_by="start_date desc"),
	}


@frappe.whitelist(methods=["GET"])
def timesheet_week(week_start: str | None = None) -> dict:
	"""A week for the phone: the person's timesheet for it (if any), its lines, the days, last week's lines."""
	from seal_hrms.seal_hrms.timesheets import approval
	from seal_hrms.seal_hrms.timesheets.claim import candidates
	from seal_hrms.seal_hrms.timesheets.week import entries_of, monday_of, week_context

	person = me()
	start = monday_of(week_start or today())
	name = frappe.db.get_value("Timesheet", {"employee": person.name, "custom_week_start": start, "docstatus": ["<", 2]}, "name")
	context = week_context(person.name, str(start), name)
	sheet = None
	if name:
		doc = _record("Timesheet", name)
		state = doc.get("custom_approval_state") or approval.NOT_SENT
		sheet = {
			"name": doc.name,
			"docstatus": doc.docstatus,
			"state": state,
			"return_reason": doc.get("custom_return_reason"),
			"approver_name": _full_name(doc.get("custom_approver")),
			"entries": entries_of(doc),
			"total_hours": doc.total_hours,
			"can_edit": doc.docstatus == 0 and state in (approval.NOT_SENT, approval.RETURNED),
			"can_send": doc.docstatus == 0 and approval.applies(doc) and state in (approval.NOT_SENT, approval.RETURNED),
			"can_claim": bool(candidates(doc)) if doc.docstatus == 1 else False,
		}
	activity_types = frappe.get_list("Activity Type", filters={"disabled": 0}, pluck="name", order_by="name asc", limit_page_length=200)
	return {**context, "timesheet": sheet, "activity_types": activity_types, "approval": bool(context.get("weekly")) and not approval.site_workflow()}


@frappe.whitelist(methods=["GET"])
def timesheet_record(name: str) -> dict:
	"""One timesheet, read only: its lines by day. A weekly one of the person's own opens in the week screen."""
	from seal_hrms.seal_hrms.timesheets import approval

	doc = _record("Timesheet", name)
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"start_date": doc.start_date,
		"end_date": doc.end_date,
		"total_hours": doc.total_hours,
		"docstatus": doc.docstatus,
		"status": doc.status,
		"state": doc.get("custom_approval_state") or approval.NOT_SENT,
		"week_start": doc.get("custom_week_start"),
		"mine": _mine(doc),
		"lines": [
			{"date": getdate(t.from_time) if t.from_time else None, "activity_type": t.activity_type, "hours": t.hours, "description": t.description}
			for t in doc.time_logs
		],
	}


@frappe.whitelist(methods=["POST"])
def save_timesheet_week(week_start: str, entries, send: int = 0) -> dict:
	"""Save the person's week (and send it for approval when asked). Lines are written from the week on save."""
	from seal_hrms.seal_hrms.timesheets import approval
	from seal_hrms.seal_hrms.timesheets.week import monday_of
	from seal_hrms.seal_hrms.working_time.policy import policy_for

	person = me()
	if not policy_for(person.company).weekly_timesheets:
		frappe.throw(_("{0} does not keep weekly timesheets. Fill your timesheet in on a computer.").format(person.company))
	start = monday_of(week_start)
	name = frappe.db.get_value("Timesheet", {"employee": person.name, "custom_week_start": start, "docstatus": ["<", 2]}, "name")
	if name:
		doc = frappe.get_doc("Timesheet", name)
		if doc.docstatus != 0 or (doc.get("custom_approval_state") or approval.NOT_SENT) not in (approval.NOT_SENT, approval.RETURNED):
			frappe.throw(_("This week has been sent. It can be changed only if it is returned to you."))
	else:
		doc = frappe.new_doc("Timesheet")
		doc.employee = person.name
		doc.company = person.company
		doc.custom_week_start = start
	doc.custom_week_entries = json.dumps(_payload(entries) or [])
	doc.save()
	if cint(send):
		approval.send_for_approval(doc.name)
	return {"name": doc.name, "state": frappe.db.get_value("Timesheet", doc.name, "custom_approval_state")}


@frappe.whitelist(methods=["POST"])
def timesheet_claim(name: str) -> str:
	"""A draft time off claim from an approved timesheet's extra hours; the phone opens it next."""
	from seal_hrms.seal_hrms.timesheets.claim import make_toil_claim

	claim = make_toil_claim(name)
	lines = [{k: line.get(k) for k in ("work_date", "hours", "planned_hours", "work_done")} for line in claim.get("lines") or []]
	doc = frappe.get_doc("Time Off in Lieu Claim", save_toil_claim(lines, claim.get("note")))
	for line, source in zip(doc.lines, claim.get("lines") or [], strict=False):
		line.timesheet = source.get("timesheet")
	doc.save()
	return doc.name


# ---------------------------------------------------------------- expenses and advances


@frappe.whitelist(methods=["GET"])
def expense_list() -> list[dict]:
	person = me()
	return _own_list(
		"Expense Claim",
		person.name,
		["name", "posting_date", "total_claimed_amount", "total_sanctioned_amount", "currency", "approval_status", "status", "docstatus", "creation"],
		filters={"docstatus": ["<", 2]},
		order_by="creation desc",
	)


@frappe.whitelist(methods=["GET"])
def expense_options() -> dict:
	"""Kinds of expense, the currency, and who approves."""
	person = me()
	approver = _department_approver(person.name, "expense_approver", "expense_approvers")
	return {
		"types": frappe.get_list("Expense Claim Type", fields=["name", "description"], order_by="name asc", limit_page_length=200),
		"currency": _currency(person.company),
		"approver_name": _full_name(approver),
	}


@frappe.whitelist(methods=["POST"])
def claim_expenses(lines, remark: str | None = None) -> str:
	"""A new expense claim for the person, waiting for their expense approver. Receipts are attached after."""
	from hrms.hr.doctype.expense_claim.expense_claim import get_default_payable_account, get_expense_claim_account_and_cost_center

	lines = _payload(lines) or []
	if not lines:
		frappe.throw(_("Add at least one expense."))
	person = me()
	doc = frappe.new_doc("Expense Claim")
	doc.update({
		"employee": person.name,
		"company": person.company,
		"posting_date": today(),
		"currency": _currency(person.company),
		"exchange_rate": 1,
		"expense_approver": _department_approver(person.name, "expense_approver", "expense_approvers"),
		"payable_account": get_default_payable_account(person.company),
		"cost_center": frappe.get_cached_value("Company", person.company, "cost_center"),
		"remark": remark,
	})
	for line in lines:
		amount = flt(line.get("amount"))
		# What the desk form fills on each row (Frappe HR's expense_claim.js: the type's account and the
		# company's cost centre): without them the approver's approval is refused ("Cost Center is
		# required"), found by the P6 walk in the real shell.
		booking = get_expense_claim_account_and_cost_center(line.get("expense_type"), person.company) if line.get("expense_type") else {}
		doc.append("expenses", {
			"expense_date": line.get("expense_date") or today(),
			"expense_type": line.get("expense_type"),
			"description": line.get("description"),
			"amount": amount,
			"sanctioned_amount": amount,
			"default_account": booking.get("account"),
			"cost_center": doc.cost_center or booking.get("cost_center"),
		})
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["GET"])
def expense_record(name: str) -> dict:
	doc = _record("Expense Claim", name)
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"posting_date": doc.posting_date,
		"currency": doc.currency,
		"total_claimed_amount": doc.total_claimed_amount,
		"total_sanctioned_amount": doc.total_sanctioned_amount,
		"approval_status": doc.approval_status,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"approver_name": _full_name(doc.expense_approver),
		"remark": doc.remark,
		"mine": _mine(doc),
		"expenses": [
			{"expense_date": e.expense_date, "expense_type": e.expense_type, "description": e.description, "amount": e.amount, "sanctioned_amount": e.sanctioned_amount}
			for e in doc.expenses
		],
		"receipts": _attachments("Expense Claim", doc.name),
	}


def _attachments(doctype: str, name: str) -> list[dict]:
	return frappe.get_all(
		"File", filters={"attached_to_doctype": doctype, "attached_to_name": name}, fields=["name", "file_name", "file_url", "is_private"], order_by="creation asc"
	)


@frappe.whitelist(methods=["GET"])
def advance_list() -> list[dict]:
	"""The person's advances and what is left to settle on each."""
	person = me()
	rows = _own_list(
		"Employee Advance",
		person.name,
		["name", "posting_date", "purpose", "advance_amount", "paid_amount", "claimed_amount", "return_amount", "currency", "status", "docstatus", "creation"],
		filters={"docstatus": ["<", 2]},
		order_by="creation desc",
	)
	for row in rows:
		row["to_settle"] = flt(row.paid_amount) - flt(row.claimed_amount) - flt(row.return_amount)
	return rows


@frappe.whitelist(methods=["POST"])
def request_advance(purpose: str, amount: float) -> str:
	"""A new advance request for the person, in their company's currency."""
	person = me()
	if flt(amount) <= 0:
		frappe.throw(_("Enter the amount you need."))
	doc = frappe.new_doc("Employee Advance")
	doc.update({
		"employee": person.name,
		"company": person.company,
		"posting_date": today(),
		"purpose": purpose,
		"advance_amount": flt(amount),
		"currency": _currency(person.company),
		"exchange_rate": 1,
	})
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["GET"])
def advance_record(name: str) -> dict:
	doc = _record("Employee Advance", name)
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"posting_date": doc.posting_date,
		"purpose": doc.purpose,
		"currency": doc.currency,
		"advance_amount": doc.advance_amount,
		"paid_amount": doc.paid_amount,
		"claimed_amount": doc.claimed_amount,
		"return_amount": doc.return_amount,
		"to_settle": flt(doc.paid_amount) - flt(doc.claimed_amount) - flt(doc.return_amount),
		"status": doc.status,
		"docstatus": doc.docstatus,
		"mine": _mine(doc),
	}


# ---------------------------------------------------------------- pay


@frappe.whitelist(methods=["GET"])
def payslips() -> list[dict]:
	person = me()
	return _own_list(
		"Salary Slip",
		person.name,
		["name", "start_date", "end_date", "posting_date", "gross_pay", "total_deduction", "net_pay", "currency"],
		filters={"docstatus": 1},
		order_by="end_date desc",
		limit=24,
	)


@frappe.whitelist(methods=["GET"])
def payslip_record(name: str) -> dict:
	doc = _record("Salary Slip", name)
	return {
		"name": doc.name,
		"employee_name": doc.employee_name,
		"start_date": doc.start_date,
		"end_date": doc.end_date,
		"posting_date": doc.posting_date,
		"currency": doc.currency,
		"gross_pay": doc.gross_pay,
		"total_deduction": doc.total_deduction,
		"net_pay": doc.net_pay,
		"earnings": [{"component": r.salary_component, "amount": r.amount} for r in doc.earnings],
		"deductions": [{"component": r.salary_component, "amount": r.amount} for r in doc.deductions],
		"print_format": payslip_print_format(),
	}


def payslip_print_format() -> str:
	"""The client's own default print format for Salary Slip, else Standard (PWA-7)."""
	chosen = frappe.get_meta("Salary Slip").default_print_format
	if chosen and frappe.db.get_value("Print Format", chosen, "disabled") == 0:
		return chosen
	return "Standard"


@frappe.whitelist(methods=["GET"])
def payslip_pdf(name: str) -> None:
	"""The slip as a PDF, as the person, in the site's default print format for Salary Slip. Never cached."""
	from frappe.utils.print_format import download_pdf

	doc = _record("Salary Slip", name)
	doc.check_permission("print")
	download_pdf("Salary Slip", doc.name, format=payslip_print_format())


# ---------------------------------------------------------------- check-in (PWA-5)


def _checkin_settings() -> dict:
	settings = frappe.db.get_singles_dict("HR Settings", cast=True)
	return {
		"offered": bool(settings.get("allow_employee_checkin_from_mobile_app")),
		"location": bool(settings.get("allow_geolocation_tracking")),
	}


@frappe.whitelist(methods=["GET"])
def checkin_status() -> dict:
	"""Today's check-ins (the phone's and any device's), and whether the next is In or Out."""
	person = me()
	start = get_datetime(nowdate())
	# Filtered on the person's own record; `time` sits at a permission level staff may lack, so
	# the filter reads it here rather than through get_list (SEAL_DEV_RULES §2.8: the filter is the control).
	rows = frappe.get_all(
		"Employee Checkin",
		filters=[["employee", "=", person.name], ["time", ">=", start], ["time", "<", add_days(start, 1)]],
		fields=["name", "log_type", "time", "device_id"],
		order_by="time asc",
	)
	last = rows[-1].log_type if rows else None
	return {**_checkin_settings(), "today": rows, "next": "OUT" if last == "IN" else "IN"}


@frappe.whitelist(methods=["POST"])
def check_in(log_type: str, latitude: float | None = None, longitude: float | None = None) -> dict:
	"""Record an In or Out now, with where the phone is when HR asks for it and the phone shares it (P5-6)."""
	if log_type not in ("IN", "OUT"):
		frappe.throw(_("Check in or out."))
	settings = _checkin_settings()
	if not settings["offered"]:
		frappe.throw(_("HR has not turned on checking in from the phone."), title=_("Check-in Off"))
	person = me()
	doc = frappe.new_doc("Employee Checkin")
	doc.update({"employee": person.name, "log_type": log_type, "time": now_datetime(), "device_id": _("My Desk phone app")})
	if settings["location"] and latitude is not None and longitude is not None:
		doc.latitude, doc.longitude = flt(latitude), flt(longitude)
	doc.insert()
	return {"name": doc.name, "log_type": doc.log_type, "time": doc.time}


# ---------------------------------------------------------------- attendance and shift requests


@frappe.whitelist(methods=["GET"])
def attendance_requests() -> dict:
	person = me()
	return {
		"attendance": _own_list(
			"Attendance Request",
			person.name,
			["name", "from_date", "to_date", "reason", "explanation", "half_day", "docstatus"],
			order_by="from_date desc",
		),
		"shifts": _own_list(
			"Shift Request", person.name, ["name", "shift_type", "from_date", "to_date", "status", "docstatus"], order_by="from_date desc"
		),
	}


@frappe.whitelist(methods=["GET"])
def attendance_options() -> dict:
	person = me()
	approver = _department_approver(person.name, "shift_request_approver", "shift_request_approver")
	return {
		"reasons": ["Work From Home", "On Duty"],
		"shift_types": frappe.get_list("Shift Type", pluck="name", order_by="name asc", limit_page_length=100),
		"shift_approver_name": _full_name(approver),
		"has_shift_approver": bool(approver),
	}


@frappe.whitelist(methods=["POST"])
def request_attendance(from_date: str, to_date: str, reason: str, explanation: str | None = None, half_day: int = 0) -> str:
	"""An attendance request for days worked away from the office; HR submits it."""
	person = me()
	doc = frappe.new_doc("Attendance Request")
	doc.update({
		"employee": person.name,
		"company": person.company,
		"from_date": from_date,
		"to_date": to_date,
		"reason": reason,
		"explanation": explanation,
		"half_day": cint(half_day),
		"half_day_date": from_date if cint(half_day) else None,
	})
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["POST"])
def request_shift(shift_type: str, from_date: str, to_date: str | None = None) -> str:
	"""A shift request to the person's shift approver."""
	person = me()
	approver = _department_approver(person.name, "shift_request_approver", "shift_request_approver")
	if not approver:
		frappe.throw(_("Nobody approves your shift requests yet. Ask HR to set a shift approver."), title=_("No Approver"))
	doc = frappe.new_doc("Shift Request")
	doc.update({
		"employee": person.name,
		"company": person.company,
		"shift_type": shift_type,
		"from_date": from_date,
		"to_date": to_date,
		"approver": approver,
		"status": "Draft",
	})
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["GET"])
def attendance_record(doctype: str, name: str) -> dict:
	"""One attendance or shift request."""
	if doctype not in ("Attendance Request", "Shift Request"):
		frappe.throw(_("Not a request this screen shows."))
	doc = _record(doctype, name)
	keep = ("name", "employee_name", "from_date", "to_date", "reason", "explanation", "half_day", "shift_type", "status", "docstatus")
	answer = {k: doc.get(k) for k in keep}
	answer["approver_name"] = _full_name(doc.get("approver"))
	answer["mine"] = _mine(doc)
	return answer


# ---------------------------------------------------------------- my details and payout


def mask(value: str | None) -> str | None:
	"""Only the last four characters, the rest as dots: enough to recognise, not enough to use (P5-3)."""
	text = "".join((value or "").split())
	if not text:
		return None
	return "•••• " + text[-4:] if len(text) > 4 else "•" * len(text)


@frappe.whitelist(methods=["GET"])
def my_details() -> dict:
	"""The person's own details, contact, dependants and beneficiaries, and where they are paid (masked)."""
	from seal_hrms.seal_hrms.payout_change import DOCTYPE, OPEN, current_details

	person = me()
	emp = frappe.db.get_value(
		"Employee",
		person.name,
		["employee_name", "designation", "department", "company", "date_of_joining", "company_email", "personal_email", "custom_contact"],
		as_dict=True,
	)
	now = current_details(person.name)
	dependants = (
		frappe.get_all(
			"Employee Dependent and Beneficiary",
			filters={"employee": person.name},
			fields=["name", "full_name", "type", "relationship", "dob"],
			order_by="full_name asc",
		)
		if frappe.db.exists("DocType", "Employee Dependent and Beneficiary")
		else []
	)
	pending = None
	if frappe.db.table_exists(DOCTYPE):
		pending = frappe.db.get_value(DOCTYPE, {"employee": person.name, "status": ["in", list(OPEN)]}, ["name", "status", "change"], as_dict=True)
	return {
		"employee": {**person, **emp, "custom_contact": None},
		"mobile_no": mask(now.mobile_no),
		"has_contact": bool(emp.custom_contact),
		"dependants": dependants,
		"payout": {
			"bank": now.bank,
			"account_name": now.account_name,
			"account_no": mask(now.bank_account_no),
			"mobile_no": mask(now.mobile_no),
		},
		"payout_request": pending,
		"payout_requests": _own_list(DOCTYPE, person.name, ["name", "status", "change", "creation"], order_by="creation desc", limit=10)
		if frappe.db.table_exists(DOCTYPE)
		else [],
	}


@frappe.whitelist(methods=["POST"])
def update_my_contact(mobile_no: str) -> dict:
	"""Change the person's own mobile number on their Contact (kept, not overwritten: `api.update_employee_contact`)."""
	from seal_hrms.seal_hrms.api import update_employee_contact

	person = me()
	update_employee_contact(person.name, mobile_no=mobile_no)
	return {"mobile_no": mask(frappe.db.get_value("Employee", person.name, "cell_number"))}


@frappe.whitelist(methods=["GET"])
def payout_options() -> dict:
	"""Banks to choose from, and the request's two kinds."""
	# get_all, not get_list (SEAL_DEV_RULES §2.8, inverted on purpose): staff cannot read Bank, and a
	# refusal here broke the whole Request a Change screen, Mobile Money included (P6 walk, P6-7).
	# Only the banks' names leave, which are public; nothing else of the record.
	return {"banks": frappe.get_all("Bank", pluck="name", order_by="name asc", limit_page_length=500), "changes": ["Bank Account", "Mobile Money"]}


@frappe.whitelist(methods=["POST"])
def request_payout_change(
	change: str,
	bank: str | None = None,
	bank_account_no: str | None = None,
	branch_code: str | None = None,
	account_name: str | None = None,
	mobile_no: str | None = None,
	reason: str | None = None,
) -> str:
	"""A Draft request for the person (company from their record). The phone attaches the evidence to it,
	then sends it with `payout_change.send`, which asks for a fresh check (P5-4)."""
	from seal_hrms.seal_hrms.payout_change import DOCTYPE

	person = me()
	doc = frappe.new_doc(DOCTYPE)
	doc.update({
		"employee": person.name,
		"company": person.company,
		"change": change,
		"bank": bank,
		"bank_account_no": bank_account_no,
		"branch_code": branch_code,
		"account_name": account_name,
		"mobile_no": mobile_no,
		"reason": reason,
	})
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["POST"])
def set_payout_evidence(name: str, file_url: str) -> None:
	"""Put the uploaded bank letter on the person's Draft request (the upload attached the file to it)."""
	from seal_hrms.seal_hrms.payout_change import DOCTYPE, DRAFT

	doc = frappe.get_doc(DOCTYPE, name)
	if not _mine(doc) or doc.status != DRAFT:
		frappe.throw(_("Only your own unsent request can be changed."), frappe.PermissionError)
	if not frappe.db.exists("File", {"file_url": file_url, "attached_to_doctype": DOCTYPE, "attached_to_name": name}):
		frappe.throw(_("Upload the evidence to this request first."))
	doc.evidence = file_url
	doc.save()


@frappe.whitelist(methods=["GET"])
def payout_request_record(name: str) -> dict:
	"""One payout change request, with every account and number masked."""
	from seal_hrms.seal_hrms.payout_change import DOCTYPE

	doc = _record(DOCTYPE, name)
	return {
		"name": doc.name,
		"status": doc.status,
		"change": doc.change,
		"bank": doc.bank,
		"account_name": doc.account_name,
		"account_no": mask(doc.bank_account_no),
		"mobile_no": mask(doc.mobile_no),
		"provider": doc.provider,
		"reason": doc.reason,
		"has_evidence": bool(doc.evidence),
		"sent_on": doc.sent_on,
		"effective_from": doc.effective_from,
		"decision_note": doc.decision_note,
		"decided_on": doc.decided_on,
		"mine": _mine(doc),
	}
