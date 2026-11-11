// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { expect, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

/** What the harness made (seed.py SEEDED). */
export interface Seeded {
	otieno: string;
	njeri: string;
	otieno_user: string;
	achieng_user: string;
	njeri_user: string;
	otieno_name: string;
	achieng_name: string;
	njeri_name: string;
	password: string;
	company: string;
	payslip: string;
	leave_type: string;
	expense_type: string;
	activity: string;
	last_monday: string;
	rest_day: string;
	working_day: string;
	travel_purpose: string;
	compensatory_type: string;
	public_holiday: string;
}

/** Otieno's records as the database has them (seed.py state). */
export interface State {
	leave: { name: string; leave_type: string; status: string; docstatus: number }[];
	handovers: { name: string; docstatus: number }[];
	toil: { name: string; status: string; docstatus: number; days: number }[];
	timesheets: { name: string; custom_approval_state: string; docstatus: number; total_hours: number; custom_week_start: string }[];
	expenses: { name: string; approval_status: string; docstatus: number; total_claimed_amount: number }[];
	checkins: { name: string; log_type: string; device_id: string }[];
	payout: { name: string; status: string; change: string; mobile_no: string }[];
	travel: { name: string; workflow_state: string; docstatus: number; purpose_of_travel: string; company: string }[];
	compensatory: { name: string; leave_type: string; docstatus: number; work_from_date: string; leave_allocation: string | null; _assign: string | null }[];
	notifications: { for_user: string; subject: string; document_type: string; document_name: string }[];
}

export const state = (request: APIRequestContext) => harness<State>(request, "state");

/** Ask the harness (`/__harness/<path>`): answers come from inside its transaction. */
export async function harness<T = unknown>(request: APIRequestContext, path: string, body?: object): Promise<T> {
	const response = body ? await request.post(`/__harness/${path}`, { data: body }) : await request.get(`/__harness/${path}`);
	const json = await response.json();
	if (!response.ok()) throw new Error(`harness ${path}: ${JSON.stringify(json)}`);
	return json as T;
}

export const seeded = (request: APIRequestContext) => harness<Seeded>(request, "seeded");

/** The newest code "texted" to a mobile number (held by the harness, never sent). */
export async function latestCode(request: APIRequestContext, after = 0): Promise<string> {
	let codes: { code: string }[] = [];
	await expect
		.poll(async () => {
			codes = await harness<{ code: string }[]>(request, "codes");
			return codes.length;
		})
		.toBeGreaterThan(after);
	return codes[codes.length - 1].code;
}

export const codeCount = async (request: APIRequestContext) => (await harness<unknown[]>(request, "codes")).length;

type Cookies = Awaited<ReturnType<BrowserContext["cookies"]>>;
const sessions = new Map<string, Cookies>();

/**
 * Sign in as a phone would, without the screens (password, then the texted code), through the
 * page's own request context so the session cookie lands in the browser. The sign-in screens
 * themselves are covered by 01-sign-in. A person stays signed in between tests, as on a phone:
 * seal_common allows only a few codes an hour to one number, so each signs in once a run.
 */
export async function signIn(page: Page, user: string, password: string) {
	// This worker's own copy first, then the harness's (a worker started after a failure has none of
	// its own and must not spend another code).
	const held = sessions.get(user) ?? (await harness<{ cookies: Cookies }>(page.request, `session?user=${encodeURIComponent(user)}`)).cookies;
	if (held.length) {
		await page.context().addCookies(held);
		const boot = await page.request.get("/api/method/seal_desk.api.phone.boot");
		if (boot.ok() && (await boot.json()).message?.user?.name === user) {
			sessions.set(user, held);
			return;
		}
	}
	await signInNow(page, user, password);
	const cookies = await page.context().cookies();
	sessions.set(user, cookies);
	await harness(page.request, "session", { user, cookies });
}

async function signInNow(page: Page, user: string, password: string) {
	const before = await codeCount(page.request);
	const start = await page.request.post("/api/method/seal_common.api.v1.sign_in.start", { data: { login: user, password } });
	expect(start.ok(), await start.text()).toBeTruthy();
	const started = (await start.json()).message;
	if (started.next === "code") {
		const code = await latestCode(page.request, before);
		const finish = await page.request.post("/api/method/seal_common.api.v1.sign_in.finish", { data: { ticket: started.ticket, code } });
		expect(finish.ok(), await finish.text()).toBeTruthy();
	}
}

/** Collect Content Security Policy violations the page reports, from the first script on. */
export async function watchPolicy(page: Page): Promise<() => Promise<string[]>> {
	await page.addInitScript(() => {
		(window as unknown as { __cspViolations: string[] }).__cspViolations = [];
		document.addEventListener("securitypolicyviolation", (e) =>
			(window as unknown as { __cspViolations: string[] }).__cspViolations.push(`${e.violatedDirective} ${e.blockedURI} ${e.sample}`),
		);
	});
	return () => page.evaluate(() => (window as unknown as { __cspViolations?: string[] }).__cspViolations ?? []);
}

/** Uncaught errors on the page, for an assertion at the end of a test. */
export function watchErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
	return errors;
}

/** The page is no wider than the phone. */
export async function expectNoSidewaysScroll(page: Page) {
	const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
	expect(over, "the page is wider than the phone").toBeLessThanOrEqual(1);
}

/** The tab bar's buttons; Approvals' text carries the count. */
export const tab = (page: Page, name: RegExp) => page.getByRole("navigation", { name: "Main" }).getByRole("button", { name });

/** The tab bar's Approvals button, whose text carries the count. */
export const approvalsTab = (page: Page) => page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: /Approvals/ });
