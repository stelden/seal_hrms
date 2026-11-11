// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { describe, expect, it } from "vitest";

import { leavePreview, willApprove } from "./approver";

describe("who will approve", () => {
	it("is said in the future tense, before anything is sent", () => {
		expect(willApprove("Achieng Odhiambo")).toBe("Achieng Odhiambo will approve it.");
		expect(leavePreview(7, "Achieng Odhiambo")).toBe("7 days. Achieng Odhiambo will approve it.");
		expect(leavePreview(null, "Achieng Odhiambo")).toBe("Achieng Odhiambo will approve it.");
	});

	it("says what to do when nobody approves yet", () => {
		expect(willApprove(null)).toBe("Nobody approves this yet. Ask HR to set your approver.");
		expect(leavePreview(2, undefined)).toBe("2 days. Nobody approves this yet. Ask HR to set your approver.");
	});
});
