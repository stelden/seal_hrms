# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Extra hours a member of staff worked, sent to their leave approver to become time off.

The rules are in `seal_hrms.seal_hrms.toil.rules`, the decisions in
`toil.approval`, who may do what in `toil.access`, and adding the time to the
leave balance in `toil.ledger`. Design: dev_notes/seal_hrms/WORKING_TIME_DESIGN.md.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

from seal_hrms.seal_hrms import acting
from seal_hrms.seal_hrms.toil import access, approval, lapse, ledger, rules

EDITABLE = (approval.DRAFT, approval.RETURNED)


class TimeOffinLieuClaim(Document):
	def onload(self):
		"""Tell the form which buttons this viewer may use; the endpoints check again."""
		user = frappe.session.user
		self.set_onload("can_decide", not self.is_new() and access.can_decide(self, user))
		self.set_onload("can_send", not self.is_new() and access.can_send(self, user))

	def validate(self):
		self._guard_status()
		self._guard_editing()
		self._check_who_claims()
		if self.status in EDITABLE:
			self.approver = get_employee_leave_approver(self.employee) or None
		rules.check(self)

	def _guard_status(self):
		if approval.in_transition(self):
			return
		before = self.get_doc_before_save()
		previous = before.status if before else approval.DRAFT
		if (self.status or approval.DRAFT) != previous:
			frappe.throw(
				_("A claim's status changes only by sending it or deciding it."), frappe.PermissionError
			)

	def _guard_editing(self):
		before = self.get_doc_before_save()
		if before and before.status == approval.WAITING and not approval.in_transition(self):
			frappe.throw(
				_("This claim is with {0}. Ask them to return it before changing it.").format(
					self.approver_name or self.approver
				),
				title=_("Waiting for Approval"),
			)

	def _check_who_claims(self):
		if self.is_new() or self.has_value_changed("employee"):
			access.require_self_or_hr(self.employee)

	def before_submit(self):
		if not approval.in_transition(self) or self.status not in (approval.APPROVED, approval.REJECTED):
			frappe.throw(_("Approve or reject the claim with its buttons."), frappe.PermissionError)
		access.require_decider(self)
		acting.refuse_self_approval(self, self.employee, self.approver, access.AUTHORITY)
		if self.status == approval.APPROVED:
			ledger.prepare(self)

	def on_submit(self):
		if self.status == approval.APPROVED:
			ledger.credit(self)
			lapse.reconcile(self.leave_allocation)
		acting.record_acting_approval(self, self.approver, access.AUTHORITY)

	def on_update(self):
		if self.status == approval.WAITING:
			acting.share_new_document(self, self.approver, access.AUTHORITY)

	def before_cancel(self):
		# The ledger rows tagged with this claim stay, as the record of what happened.
		self.ignore_linked_doctypes = ("Leave Ledger Entry",)
		if self.status == approval.APPROVED:
			lapse.check_can_cancel(self)
			# Written before the cancel lands: a row cannot link to a cancelled claim.
			ledger.reverse(self)

	def on_cancel(self):
		self.db_set("status", approval.CANCELLED, update_modified=False)
		if self.leave_allocation:
			# Its lapse rows go, and the claims that remain may now lapse differently.
			lapse.reconcile(self.leave_allocation)
