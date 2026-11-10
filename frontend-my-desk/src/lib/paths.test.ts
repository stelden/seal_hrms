// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { nameFrom, P, RECORDS } from "./paths";
import { ROUTES } from "../section";

// vitest runs from the frontend folder; the hooks sit in the app package beside it.
const HOOKS = readFileSync(resolve(process.cwd(), "../seal_hrms/hooks.py"), "utf8");

/** The DocTypes the hook's `claims` lists (seal_hrms/hooks.py, seal_desk_app_sections). */
function claimed(): string[] {
	const block = HOOKS.slice(HOOKS.indexOf("seal_desk_app_sections"));
	const claims = block.slice(block.indexOf('"claims": ['), block.indexOf("],", block.indexOf('"claims": [')));
	return [...claims.matchAll(/"([^"]+)",/g)].map((m) => m[1]).filter((name) => name !== "claims");
}

/** Whether a section path is answered by one of its routes (":x" matches one segment). */
function routed(path: string): boolean {
	const clean = path.split("?")[0];
	return ROUTES.some((route) => {
		const want = route.path.split("/");
		const have = clean.split("/");
		return want.length === have.length && want.every((part, i) => part.startsWith(":") || part === have[i]);
	});
}

describe("records map", () => {
	it("claims exactly the DocTypes the hook declares", () => {
		expect(Object.keys(RECORDS).sort()).toEqual(claimed().sort());
	});

	it("opens every list, record and new form on a route of the section", () => {
		for (const [doctype, how] of Object.entries(RECORDS)) {
			for (const path of [how.list, how.create, how.record?.("HR-LAP-2026-00042")].filter(Boolean) as string[]) {
				expect(routed(path), `${doctype} → ${path}`).toBe(true);
			}
		}
	});

	it("keeps a name with slashes in one segment, and reads it back", () => {
		const path = RECORDS["Salary Slip"].record!("Sal Slip/HR-EMP-00012/00003");
		expect(path).toBe("pay/Sal%20Slip%2FHR-EMP-00012%2F00003");
		expect(routed(path)).toBe(true);
		expect(nameFrom(path.split("/")[1])).toBe("Sal Slip/HR-EMP-00012/00003");
		expect(nameFrom("HR-EXP-2026-00007")).toBe("HR-EXP-2026-00007");
		expect(nameFrom("100%")).toBe("100%");
	});
});

describe("routes", () => {
	it("are unique and relative", () => {
		const paths = ROUTES.map((r) => r.path);
		expect(new Set(paths).size).toBe(paths.length);
		expect(paths.every((p) => !p.startsWith("/"))).toBe(true);
	});

	it("give each area its list, and the forms the home screen opens", () => {
		for (const path of [P.leave, P.leaveNew, P.cover, P.toil, P.toilNew, P.timesheet, P.week("2026-11-09"), P.expenses, P.expenseNew, P.advances, P.pay, P.checkIn, P.attendance, P.shifts, P.me, P.payoutNew]) {
			expect(routed(path), path).toBe(true);
		}
	});
});
