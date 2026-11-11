// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Travel requests (1.27.0, EM-3 to EM-8): Otieno asks to travel from Nairobi to Kisumu; the form names
 * Achieng, his line manager, as the one who will approve it ("X will approve it.", EM-11); she
 * approves it from Approvals, through the shipped Frappe Workflow "Travel Request".
 */

import { expect, test } from "@playwright/test";

import { expectNoSidewaysScroll, seeded, signIn, state, watchErrors } from "../fixtures";

const MY_HR = "/my-desk/apps/my-hr";

test.describe.configure({ mode: "serial" });

test("Otieno sends a travel request; the form says Achieng will approve it", async ({ page }) => {
	const errors = watchErrors(page);
	const who = await seeded(page.request);
	await signIn(page, who.otieno_user, who.password);

	await page.goto(MY_HR);
	await page.getByRole("button", { name: /Travel Requests/ }).first().click();
	await expect(page.getByRole("heading", { name: "Travel Requests" }).first()).toBeVisible();
	await page.getByRole("button", { name: "New Travel Request" }).first().click();
	await expect(page.getByRole("heading", { name: "New Travel Request" }).first()).toBeVisible();
	await expect(page.getByText("Achieng Odhiambo will approve it.")).toBeVisible();

	await page.getByRole("combobox", { name: "Travel Type" }).click();
	await page.getByRole("option", { name: "Domestic" }).click();
	await page.getByRole("combobox", { name: "Purpose of Travel" }).click();
	await page.getByRole("option", { name: who.travel_purpose }).click();
	await page.getByRole("textbox", { name: "From", exact: true }).fill("Nairobi");
	await page.getByRole("textbox", { name: "To", exact: true }).fill("Kisumu");
	await page.getByLabel("Other Details").fill("Kisumu county health outreach review with the ward teams");
	await expectNoSidewaysScroll(page);
	await page.getByRole("button", { name: "Send for Approval" }).click();
	await expect(page.getByText("Travel request sent to Achieng Odhiambo.")).toBeVisible();
	await expect.poll(async () => (await state(page.request)).travel[0]?.workflow_state).toBe("Pending Approval");
	const sent = (await state(page.request)).travel[0];
	expect(sent).toMatchObject({ docstatus: 0, purpose_of_travel: who.travel_purpose, company: who.company });
	// The record: the journey, and Achieng named as his line manager.
	await expect(page.getByText("Nairobi to Kisumu").first()).toBeVisible();
	await expect(page.getByText("Achieng Odhiambo").first()).toBeVisible();
	expect(errors).toEqual([]);
});

test("Achieng approves the travel request from the Approvals tab", async ({ page }) => {
	const errors = watchErrors(page);
	const who = await seeded(page.request);
	await signIn(page, who.achieng_user, who.password);
	await page.goto("/my-desk/approvals");
	await expect(page.getByRole("heading", { name: "Approvals" }).first()).toBeVisible();
	// A workflow approval, listed under the document's kind, titled by the traveller.
	const card = page.getByRole("region", { name: "Travel Request" }).locator("[data-slot=card]").filter({ hasText: /Otieno Ochieng/ });
	await expect(card).toHaveCount(1);
	await expect(card).toContainText("Pending Approval");
	await card.getByRole("button", { name: "Approve" }).click();
	await expect.poll(async () => (await state(page.request)).travel[0]).toMatchObject({ workflow_state: "Approved", docstatus: 1 });
	await expect(card).toHaveCount(0);
	expect(errors).toEqual([]);
});
