// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Timesheet approval, end to end in the browser, with two logins.
 *
 * Otieno records a day and clicks Send for Approval (the form offers no plain
 * Submit where approval is on); Achieng, his leave approver, opens it, reads the
 * banner and clicks Approve. What this catches that the Python suite cannot:
 * the stock Timesheet form still loads with our script, the primary Submit is
 * gone, and an approver with no role on Timesheet reaches it through the share.
 *
 * Seeded and removed with `_toil_fixtures.browser_set_up` / `browser_tear_down`.
 */

import { test, expect, request, Browser, Page } from "@playwright/test";

import { runPython, runPythonVoid } from "../fixtures/bench";
import { assertNoErrorDialog, assertViewRendered, collectErrors, ourErrors } from "../fixtures/desk";

const OTIENO_PASSWORD = "Otieno-Kilimani-2026!";
const ACHIENG_PASSWORD = "Achieng-Kilimani-2026!";

type Seed = { employee: string; otieno_user: string; achieng_user: string; working_day: string };
let seed: Seed;
let timesheet = "";

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
	seed = await runPython<Seed>(`
from seal_hrms.tests import _toil_fixtures as tf
return tf.browser_set_up(${JSON.stringify(OTIENO_PASSWORD)}, ${JSON.stringify(ACHIENG_PASSWORD)}, timesheet_approval=1)
`);
});

test.afterAll(async () => {
	if (!seed) return;
	await runPythonVoid(`
from seal_hrms.tests import _toil_fixtures as tf
tf.browser_tear_down(json.loads(${JSON.stringify(JSON.stringify(seed))}))
`);
});

async function signedIn(browser: Browser, baseURL: string | undefined, usr: string, pwd: string) {
	const api = await request.newContext({ baseURL });
	const login = await api.post("/api/method/login", { form: { usr, pwd } });
	expect(login.status(), `${usr} can log in`).toBe(200);
	const context = await browser.newContext({ storageState: await api.storageState() });
	await api.dispose();
	return context;
}

function banner(page: Page) {
	// Desk keeps earlier pages in the DOM: the banner that counts is the one on screen.
	return page.locator(".seal-where-it-is:visible");
}

test("Otieno records a day and sends it for approval", async ({ browser, baseURL }) => {
	const context = await signedIn(browser, baseURL, seed.otieno_user, OTIENO_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto("/app/timesheet/new");
	await assertViewRendered(page);
	await page.evaluate(
		async ({ employee, day }) => {
			const frm = (window as any).cur_frm;
			await frm.set_value("company", "_Test Company");
			await frm.set_value("employee", employee);
			const row = (frm.doc.time_logs || [])[0] || frm.add_child("time_logs");
			Object.assign(row, {
				activity_type: "Community Outreach",
				from_time: `${day} 08:00:00`,
				to_time: `${day} 18:00:00`,
				hours: 10,
				description: "Household visits in Mathare North",
			});
			frm.refresh_field("time_logs");
		},
		{ employee: seed.employee, day: seed.working_day }
	);
	await page.keyboard.press("Control+s");
	await page.waitForURL(/timesheet\/TS-/);
	timesheet = decodeURIComponent(page.url().split("/").pop() || "");
	await expect(banner(page)).toContainText("Not sent yet.");
	await expect(page.locator(".page-actions .primary-action:visible", { hasText: "Submit" })).toHaveCount(0);
	await page.getByRole("button", { name: "Send for Approval" }).click();
	await expect(banner(page)).toContainText("Waiting for");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});

test("Achieng approves it", async ({ browser, baseURL }) => {
	expect(timesheet, "the first test made a timesheet").not.toBe("");
	const context = await signedIn(browser, baseURL, seed.achieng_user, ACHIENG_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto(`/app/timesheet/${timesheet}`);
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("click Approve");
	await page.getByRole("button", { name: "Approve", exact: true }).click();
	await expect(banner(page)).toContainText("Approved by");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});

test("Otieno claims the extra two hours as time off", async ({ browser, baseURL }) => {
	expect(timesheet, "the first test made a timesheet").not.toBe("");
	const context = await signedIn(browser, baseURL, seed.otieno_user, OTIENO_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto(`/app/timesheet/${timesheet}`);
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("Claim as Time Off in Lieu");
	await page.getByRole("button", { name: "Claim as Time Off in Lieu" }).click();
	await page.waitForURL(/time-off-in-lieu-claim\/new/);
	// The address changes before the new form is drawn: wait for the claim to be the current form.
	await page.waitForFunction(() => (window as any).cur_frm?.doctype === "Time Off in Lieu Claim");
	const lines = await page.evaluate(() =>
		(window as any).cur_frm.doc.lines.map((l: any) => [l.hours, l.timesheet])
	);
	expect(lines).toEqual([[2, timesheet]]);
	await page.keyboard.press("Control+s");
	await page.waitForURL(/time-off-in-lieu-claim\/TOIL-/);
	await expect(banner(page)).toContainText("Draft: not yet sent.");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});
