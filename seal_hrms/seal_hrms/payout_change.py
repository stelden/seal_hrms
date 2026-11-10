# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Payout Change Request: a member of staff asks to be paid somewhere else, and HR confirms it.

Changing where pay goes is the change a thief wants most, so (HR_ON_MY_DESK.md §2.7):

  * **sending** needs a fresh check of who is asking (`step_up`, where the site has
    one), and tells the OLD number by text and the OLD address by email, so the real
    person hears of a change they did not ask for; HR is told too;
  * **nothing is paid differently until HR approves**: approval is by an HR Manager
    who is not the person asking, after a fresh check, and only then are the details
    put where payroll reads them;
  * the old Bank Account is kept, only no longer the default, so history still reads.

Statuses move only through the endpoints below, under an in-process flag
(SEAL_DEV_RULES §3.2); a direct edit of a sent request is refused. Each endpoint
checks its caller first (§2.15). Approval puts the details on the Employee through
the same rules as the Employee form: the Bank Account must be this employee's
(`overrides.employee`), the Contact must be their own User's (`api`).

Decisions taken without Keith are P4-3 to P4-6 and P4-14 in `dev_notes/seal_hrms/DESIGN.md`;
Keith decided P4-7 (approval is the governed change) and P4-10 (HR Managers of the
employee's company are told) on 2026-11-11.
"""

from __future__ import annotations

import re
from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import add_days, get_link_to_form, get_url_to_form, getdate, now_datetime, today

from seal_hrms.seal_hrms import notify, step_up
from seal_hrms.seal_hrms.handover import user_for_employee

DOCTYPE = "Payout Change Request"
DRAFT, WAITING, APPROVED, REJECTED, WITHDRAWN = "Draft", "Waiting for HR", "Approved", "Rejected", "Withdrawn"
BANK, MOBILE = "Bank Account", "Mobile Money"
OPEN = (DRAFT, WAITING)
DECIDER_ROLE = "HR Manager"
BACKOFFICE_ROLES = {"HR User", "HR Manager", "System Manager"}
FLAG = "seal_payout_change_transition"
BANK_FIELDS = ("bank", "bank_account_no", "branch_code", "account_name", "evidence")
MOBILE_FIELDS = ("mobile_no", "provider")
#: The text the old number receives (HR_ON_MY_DESK §2.7).
NOTICE = "A change to where your pay goes was requested in My Desk. If this wasn't you, call HR."


@contextmanager
def transition(name: str):
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = name
	try:
		yield
	finally:
		frappe.flags[FLAG] = previous


def _in_transition(doc) -> bool:
	return bool(doc.name) and frappe.flags.get(FLAG) == doc.name


def is_backoffice(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user == "Administrator" or bool(set(frappe.get_roles(user)) & BACKOFFICE_ROLES)


def own_employee(user: str | None = None) -> str | None:
	return frappe.db.get_value("Employee", {"user_id": user or frappe.session.user}, "name")


def is_requester(doc, user: str | None = None) -> bool:
	"""The person the request is about, or whoever raised it."""
	user = user or frappe.session.user
	return user_for_employee(doc.employee) == user or doc.owner == user


def can_decide(doc, user: str | None = None) -> bool:
	"""An HR Manager who is neither the employee nor the person who raised it (P4-4)."""
	user = user or frappe.session.user
	return DECIDER_ROLE in frappe.get_roles(user) and not is_requester(doc, user)


# ---------------------------------------------------------------- permissions (both hooks, §3.4)


def has_permission(doc, ptype=None, user=None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	roles = set(frappe.get_roles(user))
	if user == "Administrator" or roles & {"HR Manager", "System Manager"}:
		return True
	if "HR User" in roles and ptype in (None, "read", "select", "print", "email", "report", "export"):
		return True
	if ptype == "create" and not doc.get("employee"):
		return True  # a new, empty request: the role decides
	me = own_employee(user)
	if me and doc.get("employee") == me:
		return ptype != "delete" or doc.get("status") in (None, "", DRAFT)
	return False


def query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if is_backoffice(user):
		return ""
	me = own_employee(user)
	if not me:
		return "1=0"
	return f"`tab{DOCTYPE}`.employee = {frappe.db.escape(me)}"


# ---------------------------------------------------------------- controller


def validate(doc) -> None:
	"""Only a draft is edited by hand; the person asking for themselves; one kind of detail at a time."""
	if _in_transition(doc):
		return
	before = doc.get_doc_before_save()
	previous = before.status if before else DRAFT
	if previous != DRAFT:
		frappe.throw(_("This request has been sent. HR decides it; it cannot be changed."), title=_("Already Sent"))
	if (doc.status or DRAFT) != DRAFT:
		frappe.throw(_("A request's status changes only by sending or deciding it."), frappe.PermissionError)
	doc.status = DRAFT
	if not is_backoffice() and doc.employee != own_employee():
		frappe.throw(_("You can only ask to change your own payout details."), frappe.PermissionError)
	if doc.change == BANK:
		for field in MOBILE_FIELDS:
			doc.set(field, None)
		doc.bank_account_no = re.sub(r"\s+", "", doc.bank_account_no or "") or None
	elif doc.change == MOBILE:
		for field in BANK_FIELDS:
			doc.set(field, None)
		if doc.mobile_no:
			number = _normalise_mobile(doc.mobile_no)
			doc.mobile_no = number
			doc.provider = _provider(number)


def onload(doc) -> None:
	"""What the form may offer the person looking."""
	user = frappe.session.user
	doc.set_onload("can_send", doc.status == DRAFT and (is_requester(doc, user) or is_backoffice(user)))
	doc.set_onload("can_decide", doc.status == WAITING and can_decide(doc, user))
	doc.set_onload("can_withdraw", doc.status == WAITING and is_requester(doc, user))


def on_trash(doc) -> None:
	if doc.status not in (DRAFT, None, "") and "System Manager" not in frappe.get_roles():
		frappe.throw(_("A sent request is kept as a record. Withdraw it instead."))


# ---------------------------------------------------------------- numbers and names


def _normalise_mobile(number: str) -> str:
	try:
		from seal_common.seal_common.mno import is_valid_kenya_mobile_no, normalize_kenya_mobile_no
	except ImportError:
		digits = re.sub(r"\D", "", number or "")
		if re.fullmatch(r"0[17]\d{8}", digits):
			digits = "254" + digits[1:]
		if not re.fullmatch(r"254[17]\d{8}", digits):
			frappe.throw(_("{0} is not a Kenyan mobile number.").format(number))
		return digits
	normalised = normalize_kenya_mobile_no(number)
	if not (normalised and is_valid_kenya_mobile_no(normalised)):
		frappe.throw(_("{0} is not a Kenyan mobile number.").format(number))
	return normalised


def _provider(number: str) -> str | None:
	try:
		from seal_common.seal_common.mno import get_mno_from_no
	except ImportError:
		return None
	operator = get_mno_from_no(number)
	return None if not operator or operator == "UNKNOWN" else operator


def _words(name: str | None) -> set[str]:
	return {w for w in re.split(r"[^a-z]+", (name or "").lower()) if len(w) > 1}


def names_match(account_name: str | None, employee_name: str | None) -> bool:
	"""The account is in the employee's name: at least two of their name's words, or the one (P4-6)."""
	theirs, account = _words(employee_name), _words(account_name)
	if not theirs or not account:
		return False
	return len(theirs & account) >= min(2, len(theirs))


# ---------------------------------------------------------------- what is there now


def current_details(employee: str) -> frappe._dict:
	"""Where the employee is paid now: the default Bank Account and the mobile number payroll reads."""
	from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

	emp = frappe.db.get_value("Employee", employee, ["custom_salary_bank_account", "custom_contact", "cell_number"], as_dict=True) or {}
	account = emp.get("custom_salary_bank_account") or get_party_bank_account("Employee", employee)
	bank = frappe.db.get_value("Bank Account", account, ["name", "bank", "bank_account_no", "account_name"], as_dict=True) if account else None
	mobile = None
	if emp.get("custom_contact"):
		mobile = frappe.db.get_value("Contact", emp.custom_contact, "mobile_no")
	return frappe._dict(
		bank_account=bank.name if bank else None,
		bank=bank.bank if bank else None,
		bank_account_no=bank.bank_account_no if bank else None,
		account_name=bank.account_name if bank else None,
		mobile_no=mobile or emp.get("cell_number"),
	)


# ---------------------------------------------------------------- sending


def _load(name: str):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	return doc


@frappe.whitelist(methods=["POST"])
def send(name: str) -> str:
	"""The person (or HR for them) sends a request to HR, after a fresh check of who is asking."""
	doc = _load(name)
	if not (is_requester(doc) or is_backoffice()):
		frappe.throw(_("Only the person it is about, or HR, can send this request."), frappe.PermissionError)
	if doc.status != DRAFT:
		frappe.throw(_("This request has already been sent."))
	step_up.require_fresh_check()
	if frappe.db.exists(DOCTYPE, {"employee": doc.employee, "status": WAITING, "name": ["!=", doc.name]}):
		frappe.throw(_("{0} already has a request waiting for HR. Wait for it, or withdraw it.").format(doc.employee_name))
	_check_complete(doc)
	now = current_details(doc.employee)
	doc.update({
		"previous_bank_account": now.bank_account,
		"previous_bank": now.bank,
		"previous_bank_account_no": now.bank_account_no,
		"previous_account_name": now.account_name,
		"previous_mobile_no": now.mobile_no,
		"status": WAITING,
		"sent_on": now_datetime(),
	})
	with transition(doc.name):
		doc.save()
	_tell_on_send(doc)
	return doc.status


def _check_complete(doc) -> None:
	if doc.change == BANK:
		missing = [doc.meta.get_label(f) for f in ("bank", "bank_account_no", "account_name", "evidence") if not doc.get(f)]
		if missing:
			frappe.throw(_("Fill in {0} before sending.").format(", ".join(_(m) for m in missing)), title=_("Missing Details"))
		if not names_match(doc.account_name, doc.employee_name):
			frappe.throw(
				_("The account name {0} does not match {1}. Pay can only go to an account in the employee's own name.").format(
					frappe.bold(doc.account_name), frappe.bold(doc.employee_name)
				),
				title=_("Account Name"),
			)
	elif doc.change == MOBILE:
		if not doc.mobile_no:
			frappe.throw(_("Fill in the mobile number before sending."), title=_("Missing Details"))
		_normalise_mobile(doc.mobile_no)
	else:
		frappe.throw(_("Choose what is changing: a bank account or a mobile money number."))


def _hr_managers(company: str | None, exclude: set[str]) -> list[str]:
	"""Who is told of a new request: enabled desk users holding HR Manager who may see the
	employee's company (Keith, 2026-11-11, replacing P4-10's "every HR Manager on the site").

	Company access is by User Permission alone (bench rule): an HR Manager with Company
	User Permissions is told only about those companies. One with none is not restricted
	by Frappe and can open every company's requests, so is told of all of them (P4-14).
	"""
	users = frappe.get_all("Has Role", filters={"role": DECIDER_ROLE, "parenttype": "User"}, pluck="parent")
	enabled = frappe.get_all("User", filters={"name": ["in", users or [""]], "enabled": 1, "user_type": "System User"}, pluck="name")
	return [u for u in enabled if u not in exclude and u != "Administrator" and _sees_company(u, company)]


def _sees_company(user: str, company: str | None) -> bool:
	"""Whether `user` may see `company` by their Company User Permissions (none = every company)."""
	allowed = {p.get("doc") for p in frappe.permissions.get_user_permissions(user).get("Company", [])}
	return not allowed or not company or company in allowed


def _old_addresses(employee: str) -> list[str]:
	values = frappe.db.get_value("Employee", employee, ["user_id", "prefered_email", "personal_email", "company_email"], as_dict=True) or {}
	out = []
	for address in (values.get("prefered_email"), frappe.db.get_value("User", values.get("user_id"), "email") if values.get("user_id") else None):
		if address and address not in out:
			out.append(address)
	return out


def _mail(recipients: list[str], subject: str, message: str, doc) -> None:
	if not recipients:
		return
	try:
		frappe.sendmail(recipients=recipients, subject=subject, message=message, reference_doctype=DOCTYPE, reference_name=doc.name)
	except Exception:
		frappe.log_error(title="Payout change: email not sent", reference_doctype=DOCTYPE, reference_name=doc.name)


def _tell_on_send(doc) -> None:
	"""The old number and the old address hear of it; HR is asked to check it."""
	if doc.previous_mobile_no:
		frappe.enqueue(
			"seal_hrms.seal_hrms.payout_change.send_text_notice",
			queue="short",
			enqueue_after_commit=True,
			number=doc.previous_mobile_no,
			request_name=doc.name,
		)
	_mail(_old_addresses(doc.employee), _("A change to where your pay goes was requested"), f"<p>{_(NOTICE)}</p>", doc)
	link = get_url_to_form(DOCTYPE, doc.name)
	subject = _("Payout change to confirm for {0}").format(doc.employee_name)
	company = frappe.db.get_value("Employee", doc.employee, "company") or doc.get("company")
	managers = _hr_managers(company, {frappe.session.user, user_for_employee(doc.employee) or ""})
	_mail(
		managers,
		subject,
		_("<p>{0} asked to change where their pay goes ({1}). Check the evidence and confirm or reject it: <a href=\"{2}\">{3}</a>.</p>").format(
			frappe.utils.escape_html(doc.employee_name), _(doc.change), link, doc.name
		),
		doc,
	)
	for user in managers:
		notify.log(user, subject, DOCTYPE, doc.name)


def send_text_notice(number: str, request_name: str) -> None:
	"""Background job: the text to the old number. Never names the new details."""
	text = _(NOTICE)
	try:
		if "seal_common" in frappe.get_installed_apps():
			from seal_common.messaging.channels import send_on_channel

			send_on_channel("SMS", [number], text, reference_doctype=DOCTYPE, reference_name=request_name, kind="Service")
		else:
			from frappe.core.doctype.sms_settings.sms_settings import send_sms

			send_sms([number], text)
	except Exception:
		frappe.log_error(title="Payout change: text to the old number not sent", reference_doctype=DOCTYPE, reference_name=request_name)


# ---------------------------------------------------------------- deciding


def _waiting_for(doc) -> None:
	if not can_decide(doc):
		if is_requester(doc):
			frappe.throw(_("This request is about you. Another HR Manager must decide it."), frappe.PermissionError)
		frappe.throw(_("Only an HR Manager can decide a payout change."), frappe.PermissionError)
	if doc.status != WAITING:
		frappe.throw(_("This request is not waiting for HR."))


@frappe.whitelist(methods=["POST"])
def approve(name: str, effective_from: str | None = None) -> str:
	"""An HR Manager confirms the request. From `effective_from` (today if blank) payments use the new details."""
	doc = _load(name)
	_waiting_for(doc)
	step_up.require_fresh_check()
	day = getdate(effective_from or today())
	if day < getdate(today()):
		frappe.throw(_("Effective From cannot be in the past: payments already made used the old details."))
	doc.update({"status": APPROVED, "effective_from": day, "decided_by": frappe.session.user, "decided_on": now_datetime()})
	with transition(doc.name):
		doc.save()
		if day <= getdate(today()):
			apply(doc)
	_tell_requester(doc, _("Your payout change was approved"), _("<p>From {0} your pay goes to the new details.</p>").format(frappe.utils.formatdate(day)))
	return doc.status


@frappe.whitelist(methods=["POST"])
def reject(name: str, reason: str | None = None) -> str:
	"""An HR Manager turns the request down, saying why. Nothing on the employee record changes."""
	doc = _load(name)
	_waiting_for(doc)
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("Say why, so the employee knows what to do next."))
	doc.update({"status": REJECTED, "decision_note": reason, "decided_by": frappe.session.user, "decided_on": now_datetime()})
	with transition(doc.name):
		doc.save()
	_tell_requester(doc, _("Your payout change was not approved"), "<p>{0}</p>".format(frappe.utils.escape_html(reason)))
	return doc.status


@frappe.whitelist(methods=["POST"])
def withdraw(name: str) -> str:
	"""The person takes back a request HR has not decided yet."""
	doc = _load(name)
	if not is_requester(doc):
		frappe.throw(_("Only the person who asked can withdraw this request."), frappe.PermissionError)
	if doc.status != WAITING:
		frappe.throw(_("Only a request waiting for HR can be withdrawn."))
	doc.status = WITHDRAWN
	with transition(doc.name):
		doc.save()
	return doc.status


def _tell_requester(doc, subject: str, body: str) -> None:
	user = user_for_employee(doc.employee)
	if not user:
		return
	_mail([user], subject, body, doc)
	notify.log(user, subject, DOCTYPE, doc.name)


# ---------------------------------------------------------------- applying


def apply(doc) -> None:
	"""Put an approved request's details where payroll reads them. Called under `transition`.

	Bank: a new Bank Account for this employee becomes the default and the Employee's
	salary account; the old one is kept, only no longer the default. Mobile: the
	employee's own Contact gets the number as its primary mobile, and `cell_number`
	follows. The Employee is saved through the ORM, so its guards run.

	HR's approval IS the governed change (P4-7, Keith 2026-11-11): where seal_governance
	guards Employee, Bank Account or Contact, these writes run under its `mdc_bypass()`
	(SEAL_DEV_RULES §3.11b), and a comment on the Employee names the request and who
	approved it. A direct edit of the same details still needs a governance request.
	"""
	if doc.applied_on:
		return
	with _governed_change():
		employee = frappe.get_doc("Employee", doc.employee)
		if doc.change == BANK:
			account = _new_bank_account(doc, employee)
			employee.custom_salary_bank_account = account
			employee.save(ignore_permissions=True)  # the caller checked: an HR Manager, not the requester
			doc.new_bank_account = account
		else:
			_set_mobile(doc, employee)
	doc.applied_on = now_datetime()
	doc.db_set({"applied_on": doc.applied_on, "new_bank_account": doc.new_bank_account}, update_modified=False)
	doc.add_comment("Info", _("The new payout details are on {0}'s employee record.").format(doc.employee_name))
	employee.add_comment("Info", _audit_note(doc))


def _audit_note(doc) -> str:
	"""What the Employee's timeline says: which request changed where pay goes, and who approved it."""
	approver = frappe.utils.get_fullname(doc.decided_by) if doc.decided_by else _("an HR Manager")
	what = _("bank account") if doc.change == BANK else _("mobile money number")
	return _("Payout {0} changed by Payout Change Request {1}, approved by {2} ({3}).").format(
		what, get_link_to_form(DOCTYPE, doc.name), frappe.utils.escape_html(approver), doc.decided_by or ""
	)


@contextmanager
def _governed_change():
	"""Run the apply under seal_governance's `mdc_bypass()` where that app is installed.

	seal_governance is optional for seal_hrms: imported here, never at module level, and
	a site without it (or an older one without the context manager) runs the block as is.
	"""
	bypass = None
	if "seal_governance" in frappe.get_installed_apps():
		try:
			from seal_governance.data_governance.change_request_utils import mdc_bypass as bypass
		except ImportError:
			bypass = None
	if bypass is None:
		yield
		return
	with bypass():
		yield


def _new_bank_account(doc, employee) -> str:
	account = _create_or_reuse_account(doc, employee)
	# Bank Account.validate clears the old default only within the same company, and older
	# accounts often have none: clear every other default of this employee's, keeping the rows.
	for other in frappe.get_all(
		"Bank Account", filters={"party_type": "Employee", "party": employee.name, "is_default": 1, "name": ["!=", account]}, pluck="name"
	):
		frappe.db.set_value("Bank Account", other, "is_default", 0)
	return account


def _create_or_reuse_account(doc, employee) -> str:
	existing = frappe.db.get_value(
		"Bank Account", {"party_type": "Employee", "party": employee.name, "bank_account_no": doc.bank_account_no, "bank": doc.bank}, "name"
	)
	if existing:
		account = frappe.get_doc("Bank Account", existing)
		account.update({"is_default": 1, "disabled": 0})
		account.save(ignore_permissions=True)  # its own validate clears the old default
		return account.name
	account = frappe.new_doc("Bank Account")
	account.update({
		"account_name": doc.account_name,
		"bank": doc.bank,
		"bank_account_no": doc.bank_account_no,
		"branch_code": doc.branch_code,
		"party_type": "Employee",
		"party": employee.name,
		"company": employee.company,
		"is_default": 1,  # Bank Account.validate clears the employee's previous default
	})
	name = f"{doc.account_name} - {doc.bank}"
	# The account is named after its holder and bank, so a second account at the same bank clashes.
	set_name = f"{name} - {doc.bank_account_no[-4:]}" if frappe.db.exists("Bank Account", name) else None
	account.insert(ignore_permissions=True, set_name=set_name)
	return account.name


def _set_mobile(doc, employee) -> None:
	from seal_hrms.seal_hrms.api import _assert_contact_belongs_to_employee, _set_primary_mobile

	if not employee.get("custom_contact"):
		frappe.throw(
			_("{0} has no contact on their employee record. Link the contact of their own user first, then approve.").format(employee.employee_name),
			title=_("No Contact"),
		)
	_assert_contact_belongs_to_employee(employee.custom_contact, employee.name)
	contact = frappe.get_doc("Contact", employee.custom_contact)
	_set_primary_mobile(contact, doc.mobile_no)
	contact.save(ignore_permissions=True)
	employee.reload()
	employee.cell_number = doc.mobile_no
	employee.save(ignore_permissions=True)


def apply_due(names: list[str] | None = None) -> list[str]:
	"""Daily: apply approved requests whose Effective From has come (P4-5). `names` limits the pass."""
	if not frappe.db.table_exists(DOCTYPE):
		return []
	filters = [["status", "=", APPROVED], ["applied_on", "is", "not set"], ["effective_from", "is", "set"], ["effective_from", "<=", today()]]
	if names is not None:
		filters.append(["name", "in", names or [""]])
	done = []
	for name in frappe.get_all(DOCTYPE, filters=filters, pluck="name"):
		doc = frappe.get_doc(DOCTYPE, name)
		try:
			with transition(name):
				apply(doc)
			done.append(name)
		except Exception:
			frappe.log_error(title="Payout change: not applied on its date", reference_doctype=DOCTYPE, reference_name=name)
	return done


# ---------------------------------------------------------------- for My Desk and App Health


def waiting_figure(user: str):
	"""HR's figure: requests waiting for a decision. None for someone who cannot decide them."""
	if not frappe.db.table_exists(DOCTYPE) or DECIDER_ROLE not in frappe.get_roles(user):
		return None
	count = len(frappe.get_list(DOCTYPE, filters={"status": WAITING}, pluck="name", limit=1000))
	return frappe._dict(
		key="payout_changes_to_confirm",
		caption=_("Payout changes to confirm"),
		value=count,
		target=frappe._dict(kind="List", name=DOCTYPE, filters={"status": WAITING}),
	)


def working_days_ago(n: int, on_date=None):
	"""The date `n` working days (Monday to Friday) before `on_date` (P4-11)."""
	day = getdate(on_date or today())
	while n > 0:
		day = add_days(day, -1)
		if day.weekday() < 5:
			n -= 1
	return day
