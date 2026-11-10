// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { afterEach, describe, expect, it } from "vitest";

import { DRAFT_MAX_AGE_DAYS, clearAllDrafts, clearDraft, draftKey, readDraft, savedDay, writeDraft } from "./drafts";

const OTIENO = "otieno.ochieng@kilimani-office.co.ke";
const ACHIENG = "achieng.wanjiru@kilimani-office.co.ke";

afterEach(() => window.localStorage.clear());

describe("drafts kept on the phone", () => {
	it("are keyed seal-draft:<user>:<form>:<id>, the key the shell clears on sign-out", () => {
		expect(draftKey(OTIENO, "timesheet-week", "2026-11-02")).toBe(`seal-draft:${OTIENO}:timesheet-week:2026-11-02`);
	});

	it("come back as written, then are gone once cleared", () => {
		const key = draftKey(OTIENO, "expense-claim", "new");
		expect(writeDraft(key, { remark: "Matatu fare to Kibera" }, 1_000)).toBe(true);
		expect(readDraft(key, 2_000)).toEqual({ value: { remark: "Matatu fare to Kibera" }, saved: 1_000 });
		clearDraft(key);
		expect(readDraft(key)).toBeNull();
	});

	it("are dropped when older than the age limit, or unreadable", () => {
		const key = draftKey(OTIENO, "leave-application", "new");
		writeDraft(key, { leave_type: "Annual Leave" }, 0);
		expect(readDraft(key, (DRAFT_MAX_AGE_DAYS + 1) * 86_400_000)).toBeNull();
		expect(window.localStorage.getItem(key)).toBeNull();
		window.localStorage.setItem(key, "{not json");
		expect(readDraft(key)).toBeNull();
		expect(window.localStorage.getItem(key)).toBeNull();
	});

	it("are all cleared at sign-out, one person's or everyone's, and nothing else", () => {
		writeDraft(draftKey(OTIENO, "timesheet-week", "2026-11-02"), []);
		writeDraft(draftKey(OTIENO, "expense-claim", "new"), {});
		writeDraft(draftKey(ACHIENG, "expense-claim", "new"), {});
		window.localStorage.setItem("seal-colour-mode", "dark");
		expect(clearAllDrafts(OTIENO)).toBe(2);
		expect(readDraft(draftKey(ACHIENG, "expense-claim", "new"))).not.toBeNull();
		expect(clearAllDrafts()).toBe(1);
		expect(window.localStorage.getItem("seal-colour-mode")).toBe("dark");
	});

	it("say the phone's own day they were saved on", () => {
		const late = new Date(2026, 10, 10, 23, 30).getTime();
		expect(savedDay(late)).toBe("2026-11-10");
	});
});
