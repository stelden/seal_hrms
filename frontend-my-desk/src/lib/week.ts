// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * A timesheet week on a phone: one day at a time. The server keeps the week as lines down the side
 * with seven days of hours across (`custom_week_entries`, timesheets/week.py); this file only edits
 * that shape. Dates are plain YYYY-MM-DD strings, worked out without time zones (DESIGN §6: a phone's
 * "today" in UTC is the wrong day in Nairobi after 21:00).
 */

export interface WeekEntry {
	row: number;
	activity_type: string | null;
	project?: string | null;
	task?: string | null;
	description?: string | null;
	is_billable?: 0 | 1;
	hours: number[];
}

const DAY_MS = 86_400_000;

function toUtc(day: string): number {
	const [y, m, d] = day.split("-").map(Number);
	return Date.UTC(y, m - 1, d);
}

function fromUtc(ms: number): string {
	return new Date(ms).toISOString().slice(0, 10);
}

export function addDays(day: string, n: number): string {
	return fromUtc(toUtc(day) + n * DAY_MS);
}

/** The Monday of the week `day` falls in. */
export function mondayOf(day: string): string {
	const weekday = (new Date(toUtc(day)).getUTCDay() + 6) % 7; // Monday 0 … Sunday 6
	return addDays(day, -weekday);
}

/** Today where the person is (their phone's local date, not UTC's). */
export function localToday(now: Date = new Date()): string {
	const pad = (n: number) => String(n).padStart(2, "0");
	return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function weekDays(monday: string): string[] {
	return Array.from({ length: 7 }, (_, i) => addDays(monday, i));
}

/** Hours as entered: a number, never NaN or negative. */
export function hoursOf(value: unknown): number {
	const n = typeof value === "number" ? value : Number.parseFloat(String(value ?? ""));
	return Number.isFinite(n) && n > 0 ? Math.round(n * 100) / 100 : 0;
}

export function dayTotal(entries: WeekEntry[], dayIndex: number): number {
	return Math.round(entries.reduce((sum, e) => sum + hoursOf(e.hours[dayIndex]), 0) * 100) / 100;
}

export function weekTotal(entries: WeekEntry[]): number {
	return Math.round(weekDays("2000-01-03").reduce((sum, _d, i) => sum + dayTotal(entries, i), 0) * 100) / 100;
}

export function newEntry(entries: WeekEntry[], activityType: string | null): WeekEntry {
	const row = entries.reduce((max, e) => Math.max(max, e.row), 0) + 1;
	return { row, activity_type: activityType, description: "", is_billable: 0, hours: [0, 0, 0, 0, 0, 0, 0] };
}

/** The same piece of work again, with this week's hours to fill: last week's lines without their hours. */
export function copyLastWeek(previous: WeekEntry[]): WeekEntry[] {
	return previous.map((e, i) => ({
		row: i + 1,
		activity_type: e.activity_type,
		project: e.project ?? null,
		task: e.task ?? null,
		description: e.description ?? "",
		is_billable: e.is_billable ? 1 : 0,
		hours: [0, 0, 0, 0, 0, 0, 0],
	}));
}

export function setHours(entries: WeekEntry[], row: number, dayIndex: number, hours: unknown): WeekEntry[] {
	return entries.map((e) => (e.row === row ? { ...e, hours: e.hours.map((h, i) => (i === dayIndex ? hoursOf(hours) : hoursOf(h))) } : e));
}

/** What the server keeps: lines with any hours or words; empty lines dropped, rows numbered again. */
export function forSaving(entries: WeekEntry[]): WeekEntry[] {
	return entries
		.filter((e) => e.hours.some((h) => hoursOf(h) > 0) || (e.description ?? "").trim())
		.map((e, i) => ({ ...e, row: i + 1, hours: Array.from({ length: 7 }, (_, d) => hoursOf(e.hours[d])) }));
}
