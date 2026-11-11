// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { toneMap } from "@stelden/seal-frontend/ui";

/** One colour per state, across every record the section shows (StatusChip's tone). */
export const toneOf = toneMap(
	{
		Open: "info",
		Draft: "default",
		"Not Sent": "default",
		"Awaiting Acceptance": "warning",
		"Waiting for Authorisation": "warning",
		"Waiting for Approval": "warning",
		"Waiting for HR": "warning",
		"Pending Approval": "warning",
		Pending: "warning",
		Authorised: "info",
		Accepted: "success",
		Active: "primary",
		Approved: "success",
		Paid: "success",
		Claimed: "success",
		Submitted: "success",
		"Handed Back": "default",
		Returned: "warning",
		Unpaid: "warning",
		"Partly Claimed and Returned": "info",
		Rejected: "error",
		Declined: "error",
		Cancelled: "default",
		Withdrawn: "default",
	},
	"default",
);
