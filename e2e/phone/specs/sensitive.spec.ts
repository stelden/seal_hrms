// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * "Is it still you?" before pay (1.27.0, EM-9 and EM-10; SEAL HRMS Settings → Confirm It Is You, both
 * on, five minutes, as a site that never saved them reads). Otieno's phone has been signed in for a
 * while (`/__harness/stale`): his payslips and where his pay goes stay hidden until he confirms with
 * his password, and a mistyped password neither shows them nor signs him out (seal_common 1.38.1).
 */

import { expect, test, type Page } from "@playwright/test";

import { expectNoSidewaysScroll, harness, seeded, signIn, watchErrors } from "../fixtures";

const MY_HR = "/my-desk/apps/my-hr";

/** The shell's Confirm It Is You dialog: a wrong password first, then the right one. */
async function confirmWithPassword(page: Page, password: string) {
	const dialog = page.getByRole("dialog");
	await expect(dialog.getByText("Confirm It Is You")).toBeVisible();
	await dialog.getByLabel("Password").fill("Kibera-Walk#2025");
	await dialog.getByRole("button", { name: "Confirm" }).click();
	await expect(dialog.getByText("That password is not right.")).toBeVisible();
	await dialog.getByLabel("Password").fill(password);
	await dialog.getByRole("button", { name: "Confirm" }).click();
	await expect(dialog).toHaveCount(0);
}

test("payslips: a stale session is asked first, and the password shows them", async ({ page }) => {
	const errors = watchErrors(page);
	const who = await seeded(page.request);
	await signIn(page, who.otieno_user, who.password);
	await harness(page.request, "stale", {});

	// The server refuses the list itself, not only the screen.
	const refused = await page.request.get("/api/method/seal_hrms.my_desk.api.payslips");
	expect(refused.ok()).toBeFalsy();
	expect((await refused.json()).exc_type).toBe("VerificationNeeded");

	await page.goto(`${MY_HR}/pay`);
	// Asked on arrival; nothing about his pay shows behind the question.
	await expect(page.getByRole("dialog").getByText("Confirm It Is You")).toBeVisible();
	await expect(page.getByText(/^Net pay/)).toHaveCount(0);
	await confirmWithPassword(page, who.password);
	await expect(page.getByText(/^Net pay/).first()).toBeVisible();
	// Still signed in after the mistyped password: the boot still knows him.
	const boot = await page.request.get("/api/method/seal_desk.api.phone.boot");
	expect((await boot.json()).message?.user?.name).toBe(who.otieno_user);
	await expectNoSidewaysScroll(page);
	expect(errors).toEqual([]);
});

test("My Details: where pay goes is held back until he confirms", async ({ page }) => {
	const errors = watchErrors(page);
	const who = await seeded(page.request);
	await signIn(page, who.otieno_user, who.password);
	await harness(page.request, "stale", {});

	await page.goto(`${MY_HR}/me`);
	await expect(page.getByRole("heading", { name: "My Details" }).first()).toBeVisible();
	// The rest of his details show at once; only the payout is held back, and he is not asked on arrival.
	await expect(page.getByText(who.otieno_name).first()).toBeVisible();
	await expect(page.getByText("Your payout details show once you confirm it is you.")).toBeVisible();
	await expect(page.getByRole("dialog")).toHaveCount(0);
	await expect(page.getByText("Mobile Money", { exact: true })).toHaveCount(0);

	await page.getByRole("button", { name: "Confirm", exact: true }).click();
	await confirmWithPassword(page, who.password);
	await expect(page.getByText("Your payout details show once you confirm it is you.")).toHaveCount(0);
	await expect(page.getByText("Mobile Money", { exact: true })).toBeVisible();
	expect(errors).toEqual([]);
});
