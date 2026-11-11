// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * The Self Service section in a browser at a phone's size (390×844), without seal_desk's shell (MY_DESK_P5_PLAN
 * §8): the test host (e2e/host, built to e2e/.host) lends React and the library through an import map as
 * the shell does, and loads the committed bundle (../seal_hrms/public/my-desk). A stub of the site
 * answers the section's endpoints with Otieno Ochieng's records and keeps what was posted.
 *
 *   npm run e2e        (builds the host first; Playwright from ../e2e/node_modules, pinned 1.62.1)
 *
 * Screenshots go to e2e/.shots/ (ignored by git).
 */

import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { extname, join, normalize } from "node:path";

const here = new URL(".", import.meta.url).pathname;
const require = createRequire(join(here, "..", "..", "e2e", "package.json"));
const { chromium } = require("@playwright/test");

const HOST_OUT = join(here, ".host");
const SECTION_OUT = join(here, "..", "..", "seal_hrms", "public", "my-desk");
const SHOTS = join(here, ".shots");
const TYPES = { ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".woff2": "font/woff2", ".svg": "image/svg+xml" };
const API = "/api/method/seal_hrms.my_desk.api.";

const monday = (() => {
	const d = new Date();
	d.setDate(d.getDate() - ((d.getDay() + 6) % 7) - 7); // last week's Monday: the screen opens on its Monday
	return d.toISOString().slice(0, 10);
})();
const days = Array.from({ length: 7 }, (_, i) => {
	const d = new Date(`${monday}T12:00:00Z`);
	d.setUTCDate(d.getUTCDate() + i);
	return { date: d.toISOString().slice(0, 10), kind: i > 4 ? "Rest day" : "Working day", leave: null, leave_fraction: 0, attendance_hours: i === 0 ? 8 : null };
});

/** What the site answers, by method. */
const ANSWERS = {
	home: {
		employee: { name: "HR-EMP-00031", employee_name: "Otieno Ochieng", company: "Kilimani Community Trust" },
		balances: [
			{ key: "leave_left:Annual Leave", label: "Annual Leave left", value: 14 },
			{ key: "toil_left", label: "Time off in lieu left", value: 1.5 },
		],
		in_flight: [{ key: "claims_in_approval", label: "Claims in approval", count: 2, doctype: "Expense Claim" }],
		checkin: { offered: true, location: false },
	},
	leave_list: [
		{ name: "HR-LAP-2026-00042", leave_type: "Annual Leave", from_date: "2026-12-14", to_date: "2026-12-18", total_leave_days: 5, status: "Open", docstatus: 0, handover: { name: "HR-TA-2611-00003", status: "Awaiting Acceptance", stand_in: "Njeri Mwangi" } },
	],
	timesheet_week: {
		weekly: true,
		checks: [],
		week_start: monday,
		hours_per_day: 8,
		default_activity_type: "Community Outreach",
		days,
		previous_entries: [{ row: 1, activity_type: "Community Outreach", description: "Household visits in Mathare North", hours: [8, 8, 8, 8, 8, 0, 0] }],
		activity_types: ["Community Outreach", "Training"],
		approval: true,
		timesheet: null,
	},
	payout_request_record: { name: "PCR-2026-00004", status: "Draft", change: "Bank Account", bank: "Kilimani Cooperative Bank", account_no: "•••• 6311", account_name: "Otieno Ochieng", has_evidence: true, mine: true },
	save_timesheet_week: { name: "TS-2026-00012", state: "Waiting for Approval" },
};

function stub() {
	const posted = [];
	let sends = 0;
	const manifest = JSON.parse(readFileSync(join(HOST_OUT, ".vite", "manifest.json"), "utf8"));
	const page = manifest["index.html"];
	const base = "/assets/e2e_host/my-desk/";
	const importmap = readFileSync(join(HOST_OUT, "importmap.json"), "utf8");
	const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><script>window.csrf_token="e2e";</script><script type="importmap">${importmap}</script>${(page.css ?? []).map((href) => `<link rel="stylesheet" href="${base}${href}">`).join("")}</head><body><div id="root"></div><script type="module" src="${base}${page.file}"></script></body></html>`;
	const roots = { e2e_host: HOST_OUT, seal_hrms: SECTION_OUT };

	const server = createServer((request, response) => {
		const url = new URL(request.url, "http://stub");
		const send = (status, body, type = "application/json") => {
			response.writeHead(status, { "Content-Type": type });
			response.end(typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body));
		};
		if (url.pathname.startsWith("/my-desk")) return send(200, html, "text/html");
		if (url.pathname.startsWith("/api/method/")) {
			let body = "";
			request.on("data", (chunk) => (body += chunk));
			request.on("end", () => {
				const method = url.pathname.slice("/api/method/".length);
				if (request.method === "POST") posted.push({ method, body: body ? JSON.parse(body) : {} });
				if (method === "seal_hrms.seal_hrms.payout_change.send") {
					sends += 1; // the first send has no fresh check: refuse it as seal_common does
					if (sends === 1) return send(403, { exc_type: "VerificationNeeded", _server_messages: JSON.stringify([JSON.stringify({ message: "Confirm it is you to continue." })]) });
					return send(200, { message: "Waiting for HR" });
				}
				const key = method.startsWith(API.slice("/api/method/".length)) ? method.slice(API.length - "/api/method/".length) : method;
				return send(200, { message: ANSWERS[key] ?? null });
			});
			return;
		}
		const match = /^\/assets\/(\w+)\/my-desk\/(.+)$/.exec(url.pathname);
		const root = match && roots[match[1]];
		if (root) {
			const file = normalize(join(root, match[2]));
			if (file.startsWith(root) && existsSync(file)) return send(200, readFileSync(file), TYPES[extname(file)] ?? "application/octet-stream");
		}
		send(404, "not found", "text/plain");
	});
	return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve({ server, posted, origin: `http://127.0.0.1:${server.address().port}` })));
}

async function until(page, what, fn, arg) {
	try {
		await page.waitForFunction(fn, arg, { timeout: 15000 });
	} catch {
		throw new Error(`timed out waiting for ${what}`);
	}
}

const site = await stub();
mkdirSync(SHOTS, { recursive: true });
const browser = await chromium.launch();
const failures = [];
try {
	const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
	const page = await context.newPage();
	const errors = [];
	page.on("pageerror", (e) => errors.push(String(e)));

	const step = async (name, fn) => {
		try {
			await fn();
			console.log(`ok   ${name}`);
		} catch (error) {
			failures.push(`${name}: ${error.message}`);
			console.log(`FAIL ${name}: ${error.message}`);
		}
		await page.screenshot({ path: join(SHOTS, `${name.replace(/\W+/g, "-").toLowerCase()}.png`), fullPage: true });
	};
	const fits = async () => {
		const width = await page.evaluate(() => document.documentElement.scrollWidth);
		if (width > 390) throw new Error(`the page scrolls sideways (${width}px wide)`);
	};

	await step("home shows balances and every area", async () => {
		await page.goto(`${site.origin}/my-desk/apps/my-hr`);
		await until(page, "the home screen", () => document.body.innerText.includes("Annual Leave left"));
		for (const text of ["14 days", "Claims in approval", "Apply for Leave", "Everything in Self Service", "Payslips"]) {
			if (!(await page.getByText(text).first().isVisible())) throw new Error(`"${text}" not shown`);
		}
		await fits();
	});

	await step("leave list opens from home", async () => {
		await page.getByText("Leave", { exact: true }).first().click();
		await until(page, "the leave list", () => document.body.innerText.includes("covered by Njeri Mwangi"));
		await fits();
	});

	await step("timesheet week: copy last week, change Monday, send", async () => {
		await page.goto(`${site.origin}/my-desk/apps/my-hr/timesheet/week/${monday}`);
		await until(page, "the week", () => document.body.innerText.includes("Copy Last Week"));
		await page.getByText("Copy Last Week").click();
		await page.getByLabel("Hours on Monday").fill("7.5");
		await page.getByText("Send for Approval").click();
		await until(page, "the week to be sent", () => document.body.innerText.includes("Week sent for approval."));
		const sent = site.posted.find((p) => p.method.endsWith("save_timesheet_week"));
		const entries = JSON.parse(sent.body.entries);
		if (sent.body.send !== 1 || entries[0].hours[0] !== 7.5 || entries[0].hours[1] !== 0) throw new Error(`sent ${JSON.stringify(sent.body)}`);
		await fits();
	});

	await step("payout change: confirm it is you, then sent", async () => {
		await page.goto(`${site.origin}/my-desk/apps/my-hr/me/payout/PCR-2026-00004`);
		await until(page, "the request", () => document.body.innerText.includes("•••• 6311"));
		await page.getByText("Send to HR").first().click();
		await until(page, "the request to be sent", () => document.body.innerText.includes("Sent to HR."));
		const checks = await page.evaluate(() => window.__verifications);
		const sends = site.posted.filter((p) => p.method.endsWith("payout_change.send")).length;
		if (checks !== 1 || sends !== 2) throw new Error(`verifications ${checks}, sends ${sends}`);
		await fits();
	});

	if (errors.length) failures.push(`page errors: ${errors.join(" | ")}`);
} finally {
	await browser.close();
	site.server.close();
}
if (failures.length) {
	console.error(`\n${failures.length} failed:\n- ${failures.join("\n- ")}`);
	process.exit(1);
}
console.log("\nall phone checks passed");
