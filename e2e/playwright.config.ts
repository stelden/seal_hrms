// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end suite for seal_hrms, running against dev.local.
 *
 * `http://localhost` IS dev.local on this bench — the site sets `host_name` and
 * the bench sets `serve_default_site`. `:8000` is the bare gunicorn upstream and
 * serves no static assets, and `dev.local` is not in /etc/hosts, so this is the
 * only address that serves a complete page.
 */

const BASE_URL = process.env.SEAL_E2E_BASE_URL || "http://localhost";

export default defineConfig({
	testDir: "./specs",
	outputDir: "./artifacts/results",
	fullyParallel: false,
	workers: 1,
	retries: 1,
	timeout: 90_000,
	expect: { timeout: 15_000 },
	reporter: [["list"], ["html", { outputFolder: "./artifacts/report", open: "never" }]],
	use: {
		baseURL: BASE_URL,
		trace: "retain-on-failure",
		video: "retain-on-failure",
		screenshot: "only-on-failure",
		actionTimeout: 20_000,
		navigationTimeout: 45_000,
		userAgent: "seal_hrms-e2e/1.0 (Playwright)",
	},
	projects: [
		{ name: "setup", testMatch: /.*\.setup\.ts/ },
		{ name: "chromium", use: { ...devices["Desktop Chrome"] }, dependencies: ["setup"] },
	],
});
