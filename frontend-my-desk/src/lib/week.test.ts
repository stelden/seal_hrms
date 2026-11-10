// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { describe, expect, it } from "vitest";

import { addDays, copyLastWeek, dayTotal, forSaving, hoursOf, localToday, mondayOf, newEntry, setHours, weekDays, weekTotal, type WeekEntry } from "./week";

const entry = (row: number, hours: number[], activity = "Community Outreach", description = "Household visits in Mathare North"): WeekEntry => ({ row, activity_type: activity, description, hours });

describe("dates", () => {
	it("finds the Monday of any day, across months and years", () => {
		expect(mondayOf("2026-11-10")).toBe("2026-11-09");
		expect(mondayOf("2026-11-09")).toBe("2026-11-09");
		expect(mondayOf("2026-11-15")).toBe("2026-11-09");
		expect(mondayOf("2027-01-02")).toBe("2026-12-28");
	});

	it("adds days and lists a week", () => {
		expect(addDays("2026-02-27", 2)).toBe("2026-03-01");
		expect(weekDays("2026-11-09")).toEqual(["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15"]);
	});

	it("takes today from the phone's own clock, not UTC's", () => {
		// 23:30 in Nairobi on the 10th is 20:30 UTC: still the 10th either way; build the local date directly.
		expect(localToday(new Date(2026, 10, 10, 23, 30))).toBe("2026-11-10");
	});
});

describe("hours", () => {
	it("reads what people type", () => {
		expect(hoursOf("7.5")).toBe(7.5);
		expect(hoursOf("")).toBe(0);
		expect(hoursOf("-2")).toBe(0);
		expect(hoursOf("abc")).toBe(0);
		expect(hoursOf(1.3333)).toBe(1.33);
	});

	it("totals a day and a week", () => {
		const week = [entry(1, [4, 8, 0, 0, 0, 0, 0]), entry(2, [3.5, 0, 0, 0, 0, 2, 0])];
		expect(dayTotal(week, 0)).toBe(7.5);
		expect(dayTotal(week, 5)).toBe(2);
		expect(weekTotal(week)).toBe(17.5);
	});

	it("sets one day's hours on one line only", () => {
		const week = setHours([entry(1, [0, 0, 0, 0, 0, 0, 0]), entry(2, [1, 1, 1, 1, 1, 0, 0])], 1, 2, "6");
		expect(week[0].hours).toEqual([0, 0, 6, 0, 0, 0, 0]);
		expect(week[1].hours).toEqual([1, 1, 1, 1, 1, 0, 0]);
	});
});

describe("lines", () => {
	it("numbers a new line after the last", () => {
		expect(newEntry([entry(1, []), entry(4, [])], "Training").row).toBe(5);
		expect(newEntry([], null)).toMatchObject({ row: 1, activity_type: null, hours: [0, 0, 0, 0, 0, 0, 0] });
	});

	it("copies last week's work without its hours", () => {
		const copied = copyLastWeek([entry(3, [8, 8, 8, 8, 8, 0, 0]), entry(7, [0, 0, 0, 0, 0, 4, 0], "Training", "First aid course")]);
		expect(copied.map((e) => [e.row, e.activity_type, e.description, e.hours.reduce((a, b) => a + b, 0)])).toEqual([
			[1, "Community Outreach", "Household visits in Mathare North", 0],
			[2, "Training", "First aid course", 0],
		]);
	});

	it("saves only lines with hours or words, numbered again", () => {
		const saved = forSaving([entry(2, [0, 0, 0, 0, 0, 0, 0], "Training", ""), entry(5, [2, 0, 0, 0, 0, 0, 0]), entry(9, [], "Training", "Planning the Kibera drive")]);
		expect(saved.map((e) => e.row)).toEqual([1, 2]);
		expect(saved[1].hours).toEqual([0, 0, 0, 0, 0, 0, 0]);
	});
});
