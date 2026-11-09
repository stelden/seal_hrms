// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * A timesheet filled in as a week, in the browser.
 *
 * Otieno opens a new timesheet; ERPNext fills in who he is (through seal_hrms,
 * since his login field is closed to him), the week grid appears with the
 * company's default kind of work, he types hours into two days and saves, and
 * the server writes the time lines from the week. What this catches that the
 * Python suite cannot: the grid draws, its inputs reach the form, the form does
 * not demand time lines the server is about to write, and nothing throws.
 */

import { test, expect, request, Browser } from "@playwright/test";

import { runPython, runPythonVoid } from "../fixtures/bench";
import { assertNoErrorDialog, assertViewRendered, collectErrors, ourErrors } from "../fixtures/desk";

const OTIENO_PASSWORD = "Otieno-Kilimani-2026!";
const ACHIENG_PASSWORD = "Achieng-Kilimani-2026!";

type Seed = { employee: string; otieno_user: string };
let seed: Seed;

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
	seed = await runPython<Seed>(`
from seal_hrms.tests import _toil_fixtures as tf
return tf.browser_set_up(${JSON.stringify(OTIENO_PASSWORD)}, ${JSON.stringify(ACHIENG_PASSWORD)},
    weekly_timesheets=1, timesheet_approval=1, default_activity_type="Community Outreach")
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

test("Otieno fills in his week in the grid", async ({ browser, baseURL }) => {
	const context = await signedIn(browser, baseURL, seed.otieno_user, OTIENO_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto("/app/timesheet/new");
	await assertViewRendered(page);
	const grid = page.locator(".seal-week");
	await expect(grid).toBeVisible({ timeout: 30_000 });
	await expect(grid.locator("th").first()).toContainText("Activity Type");
	const cells = grid.locator("tbody tr").first().locator('input[type="number"]');
	await expect(cells).toHaveCount(7);
	await cells.nth(0).fill("7.5");
	await cells.nth(0).dispatchEvent("change");
	await cells.nth(1).fill("8");
	await cells.nth(1).dispatchEvent("change");
	await expect(grid.locator(".seal-week-totals th.text-right").last()).toContainText("15.5");

	await page.keyboard.press("Control+s");
	await page.waitForURL(/timesheet\/TS-/);
	const lines = await page.evaluate(() => (window as any).cur_frm.doc.time_logs.map((t: any) => t.hours));
	expect(lines).toEqual([7.5, 8]);
	await expect(page.locator(".seal-week")).toBeVisible();
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});
