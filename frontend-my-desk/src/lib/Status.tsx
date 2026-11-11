// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { StatusChip, __ } from "@stelden/seal-frontend/ui";

import { toneOf } from "./status";

/** A state's words, translated: each is written out so the translation tools find it. */
export function statusLabel(status: string | null | undefined): string {
	switch (status) {
		case "Open": return __("Open");
		case "Draft": return __("Draft");
		case "Not Sent": return __("Not Sent");
		case "Awaiting Acceptance": return __("Awaiting Acceptance");
		case "Waiting for Authorisation": return __("Waiting for Authorisation");
		case "Waiting for Approval": return __("Waiting for Approval");
		case "Waiting for HR": return __("Waiting for HR");
		case "Pending Approval": return __("Pending Approval");
		case "Pending": return __("Answer Needed");
		case "Authorised": return __("Authorised");
		case "Accepted": return __("Accepted");
		case "Active": return __("Active");
		case "Approved": return __("Approved");
		case "Paid": return __("Paid");
		case "Unpaid": return __("Unpaid");
		case "Claimed": return __("Claimed");
		case "Submitted": return __("Submitted");
		case "Handed Over": return __("Handed Over");
		case "Handed Back": return __("Handed Back");
		case "Done while away": return __("Done While Away");
		case "Already done": return __("Already Done");
		case "Returned": return __("Returned");
		case "Rejected": return __("Rejected");
		case "Declined": return __("Declined");
		case "Cancelled": return __("Cancelled");
		case "Withdrawn": return __("Withdrawn");
		default: return status ?? "";
	}
}

/** A record's state as a chip, in the section's one colour per state. */
export function Status({ value }: { value: string | null | undefined }) {
	if (!value) return null;
	return <StatusChip status={value} label={statusLabel(value)} toneOf={toneOf} />;
}
