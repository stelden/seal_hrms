// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/** Small rules the phone forms apply before the server checks again (the server stays the authority). */

export interface HandoverRule {
	needed: boolean;
	required: boolean;
	rule: string | null;
}

/** Whether the Apply for Leave screen shows its handover step, and whether a stand-in must be named. */
export function handoverStep(rule: HandoverRule | undefined): { show: boolean; standInRequired: boolean } {
	return { show: !!rule?.needed, standInRequired: !!rule?.needed && !!rule?.required };
}

export interface ToilLine {
	work_date: string;
	hours: number | null;
	work_done: string;
	planned_hours?: number | null;
}

/** "Fill from Records": days the records show, added to what is already there; a day already on the claim keeps what the person wrote. */
export function mergeFill(current: ToilLine[], found: Array<{ work_date: string; hours: number }>): ToilLine[] {
	const kept = current.filter((line) => line.work_date);
	const have = new Set(kept.map((line) => line.work_date));
	const added = found.filter((row) => !have.has(row.work_date)).map((row) => ({ work_date: row.work_date, hours: row.hours, work_done: "" }));
	return [...kept, ...added].sort((a, b) => a.work_date.localeCompare(b.work_date));
}

export type PayoutChange = "Bank Account" | "Mobile Money";

export interface PayoutDraft {
	change: PayoutChange;
	bank?: string;
	bank_account_no?: string;
	account_name?: string;
	mobile_no?: string;
	evidence?: File | null;
}

/** What is still missing before a payout change can be sent, by field (the server's own list, said earlier). */
export function payoutMissing(draft: PayoutDraft): string[] {
	if (draft.change === "Mobile Money") return draft.mobile_no?.trim() ? [] : ["mobile_no"];
	const missing: string[] = (["bank", "bank_account_no", "account_name"] as const).filter((f) => !draft[f]?.trim());
	return draft.evidence ? missing : [...missing, "evidence"];
}

/**
 * How many days of leave a compensatory leave request earns, as Frappe HR counts them on approval: every day
 * from the first to the last worked, less half a day for a half day. Null until both dates make sense.
 */
export function workDays(from: string, to: string, halfDay: boolean): number | null {
	if (!/^\d{4}-\d{2}-\d{2}$/.test(from) || !/^\d{4}-\d{2}-\d{2}$/.test(to || from)) return null;
	const start = Date.UTC(+from.slice(0, 4), +from.slice(5, 7) - 1, +from.slice(8, 10));
	const endText = to || from;
	const end = Date.UTC(+endText.slice(0, 4), +endText.slice(5, 7) - 1, +endText.slice(8, 10));
	if (end < start) return null;
	const days = Math.round((end - start) / 86_400_000) + 1;
	return halfDay ? days - 0.5 : days;
}

/** One journey of a travel request as the form holds it. */
export interface TravelLeg {
	travel_from: string;
	travel_to: string;
	mode_of_travel: string;
	departure_date: string;
	arrival_date: string;
	lodging_required: boolean;
}

/** One expected cost of a travel request as the form holds it. */
export interface TravelCost {
	expense_type: string;
	total_amount: number | null;
	comments: string;
}

/** The journeys and costs worth sending: a journey needs a place, a cost a kind or an amount. */
export function travelRows(itinerary: TravelLeg[], costings: TravelCost[]): { itinerary: TravelLeg[]; costings: TravelCost[] } {
	return {
		itinerary: itinerary.filter((l) => l.travel_from.trim() || l.travel_to.trim()),
		costings: costings.filter((c) => c.expense_type || (c.total_amount ?? 0) > 0),
	};
}
