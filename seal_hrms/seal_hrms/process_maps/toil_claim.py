# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Process map for a Time Off in Lieu Claim: from the extra hours to time off in the balance.

Registered in hooks.py (`seal_process_maps`); seal_common draws it
(dev_notes/seal_common/processmap/PROCESS_MAP.md). Two halves, so the rules are
tested without documents:

    facts_from_doc(doc) -> ClaimFacts   reads the claim and its company's policy
    build(facts)        -> definition   pure: steps, statuses, pills, arrows

Two shapes, as the company's policy says (stamped on the claim): claim
afterwards, or authorise first and confirm the hours. Numbers on pills come
from the policy, so the map cannot disagree with what the site enforces, and a
limit nobody set draws no pill.
"""

from dataclasses import dataclass
from itertools import pairwise

from frappe import _

DRAFT, RETURNED, WAITING = "Draft", "Returned", "Waiting for Approval"
WAITING_AUTH, AUTHORISED = "Waiting for Authorisation", "Authorised"
APPROVED, REJECTED = "Approved", "Rejected"


@dataclass
class ClaimFacts:
	authorise_first: bool
	status: str
	docstatus: int
	claim_within_days: int = 0
	validity_days: int = 0
	authorised: bool = False


def facts_from_doc(doc) -> ClaimFacts:
	from seal_hrms.seal_hrms.working_time.policy import AUTHORISE_FIRST, policy_for

	policy = policy_for(doc.company)
	return ClaimFacts(
		authorise_first=doc.get("mode") == AUTHORISE_FIRST,
		status=doc.status or DRAFT,
		docstatus=doc.docstatus,
		claim_within_days=int(policy.claim_within_days or 0),
		validity_days=int(policy.validity_days or 0),
		authorised=bool(doc.get("authorised_by")),
	)


def get_definition(doc) -> dict:
	"""Provider for the claim's process map (hook `seal_process_maps`)."""
	return build(facts_from_doc(doc))


def _main_path(facts: ClaimFacts) -> list[str]:
	return (
		["plan", "authorise", "confirm", "approve", "added"]
		if facts.authorise_first
		else ["claim", "approve", "added"]
	)


def _where(facts: ClaimFacts) -> str:
	"""The step the claim is at now."""
	status = facts.status
	if status in (DRAFT, RETURNED):
		return "plan" if facts.authorise_first else "claim"
	if status == WAITING_AUTH:
		return "authorise"
	if status == AUTHORISED:
		return "confirm"
	if status == WAITING:
		return "approve"
	if status == REJECTED:
		return "rejected"
	return "added"  # Approved, or Cancelled after approval


def build(facts: ClaimFacts) -> dict:
	path = _main_path(facts)
	where = _where(facts)
	cancelled = facts.docstatus == 2
	stopped_at = None
	if facts.status == REJECTED:
		stopped_at = "rejected"
	elif cancelled:
		stopped_at = "added" if facts.status in (APPROVED, "Cancelled") else where

	def status_of(step: str) -> str:
		if step == "rejected":
			return "interrupted" if facts.status == REJECTED else "skipped"
		if stopped_at == step:
			return "interrupted"
		if step == "added" and facts.status == APPROVED and not cancelled:
			return "end"
		reached = path.index(where) if where in path else len(path) - 1
		index = path.index(step)
		if facts.status == REJECTED:
			# Decided at the step it was waiting on: everything before is done, after is not taken.
			turned_down_at = "authorise" if facts.authorise_first and not facts.authorised else "approve"
			decided_at = path.index(turned_down_at)
			return "past" if index <= decided_at else "skipped"
		if index < reached:
			return "past"
		if index == reached:
			return "past" if stopped_at else "current"
		return "skipped" if stopped_at else "pending"

	approver = [{"label": _("Leave approver"), "kind": "approval"}]
	window = (
		[{"label": _("Send within {0} days").format(facts.claim_within_days), "kind": "deadline"}]
		if facts.claim_within_days
		else []
	)
	usable = (
		[{"label": _("Usable {0} days").format(facts.validity_days), "kind": "deadline"}]
		if facts.validity_days
		else []
	)
	titles = {
		"claim": (
			_("List the extra hours"),
			_("Days worked extra, and what the work was"),
			"rounded",
			window,
		),
		"plan": (_("Plan the extra work"), _("Days and hours, before the work"), "rounded", []),
		"authorise": (_("Authorise the work"), _("The approver agrees it first"), "square", approver),
		"confirm": (_("Confirm the hours"), _("The hours actually worked"), "rounded", window),
		"approve": (_("Approve the hours"), _("Or return with a reason"), "square", approver),
		"added": (_("Time off added"), _("Taken as ordinary leave"), "rounded", usable),
		"rejected": (_("Rejected"), _("Nothing is added"), "square", []),
	}
	steps = []
	for number, step in enumerate([*path, "rejected"], start=1):
		title, description, shape, pills = titles[step]
		steps.append(
			{
				"id": step,
				"number": str(number) if step != "rejected" else None,
				"title": title,
				"description": description,
				"status": status_of(step),
				"shape": shape,
				"pills": pills,
				"optional": step == "rejected",
			}
		)
	for step in steps:
		if step["number"] is None:
			del step["number"]

	links = [{"from": a, "to": b} for a, b in pairwise(path)]
	labels = {
		("claim", "approve"): _("Sent"),
		("plan", "authorise"): _("Sent"),
		("approve", "added"): _("Approved"),
	}
	labels[("authorise", "confirm")] = _("Authorised")
	labels[("confirm", "approve")] = _("Sent")
	for link in links:
		link["label"] = labels.get((link["from"], link["to"]))
	decision = "approve"
	first = path[0]
	links.append(
		{
			"from": decision,
			"to": first if not facts.authorise_first else "confirm",
			"label": _("Returned"),
			"optional": True,
		}
	)
	links.append({"from": decision, "to": "rejected", "label": _("Rejected"), "optional": True})
	if facts.authorise_first:
		links.append({"from": "authorise", "to": "plan", "label": _("Returned"), "optional": True})
		links.append({"from": "authorise", "to": "rejected", "label": _("Rejected"), "optional": True})
	for link in links:
		if not link.get("label"):
			link.pop("label", None)

	return {
		"direction": "LR",
		"shape": "rounded",
		"description": _(
			"How a time off claim moves. Square boxes are decisions by the person's leave approver; "
			"rounded boxes are what the person does. A return goes back one step to be corrected."
		),
		"steps": steps,
		"links": links,
	}
