// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { describe, expect, it } from "vitest";

import { handoverStep, mergeFill, payoutMissing } from "./forms";

describe("leave handover step", () => {
	it("shows only when the company's rule covers the leave, and requires a stand-in only under a Require rule", () => {
		expect(handoverStep(undefined)).toEqual({ show: false, standInRequired: false });
		expect(handoverStep({ needed: false, required: false, rule: "Off" })).toEqual({ show: false, standInRequired: false });
		expect(handoverStep({ needed: true, required: false, rule: "Warn" })).toEqual({ show: true, standInRequired: false });
		expect(handoverStep({ needed: true, required: true, rule: "Require on Approval" })).toEqual({ show: true, standInRequired: true });
	});
});

describe("Fill from Records", () => {
	it("adds the days the records show, keeps what the person wrote, in date order", () => {
		const merged = mergeFill(
			[
				{ work_date: "2026-11-07", hours: 3, work_done: "Weekend stock count at the Ngong Road store" },
				{ work_date: "", hours: null, work_done: "" },
			],
			[
				{ work_date: "2026-11-07", hours: 5 },
				{ work_date: "2026-11-03", hours: 2.5 },
			],
		);
		expect(merged).toEqual([
			{ work_date: "2026-11-03", hours: 2.5, work_done: "" },
			{ work_date: "2026-11-07", hours: 3, work_done: "Weekend stock count at the Ngong Road store" },
		]);
	});
});

describe("payout change", () => {
	const letter = new File(["letter"], "otieno-bank-letter.pdf");
	it("needs bank, number, name and evidence for a bank account", () => {
		expect(payoutMissing({ change: "Bank Account" })).toEqual(["bank", "bank_account_no", "account_name", "evidence"]);
		expect(payoutMissing({ change: "Bank Account", bank: "Kilimani Cooperative Bank", bank_account_no: "01109384756311", account_name: "Otieno Ochieng", evidence: letter })).toEqual([]);
	});

	it("needs only the number for mobile money", () => {
		expect(payoutMissing({ change: "Mobile Money", mobile_no: " " })).toEqual(["mobile_no"]);
		expect(payoutMissing({ change: "Mobile Money", mobile_no: "254712345678" })).toEqual([]);
	});
});
