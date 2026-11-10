// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { defineConfig, devices } from "@playwright/test";

/**
 * Otieno's week of self service in the real My Desk phone app, at 390×844 (My Desk P5/P6 done-when:
 * "Otieno does a week of self service on a phone; Achieng approves it").
 *
 * Served by phone/harness.py (copied from seal_desk's P3 harness): dev.local in one process, one
 * connection and one transaction, with this worktree's seal_hrms and the phone app's other worktrees
 * first on the path. Nothing is committed; the harness rolls back when Playwright stops it.
 *
 *   npx playwright test -c playwright.phone.config.ts
 */
const PORT = Number(process.env.PHONE_E2E_PORT || 8097);
const BASE = `http://localhost:${PORT}`;
const phone = {
	viewport: { width: 390, height: 844 },
	deviceScaleFactor: 2,
	isMobile: true,
	hasTouch: true,
	userAgent: "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
};

export default defineConfig({
	testDir: "./phone/specs",
	outputDir: "./artifacts/phone-results",
	fullyParallel: false,
	workers: 1,
	retries: 0,
	timeout: 300_000,
	expect: { timeout: 20_000 },
	reporter: [["list"], ["html", { outputFolder: "./artifacts/phone-report", open: "never" }]],
	webServer: {
		command: `/home/frappe/frappe-bench/env/bin/python phone/harness.py ${PORT}`,
		url: `${BASE}/__harness/ready`,
		timeout: 180_000,
		reuseExistingServer: Boolean(process.env.PHONE_E2E_REUSE),
		stdout: process.env.PHONE_E2E_LOG ? "pipe" : "ignore",
		stderr: "pipe",
		gracefulShutdown: { signal: "SIGTERM", timeout: 20_000 },
	},
	use: {
		...devices["Desktop Chrome"],
		...phone,
		baseURL: BASE,
		trace: "retain-on-failure",
		screenshot: "only-on-failure",
		actionTimeout: 20_000,
		navigationTimeout: 45_000,
	},
	projects: [{ name: "phone" }],
});
