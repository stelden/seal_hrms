// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/** Shared Desk helpers: error capture that ignores noise we do not own. */

import { Page, expect } from "@playwright/test";

/**
 * A Frappe Desk teardown race, not ours.
 *
 * Navigating between two workspaces quickly makes Frappe's widget teardown try
 * to remove a node the new view has already replaced. It reproduces on stock
 * workspaces and does not affect what the user sees. Filtered by name rather
 * than dropping the assertion, so a real script error still fails the test.
 */
const FRAMEWORK_NOISE = [
	/Failed to execute 'removeChild' on 'Node'/,
	/ResizeObserver loop/,
];

export function collectErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
	page.on("console", (msg) => {
		if (msg.type() !== "error") return;
		const t = msg.text();
		if (/favicon|net::ERR_|Failed to load resource|socket|websocket/i.test(t)) return;
		errors.push(`console: ${t}`);
	});
	return errors;
}

export const ourErrors = (errors: string[]) =>
	errors.filter((e) => !FRAMEWORK_NOISE.some((re) => re.test(e)));

export async function assertNoErrorDialog(page: Page) {
	await expect(
		page.locator(".modal-dialog:visible", {
			hasText: /Server Error|Traceback|Something went wrong/i,
		}),
	).toHaveCount(0);
}

/** `/app/<x>` redirects to `/desk/<x>` on this build; assert on the render. */
export async function assertViewRendered(page: Page) {
	await expect(
		page.locator(".layout-main-section, .list-row-container, .frappe-list, .form-layout").first(),
	).toBeVisible({ timeout: 30_000 });
}
