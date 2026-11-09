// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * A time off in lieu claim, end to end in the browser, with two logins.
 *
 * Otieno worked a Sunday at a community health drive. He lists it on a claim,
 * reads the banner and chooses Actions → Send for Approval; Achieng, his leave
 * approver, returns it once with a reason (the dialog the workflow action asks
 * for), he sends it again, and she chooses Actions → Approve; Otieno then sees
 * the time added and the Apply for Leave button the banner names.
 *
 * The claim moves by Frappe Workflow (decision 2026-11-10), so this also checks
 * that the Actions menu offers each person the right moves.
 *
 * What this catches that the Python suite cannot: the Now / Next / Do banner
 * draws, its Do row names actions that really are on the screen, an approver
 * who is not HR can open a colleague's claim, and no form script throws.
 *
 * Seeded and removed with `_toil_fixtures.browser_set_up` / `browser_tear_down`,
 * which put Otieno's record back as it was.
 */

import { test, expect, request, Browser, Page } from "@playwright/test";

import { runPython, runPythonVoid } from "../fixtures/bench";
import { assertNoErrorDialog, assertViewRendered, collectErrors, ourErrors } from "../fixtures/desk";

const OTIENO_PASSWORD = "Otieno-Kilimani-2026!";
const ACHIENG_PASSWORD = "Achieng-Kilimani-2026!";

type Seed = { employee: string; otieno_user: string; achieng_user: string; rest_day: string };
let seed: Seed;
let claim = "";

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
	seed = await runPython<Seed>(`
from seal_hrms.tests import _toil_fixtures as tf
return tf.browser_set_up(${JSON.stringify(OTIENO_PASSWORD)}, ${JSON.stringify(ACHIENG_PASSWORD)})
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

/** Choose an action from the workflow's Actions menu, as a person would. */
async function chooseAction(page: Page, action: string) {
	await page.getByRole("button", { name: "Actions" }).click();
	await page.getByRole("menuitem", { name: action, exact: true }).click();
}

function banner(page: Page) {
	// Desk keeps earlier pages in the DOM: the banner that counts is the one on screen.
	return page.locator(".seal-where-it-is:visible");
}

test("Otieno lists the Sunday he worked and sends it", async ({ browser, baseURL }) => {
	const context = await signedIn(browser, baseURL, seed.otieno_user, OTIENO_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto("/app/time-off-in-lieu-claim/new");
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("A new claim");
	await page.evaluate(
		async ({ employee, day }) => {
			const frm = (window as any).cur_frm;
			if (frm.doc.employee !== employee) await frm.set_value("employee", employee);
			// The form starts with one blank row, as a person would see it: fill that one.
			const values = { work_date: day, hours: 8, work_done: "Community health drive in Kibera" };
			const line = (frm.doc.lines || [])[0] || frm.add_child("lines");
			Object.assign(line, values);
			frm.refresh_field("lines");
		},
		{ employee: seed.employee, day: seed.rest_day }
	);
	// Saving a new claim moves the page to its new address, so press Save as a person would.
	await page.keyboard.press("Control+s");
	await page.waitForURL(/time-off-in-lieu-claim\/TOIL-/);
	claim = decodeURIComponent(page.url().split("/").pop() || "");
	await expect(banner(page)).toContainText("Draft: not yet sent.");
	await expect(banner(page)).toContainText("Send for Approval");
	await chooseAction(page, "Send for Approval");
	await expect(banner(page)).toContainText("Waiting for");
	await expect(banner(page)).toContainText("Nothing for now");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});

test("Achieng returns it with a reason, and Otieno sends it again", async ({ browser, baseURL }) => {
	expect(claim, "the first test made a claim").not.toBe("");
	const approver = await signedIn(browser, baseURL, seed.achieng_user, ACHIENG_PASSWORD);
	let page = await approver.newPage();
	let errors = collectErrors(page);
	await page.goto(`/app/time-off-in-lieu-claim/${claim}`);
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("Actions → Return");
	await chooseAction(page, "Return");
	const dialog = page.locator(".modal.show");
	await expect(dialog).toContainText("Return the claim");
	await dialog.locator("textarea[data-fieldname=reason]").fill("Say which households you visited");
	await dialog.getByRole("button", { name: "Return" }).click();
	await expect(banner(page)).toContainText("Say which households you visited");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await approver.close();

	const person = await signedIn(browser, baseURL, seed.otieno_user, OTIENO_PASSWORD);
	page = await person.newPage();
	errors = collectErrors(page);
	await page.goto(`/app/time-off-in-lieu-claim/${claim}`);
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("Say which households you visited");
	await chooseAction(page, "Send for Approval");
	await expect(banner(page)).toContainText("Waiting for");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await person.close();
});

test("Achieng reads what is asked of her and approves", async ({ browser, baseURL }) => {
	expect(claim, "the first test made a claim").not.toBe("");
	const context = await signedIn(browser, baseURL, seed.achieng_user, ACHIENG_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto(`/app/time-off-in-lieu-claim/${claim}`);
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("Actions → Approve");
	await expect(banner(page)).toContainText("no record behind them");
	await chooseAction(page, "Approve");
	await expect(banner(page)).toContainText("Approved: 1 day added");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});

test("Otieno sees the time added and how to take it", async ({ browser, baseURL }) => {
	const context = await signedIn(browser, baseURL, seed.otieno_user, OTIENO_PASSWORD);
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto(`/app/time-off-in-lieu-claim/${claim}`);
	await assertViewRendered(page);
	await expect(banner(page)).toContainText("Apply for Leave");
	await expect(page.getByRole("button", { name: "Apply for Leave" })).toBeVisible();
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	await context.close();
});
