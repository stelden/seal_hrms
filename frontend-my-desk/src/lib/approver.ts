// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Who will decide a request, said the same way on every form before anything is sent (Keith, 2026-11-11:
 * "approved by Achieng" read as if it were already approved). Future tense, the person's name, and a way
 * forward when nobody is set. Whole sentences per case, never pieces (translations need the whole).
 */

import { __ } from "@stelden/seal-frontend/ui";

/** "Achieng Odhiambo will approve it.", or what to do when nobody approves this kind of request yet. */
export function willApprove(name: string | null | undefined): string {
	return name ? __("{0} will approve it.", [name]) : __("Nobody approves this yet. Ask HR to set your approver.");
}

/** The leave preview: how many days, and who will approve them. */
export function leavePreview(days: number | null, name: string | null | undefined): string {
	if (days === null) return willApprove(name);
	return name
		? __("{0} days. {1} will approve it.", [String(days), name])
		: __("{0} days. Nobody approves this yet. Ask HR to set your approver.", [String(days)]);
}
