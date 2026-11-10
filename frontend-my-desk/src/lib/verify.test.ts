// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { describe, expect, it, vi } from "vitest";

import { isVerificationNeeded, VerificationCancelled, withVerification } from "./verify";

const needed = { exc_type: "VerificationNeeded", message: "Confirm it is you to continue." };

describe("fresh check", () => {
	it("recognises seal_common's VerificationNeeded however it arrives", () => {
		expect(isVerificationNeeded(needed)).toBe(true);
		expect(isVerificationNeeded({ payload: needed })).toBe(true);
		expect(isVerificationNeeded({ exception: "seal_common.otp.recent.VerificationNeeded: Confirm it is you" })).toBe(true);
		expect(isVerificationNeeded({ exc_type: "PermissionError" })).toBe(false);
		expect(isVerificationNeeded(null)).toBe(false);
	});

	it("goes straight through where no check is asked", async () => {
		const verify = vi.fn();
		expect(await withVerification(async () => "Waiting for HR", verify)).toBe("Waiting for HR");
		expect(verify).not.toHaveBeenCalled();
	});

	it("asks the person once, then tries again", async () => {
		const send = vi.fn().mockRejectedValueOnce(needed).mockResolvedValueOnce("Waiting for HR");
		const verify = vi.fn().mockResolvedValue(true);
		expect(await withVerification(send, verify)).toBe("Waiting for HR");
		expect(send).toHaveBeenCalledTimes(2);
		expect(verify).toHaveBeenCalledTimes(1);
	});

	it("sends nothing when the person cancels", async () => {
		const send = vi.fn().mockRejectedValue(needed);
		await expect(withVerification(send, async () => false)).rejects.toBeInstanceOf(VerificationCancelled);
		expect(send).toHaveBeenCalledTimes(1);
	});

	it("passes any other refusal on", async () => {
		const refused = { exc_type: "ValidationError", message: "Otieno already has a request waiting for HR." };
		await expect(withVerification(() => Promise.reject(refused), async () => true)).rejects.toBe(refused);
	});
});
