# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Extra hours a member of staff worked, sent to their leave approver to become time off.

The claim moves by Frappe Workflow (`toil.workflow`): its states, actions and the
roles for each are the site's to change. This controller keeps only what a
workflow cannot say (WORKING_TIME_DESIGN.md §9i):

  * who: the person (or HR) sends; the claim's named approver, their stand-in
    or HR decides, never the claimant (`_check_move`, `before_submit`);
  * the reason on Return and Reject, saved first by `toil.workflow.set_decision_note`;
  * the lock while it waits (a workflow's "who may edit" is enforced only in the browser);
  * the stamps, and the side effects: time added on submit, taken back on cancel
    (`toil.ledger`, `toil.lapse`), shares and emails (`toil.notifications`).

The claim's rules are in `toil.rules`, who may see it in `toil.access`.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

from seal_hrms.seal_hrms import acting
from seal_hrms.seal_hrms.handover import user_for_employee
from seal_hrms.seal_hrms.toil import access, lapse, ledger, notifications, rules, stage
from seal_hrms.seal_hrms.toil import workflow as wf
from seal_hrms.seal_hrms.working_time.policy import policy_for

EDITABLE = (wf.DRAFT, wf.RETURNED)
#: What the person writes; none of it may change while the claim waits for a decision.
CONTENT = ("employee", "note")
LINE_CONTENT = ("work_date", "hours", "planned_hours", "work_done")


def _previous(doc) -> str:
	before = doc.get_doc_before_save()
	return (before.status if before else None) or wf.DRAFT


class TimeOffinLieuClaim(Document):
	def onload(self):
		"""Tell the form where the claim is and what this viewer may do; the workflow and validate check again."""
		user = frappe.session.user
		self.set_onload("can_decide", not self.is_new() and access.can_decide(self, user))
		self.set_onload("can_send", not self.is_new() and access.can_send(self, user))
		self.set_onload("where_it_is", stage.where_it_is(self, user))
		self.set_onload("is_mine", user_for_employee(self.employee) == user)

	def before_insert(self):
		# The way extra work is agreed is the company's when the claim is made; a later
		# change of policy does not move claims already in flight.
		if not self.mode and self.company:
			self.mode = policy_for(self.company).prior_authorisation

	def validate(self):
		previous = _previous(self)
		if self.is_new() or self.has_value_changed("employee"):
			access.require_self_or_hr(self.employee)
		if previous in wf.WAITING_STATES:
			self._check_unchanged()
		if (self.status or wf.DRAFT) != previous:
			self._check_move(previous)
		if self.status in EDITABLE:
			self.approver = get_employee_leave_approver(self.employee) or None
		rules.check(self)

	def _check_move(self, previous: str) -> None:
		"""Who may make this move, what it needs, and what it stamps. The workflow has said the move exists."""
		status = self.status
		if status in wf.WAITING_STATES:
			access.require_self_or_hr(self.employee)
			self.approver = get_employee_leave_approver(self.employee) or None
			if not self.approver:
				frappe.throw(
					_(
						"Nobody approves leave for {0}, so nobody can decide this claim. Ask HR to set a leave approver."
					).format(self.employee_name),
					title=_("No Approver"),
				)
			if status == wf.WAITING:
				rules.check_claim_window(self, policy_for(self.company))
			self.sent_on = now_datetime()
			self.decision_note = None
			return
		if status == wf.CANCELLED:
			return  # the workflow's roles decide; before_cancel takes the time back
		access.require_decider(self)
		if self._is_return(previous) or status == wf.REJECTED:
			if not (self.decision_note or "").strip():
				frappe.throw(
					_("Say why: the person reads this to know what to change or why it was refused."),
					title=_("Reason Needed"),
				)
		if status == wf.AUTHORISED and previous == wf.WAITING_AUTH:
			self.authorised_by = frappe.session.user
			self.authorised_on = now_datetime()
			for line in self.lines:
				line.authorised = 1
		else:
			self.approved_by = frappe.session.user
			if status in (wf.APPROVED, wf.REJECTED):
				self.approved_on = now_datetime()

	def _is_return(self, previous: str) -> bool:
		# In "authorise first" a claim returned at approval goes back to Authorised.
		return self.status == wf.RETURNED or (self.status == wf.AUTHORISED and previous == wf.WAITING)

	def _check_unchanged(self) -> None:
		"""While a claim waits for a decision nothing the person wrote may change, whoever saves it."""
		before = self.get_doc_before_save()
		mine = [tuple(line.get(f) for f in LINE_CONTENT) for line in self.lines]
		theirs = [tuple(line.get(f) for f in LINE_CONTENT) for line in before.lines]
		if mine != theirs or any(self.get(f) != before.get(f) for f in CONTENT):
			frappe.throw(
				_("This claim is with {0}. Ask them to return it before changing it.").format(
					self.approver_name or self.approver
				),
				title=_(before.status),
			)

	def before_submit(self):
		if self.status not in (wf.APPROVED, wf.REJECTED):
			frappe.throw(_("Approve or reject the claim from its Actions menu."), frappe.PermissionError)
		access.require_decider(self)
		acting.refuse_self_approval(self, self.employee, self.approver, access.AUTHORITY)
		if self.status == wf.APPROVED:
			ledger.prepare(self)

	def on_submit(self):
		if self.status == wf.APPROVED:
			ledger.credit(self)
			lapse.reconcile(self.leave_allocation)
		acting.record_acting_approval(self, self.approver, access.AUTHORITY)

	def on_update(self):
		"""After each move: share with whoever decides next, and tell the person who acts next."""
		previous = _previous(self)
		if previous == self.status:
			return
		if self.status in wf.WAITING_STATES:
			self._share_with_approver()
			notifications.sent(self)
		elif self.status == wf.AUTHORISED and previous == wf.WAITING_AUTH:
			notifications.decided(self, "authorised")
		elif self._is_return(previous):
			notifications.decided(self, "returned")
		elif self.status == wf.APPROVED:
			notifications.decided(self, "approved")
		elif self.status == wf.REJECTED:
			notifications.decided(self, "rejected")

	def _share_with_approver(self) -> None:
		# The approver may hold no role on claims; the share is how they open it.
		if self.approver and not frappe.db.exists(
			"DocShare", {"share_doctype": self.doctype, "share_name": self.name, "user": self.approver}
		):
			frappe.share.add_docshare(
				self.doctype,
				self.name,
				self.approver,
				read=1,
				write=1,
				submit=1,
				flags={"ignore_share_permission": True},
			)
		acting.share_new_document(self, self.approver, access.AUTHORITY)

	def before_cancel(self):
		# The ledger rows tagged with this claim stay, as the record of what happened.
		self.ignore_linked_doctypes = ("Leave Ledger Entry",)
		# By time added, not by status: the workflow sets "Cancelled" before it cancels.
		if self.days_credited and self.leave_allocation:
			lapse.check_can_cancel(self)
			# Written before the cancel lands: a row cannot link to a cancelled claim.
			ledger.reverse(self)

	def on_cancel(self):
		self.db_set("status", wf.CANCELLED, update_modified=False)
		if self.leave_allocation:
			# Its lapse rows go, and the claims that remain may now lapse differently.
			lapse.reconcile(self.leave_allocation)
