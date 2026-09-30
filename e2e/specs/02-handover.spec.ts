// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * A leave handover, end to end in the browser.
 *
 * Wanjiku has leave coming up. HR prepares her handover from the Leave
 * Application, names Otieno and sends it; Otieno logs in, reads what is asked
 * of him on the banner, and accepts. What this catches that the Python suite
 * cannot: the buttons exist and are named the way the banner says, the form
 * scripts do not throw, and a stand-in who is not HR can open a colleague's
 * handover at all (HRMS's "Employee = themselves" User Permission would
 * otherwise hide it from him).
 */

import { test, expect, request, Page } from "@playwright/test";

import { statePathFor } from "../fixtures/auth";
import { runPython, runPythonVoid } from "../fixtures/bench";
import { assertNoErrorDialog, assertViewRendered, collectErrors, ourErrors } from "../fixtures/desk";

const STAND_IN_PASSWORD = "Otieno-Kilimani-2026!";

type Seed = { la: string; wanjiku: string; otieno: string; otieno_user: string };
let seed: Seed;
let handover = "";

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
	seed = await runPython<Seed>(`
from frappe.utils.password import update_password
from seal_hrms.tests import _handover_fixtures as fx
w = fx.ensure_employee("wanjiku")
o = fx.ensure_employee("otieno")
fx.cleanup([w, o])
user = frappe.get_doc("User", fx.email("otieno"))
user.user_type = "System User"
user.save(ignore_permissions=True)
update_password(user.name, ${JSON.stringify(STAND_IN_PASSWORD)})
la = fx.leave(w, 6, 3)
return {"la": la.name, "wanjiku": w, "otieno": o, "otieno_user": user.name}
`);
});

test.afterAll(async () => {
	await runPythonVoid(`
from seal_hrms.tests import _handover_fixtures as fx
fx.cleanup([${JSON.stringify(seed.wanjiku)}, ${JSON.stringify(seed.otieno)}])
`);
});

async function banner(page: Page) {
	return page.locator(".form-message .ta-banner");
}

test.describe("handover", () => {
	test.use({ storageState: statePathFor("admin") });

	test("HR prepares and sends a handover from the leave application", async ({ page }) => {
		const errors = collectErrors(page);
		await page.goto(`/app/leave-application/${seed.la}`);
		await assertViewRendered(page);
		await page.getByRole("button", { name: "Prepare Handover" }).click();
		await page.waitForURL(/task-assignment\//);
		await assertViewRendered(page);
		await expect(await banner(page)).toContainText("Not sent to the stand-in yet");

		handover = await page.evaluate(async ({ otieno }) => {
			const frm = (window as any).cur_frm;
			await frm.set_value("task_assignee", otieno);
			await frm.set_value("task_description", "<p>Keep the Westlands reconciliations moving.</p>");
			await frm.save();
			return frm.doc.name;
		}, { otieno: seed.otieno });
		// The banner's Do row names Submit; press the real button, not frm.savesubmit().
		await expect(await banner(page)).toContainText("click Submit");
		await page.locator(".page-actions .primary-action:visible", { hasText: "Submit" }).click();
		await page.getByRole("button", { name: "Yes" }).click();
		await expect(await banner(page)).toContainText("Waiting for the stand-in to agree");
		await assertNoErrorDialog(page);
		expect(ourErrors(errors), errors.join("\n")).toEqual([]);
	});

	test("the reports open", async ({ page }) => {
		for (const report of ["Who Is Covering Whom", "Stand-in Load"]) {
			const errors = collectErrors(page);
			await page.goto(`/app/query-report/${encodeURIComponent(report)}`);
			await page.waitForLoadState("networkidle");
			// The footer appears once the report has actually run, whether or not it found rows.
			await expect(page.getByText("Execution Time")).toBeVisible({ timeout: 30_000 });
			await assertNoErrorDialog(page);
			expect(ourErrors(errors), `${report}:\n${errors.join("\n")}`).toEqual([]);
		}
	});
});

test("the stand-in reads what is asked of him, and accepts", async ({ browser, baseURL }) => {
	expect(handover, "the first test prepared a handover").not.toBe("");
	const api = await request.newContext({ baseURL });
	const login = await api.post("/api/method/login", { form: { usr: seed.otieno_user, pwd: STAND_IN_PASSWORD } });
	expect(login.status(), "the stand-in can log in").toBe(200);
	const context = await browser.newContext({ storageState: await api.storageState() });
	const page = await context.newPage();
	const errors = collectErrors(page);

	await page.goto(`/app/task-assignment/${handover}`);
	await assertViewRendered(page);
	await expect(await banner(page)).toContainText("Click Accept");
	await page.getByRole("button", { name: "Accept", exact: true }).click();
	await expect(await banner(page)).toContainText("Agreed. Nothing has moved yet.");
	await assertNoErrorDialog(page);
	expect(ourErrors(errors), errors.join("\n")).toEqual([]);

	await context.close();
	await api.dispose();
});
