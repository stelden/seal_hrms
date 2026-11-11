// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Compensatory leave requests (1.28.0, CL-1 to CL-5): Otieno worked the public holiday (Utamaduni Day, on his
 * own holiday list, present that day) and asks for a day off in return. The form offers the compensatory types
 * time off in lieu does not bank and says Achieng, his leave approver, will approve it; she approves it from
 * Approvals and Frappe HR adds the day. Runs before the week's walk and leaves nothing waiting, so that walk's
 * count of four approvals holds.
 */

import { expect, test } from "@playwright/test";

import { expectNoSidewaysScroll, seeded, signIn, state, watchErrors } from "../fixtures";

const MY_HR = "/my-desk/apps/my-hr";

test.describe.configure({ mode: "serial" });

test("Otieno asks for compensatory leave; the form says Achieng will approve it", async ({ page }) => {
	const errors = watchErrors(page);
	const who = await seeded(page.request);
	await signIn(page, who.otieno_user, who.password);

	await page.goto(MY_HR);
	await page.getByRole("button", { name: /Compensatory Leave/ }).first().click();
	await expect(page.getByRole("heading", { name: "Compensatory Leave" }).first()).toBeVisible();
	await page.getByRole("button", { name: "New Request" }).first().click();
	await expect(page.getByRole("heading", { name: "New Compensatory Leave Request" }).first()).toBeVisible();
	await expect(page.getByText("Achieng Odhiambo will approve it.")).toBeVisible();

	await page.getByRole("combobox", { name: "Leave Type" }).click();
	// Time off in lieu's own type is never offered here (CL-1).
	await expect(page.getByRole("option", { name: "Kilimani Time Off in Lieu" })).toHaveCount(0);
	await page.getByRole("option", { name: who.compensatory_type }).click();
	const [y, m, d] = who.public_holiday.split("-");
	await page.getByLabel("Work From Date").fill(`${d}-${m}-${y}`);
	await page.getByLabel("Work End Date").fill(`${d}-${m}-${y}`);
	await page.getByLabel("Reason").fill("Ran the Utamaduni Day immunisation outreach at Kibera clinic");
	await expect(page.getByText("1 days of leave if approved.")).toBeVisible();
	await expectNoSidewaysScroll(page);
	await page.getByRole("button", { name: "Send Request" }).click();
	await expect(page.getByText("Request sent.")).toBeVisible();

	await expect.poll(async () => (await state(page.request)).compensatory[0]).toMatchObject({ docstatus: 0, leave_type: who.compensatory_type, work_from_date: who.public_holiday });
	expect((await state(page.request)).compensatory[0]._assign).toContain(who.achieng_user);
	// The record: waiting, and who will approve it.
	await expect(page.getByRole("heading", { name: "Compensatory Leave Request" }).first()).toBeVisible();
	await expect(page.getByText("Waiting for Approval").first()).toBeVisible();
	await expect(page.getByText("Achieng Odhiambo will approve it.")).toBeVisible();
	expect(errors).toEqual([]);
});

test("Achieng approves it from the Approvals tab, and the day is added", async ({ page }) => {
	const errors = watchErrors(page);
	const who = await seeded(page.request);
	await signIn(page, who.achieng_user, who.password);
	await page.goto("/my-desk/approvals");
	await expect(page.getByRole("heading", { name: "Approvals" }).first()).toBeVisible();
	const card = page.locator("[data-slot=card]").filter({ hasText: /Compensatory leave for Otieno Ochieng/ });
	await expect(card).toHaveCount(1);
	await expect(card).toContainText(who.compensatory_type);
	await card.getByRole("button", { name: "Approve" }).click();
	await expect(card).toHaveCount(0);
	await expect.poll(async () => (await state(page.request)).compensatory[0]).toMatchObject({ docstatus: 1 });
	expect((await state(page.request)).compensatory[0].leave_allocation).toBeTruthy();
	expect(errors).toEqual([]);
});
