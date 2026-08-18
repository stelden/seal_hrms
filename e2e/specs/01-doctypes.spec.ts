// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Coverage sweep: every seal_hrms doctype a user can open, list and form.
 *
 * The assertion that matters is the ERROR CHECK, not the page title. A form
 * script that throws on load, a link query naming a field that no longer
 * exists, a workspace block whose label does not match — none of these fail a
 * Python test or appear in the server log, and every one is the difference
 * between a working form and a blank one.
 */

import { test, expect } from "@playwright/test";

import { statePathFor } from "../fixtures/auth";
import { collectErrors, ourErrors, assertNoErrorDialog, assertViewRendered } from "../fixtures/desk";

test.use({ storageState: statePathFor("admin") });

const LISTABLE = [
 "Employee Dependent and Beneficiary",
 "Employee Separation Type",
 "Task Assignment"
];

/** Singles have no list view — `/app/<single>` lands straight on the form. */
const SINGLES = ["SEAL HRMS Settings"];

const slug = (dt: string) => dt.toLowerCase().replace(/&/g, "").replace(/\s+/g, "-");

test.describe("every list view opens", () => {
	for (const doctype of LISTABLE) {
		test(`list: ${doctype}`, async ({ page }) => {
			const errors = collectErrors(page);
			await page.goto(`/app/${slug(doctype)}`);
			await page.waitForLoadState("networkidle");
			await assertViewRendered(page);
			await assertNoErrorDialog(page);
			expect(ourErrors(errors), `${doctype} list raised:\n${errors.join("\n")}`).toEqual([]);
		});
	}
});


test.describe("every form opens", () => {
	for (const doctype of [...LISTABLE, ...SINGLES]) {
		test(`form: ${doctype}`, async ({ page }) => {
			const errors = collectErrors(page);
			const route = SINGLES.includes(doctype)
				? `/app/${slug(doctype)}`
				: `/app/${slug(doctype)}/new`;
			await page.goto(route);
			await page.waitForLoadState("networkidle");
			await assertViewRendered(page);
			await assertNoErrorDialog(page);
			expect(ourErrors(errors), `${doctype} form raised:\n${errors.join("\n")}`).toEqual([]);
		});
	}
});
