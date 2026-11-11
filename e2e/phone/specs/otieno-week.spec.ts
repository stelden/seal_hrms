// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * THE P5/P6 DONE-WHEN (seal_desk pwa/DESIGN.md §7): "Otieno does a week of self service on a phone;
 * Achieng approves it." In the real My Desk shell (seal_desk), at 390×844, with the Self Service section
 * (seal_hrms) loaded at run time:
 *
 *   Otieno Ochieng applies for leave with Njeri Mwangi covering, claims time off for a Saturday's
 *   work, fills and sends last week's timesheet (closing the app half-way: the week comes back from
 *   the phone), claims an expense, opens last month's payslip, checks in, and asks for his pay to go
 *   to a new mobile money number, confirming it is him.
 *   Achieng Odhiambo, his approver, approves the leave, the timesheet and the expense claim from the
 *   Approvals tab (the expense with a fresh check).
 *
 * Every step is checked in the database through the harness (`/__harness/state`), not only on screen.
 * The harness rolls everything back when it stops.
 */

import { expect, test, type Page } from "@playwright/test";

import { approvalsTab, expectNoSidewaysScroll, harness, seeded, signIn, state, watchErrors, type Seeded } from "../fixtures";

const SHOTS = "artifacts/otieno-week";
const MY_HR = "/my-desk/apps/my-hr";

/** dd-mm-yyyy, the site's date format, `days` from today on the phone's calendar. */
function siteDate(days: number): string {
	const d = new Date();
	d.setDate(d.getDate() + days);
	return `${String(d.getDate()).padStart(2, "0")}-${String(d.getMonth() + 1).padStart(2, "0")}-${d.getFullYear()}`;
}

/** A Base UI select: open it by its label, pick the option. */
async function choose(page: Page, label: string | RegExp, option: string) {
	await page.getByRole("combobox", { name: label }).click();
	await page.getByRole("option", { name: option }).click();
}

const shot = (page: Page, name: string) => page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: true });

test.describe.configure({ mode: "serial" });

let who: Seeded;

test("Otieno does a week of self service on his phone", async ({ page }) => {
	const errors = watchErrors(page);
	who = await seeded(page.request);
	await signIn(page, who.otieno_user, who.password);

	await test.step("Self Service opens from the Apps tab, in the shell", async () => {
		await page.goto("/my-desk/apps");
		await expect(page.getByRole("heading", { name: "Self Service" }).first()).toBeVisible();
		await expect(page.getByText(who.otieno_name).first()).toBeVisible();
		await expectNoSidewaysScroll(page);
		await shot(page, "01-my-hr");
	});

	await test.step("applies for leave with Njeri covering", async () => {
		await page.getByRole("button", { name: "Apply for Leave" }).first().click();
		await expect(page.getByRole("heading", { name: "Apply for Leave" }).first()).toBeVisible();
		await choose(page, "Leave Type", who.leave_type);
		await page.getByLabel("From Date").fill(siteDate(21));
		await page.getByLabel("To Date").fill(siteDate(22));
		await page.getByLabel("Reason").fill("My daughter's graduation in Kisumu");
		await page.getByLabel("Reason").blur();
		// One wording on every form (EM-11): who will approve it, not "approved by".
		await expect(page.getByText(/Achieng Odhiambo will approve it\./)).toBeVisible();
		// The company suggests cover for leave this long: the handover shows beneath the leave.
		await expect(page.getByText("Your company suggests arranging cover. You can leave this out.")).toBeVisible();
		await page.getByRole("combobox", { name: "Stand-in" }).click();
		await page.getByRole("option", { name: who.njeri_name }).click();
		await page.getByLabel("Handover Notes").fill("The Mathare youth workshop report is due on Friday; the draft is in the shared folder.");
		await shot(page, "02-leave-handover");
		await page.getByRole("button", { name: "Apply" }).click();
		await expect(page.getByText("Leave applied for, and the handover sent to your stand-in.")).toBeVisible();
		await expect.poll(async () => (await state(page.request)).leave.length).toBe(1);
		const now = await state(page.request);
		expect(now.leave[0]).toMatchObject({ leave_type: who.leave_type, status: "Open", docstatus: 0 });
		expect(now.handovers.length).toBe(1);
		await expectNoSidewaysScroll(page);
		await shot(page, "03-leave-applied");
	});

	await test.step("claims time off in lieu for Saturday's work and sends it", async () => {
		await page.goto(`${MY_HR}/toil/new`);
		await expect(page.getByRole("heading", { name: "Claim Time Off" }).first()).toBeVisible();
		const [y, m, d] = who.rest_day.split("-");
		await page.getByLabel("Date").first().fill(`${d}-${m}-${y}`);
		await page.getByLabel("Hours Worked").first().fill("4");
		await page.getByLabel("Work Done").first().fill("Community health drive in Kibera, Saturday morning");
		await page.getByRole("button", { name: "Save Claim" }).click();
		await expect(page.getByRole("heading", { name: "Time Off in Lieu Claim" }).first()).toBeVisible();
		await page.getByRole("button", { name: /^Send for (Approval|Authorisation)$/ }).click();
		await expect(page.getByText("Claim sent.")).toBeVisible();
		await expect.poll(async () => (await state(page.request)).toil[0]?.status).toMatch(/^Waiting for/);
		await shot(page, "04-toil-sent");
	});

	await test.step("fills last week's timesheet, closes the app, and finds the week kept on the phone", async () => {
		await page.goto(`${MY_HR}/timesheet/week/${who.last_monday}`);
		await expect(page.getByText("Monday", { exact: true })).toBeVisible();
		await choose(page, "Activity Type", who.activity);
		await page.getByLabel("Description").fill("Household visits in Mathare North");
		await page.getByLabel("Hours on Monday").fill("8");
		const key = `seal-draft:${who.otieno_user}:timesheet-week:${who.last_monday}`;
		await expect.poll(() => page.evaluate((k) => localStorage.getItem(k), key)).toContain('"hours":[8,0,0,0,0,0,0]');
		// The app is closed before saving (a call, a flat battery): nothing reached the server.
		await page.goto("/my-desk");
		expect((await state(page.request)).timesheets.length).toBe(0);
		await page.goto(`${MY_HR}/timesheet/week/${who.last_monday}`);
		await expect(page.getByText("Restored From This Phone")).toBeVisible();
		await expect(page.getByLabel("Hours on Monday")).toHaveValue("8");
		await shot(page, "05-week-restored");
		for (const [day, hours] of [["Tuesday", "8"], ["Wednesday", "7.5"], ["Thursday", "8"], ["Friday", "6"]]) {
			await page.getByRole("button", { name: "Next Day" }).click();
			await page.getByLabel(`Hours on ${day}`).fill(hours);
		}
		await page.getByRole("button", { name: "Send for Approval" }).click();
		await expect(page.getByText("Week sent for approval.")).toBeVisible();
		await expect.poll(async () => (await state(page.request)).timesheets[0]?.custom_approval_state).toBe("Waiting for Approval");
		expect((await state(page.request)).timesheets[0].total_hours).toBe(37.5);
		expect(await page.evaluate((k) => localStorage.getItem(k), key)).toBeNull();
		await expectNoSidewaysScroll(page);
		await shot(page, "06-week-sent");
	});

	await test.step("claims an expense", async () => {
		await page.goto(`${MY_HR}/expenses/new`);
		await expect(page.getByRole("heading", { name: "New Expense Claim" }).first()).toBeVisible();
		await choose(page, "Expense Type", who.expense_type);
		await page.getByLabel(/^Amount/).fill("1450");
		await page.getByLabel("Description").fill("Matatu fares to the Kibera outreach");
		await page.getByRole("button", { name: "Send Claim" }).click();
		await expect(page.getByText("Claim sent to Achieng Odhiambo.")).toBeVisible();
		await expect.poll(async () => (await state(page.request)).expenses[0]?.total_claimed_amount).toBe(1450);
		expect(await page.evaluate((u) => localStorage.getItem(`seal-draft:${u}:expense-claim:new`), who.otieno_user)).toBeNull();
		await shot(page, "07-expense-sent");
	});

	await test.step("opens last month's payslip", async () => {
		await page.goto(`${MY_HR}/pay`);
		await page.getByText(/^Net pay/).first().click();
		await expect(page.getByText(who.otieno_name).first()).toBeVisible();
		await expect(page.getByText("Kilimani Basic Pay").first()).toBeVisible();
		// Open Payslip confirms it is him (fresh from signing in: not asked) and opens the PDF in the
		// browser. The PDF itself is answered here, not by the site: the site renders it by asking
		// itself for the page's styles, and this one-connection harness would wait on itself.
		await page.context().route("**/api/method/seal_hrms.my_desk.api.payslip_pdf**", (route) =>
			route.fulfill({ status: 200, contentType: "application/pdf", body: "%PDF-1.4 stand-in" }),
		);
		// A PDF answer is a download in headless Chrome, so the new tab's address is read from its request.
		const asked = page.context().waitForEvent("request", (r) => r.url().includes("seal_hrms.my_desk.api.payslip_pdf"));
		await page.getByRole("button", { name: "Open Payslip" }).click();
		expect(new URL((await asked).url()).searchParams.get("name")).toBe(who.payslip);
		for (const extra of page.context().pages()) if (extra !== page) await extra.close();
		await expect(page.getByRole("dialog")).toHaveCount(0);
		await expectNoSidewaysScroll(page);
		await shot(page, "08-payslip");
	});

	await test.step("checks in", async () => {
		await page.goto(`${MY_HR}/check-in`);
		await page.getByRole("button", { name: "Check In" }).click();
		await expect(page.getByText("Checked in.")).toBeVisible();
		await expect.poll(async () => (await state(page.request)).checkins.map((c) => c.log_type)).toEqual(["IN"]);
		await expect(page.getByRole("button", { name: "Check Out" })).toBeVisible();
		await shot(page, "09-checked-in");
	});

	await test.step("asks for his pay to go to a new mobile money number, confirming it is him", async () => {
		// Minutes have passed since he signed in: the server wants a fresh check before this goes.
		await harness(page.request, "stale", {});
		await page.goto(`${MY_HR}/me/payout/new`);
		await page.getByRole("radio", { name: "Mobile Money" }).click();
		await page.getByLabel("Mobile No.").fill("0722418306");
		await page.getByLabel("Reason").fill("Moving my pay to M-PESA");
		await page.getByRole("button", { name: "Send to HR" }).click();
		const dialog = page.getByRole("dialog");
		await expect(dialog.getByText("Confirm It Is You")).toBeVisible();
		await dialog.getByLabel("Password").fill(who.password);
		await dialog.getByRole("button", { name: "Confirm" }).click();
		await expect(page.getByText("Sent to HR. Nothing changes until HR confirms it.")).toBeVisible();
		await expect.poll(async () => (await state(page.request)).payout[0]?.status).toBe("Waiting for HR");
		await shot(page, "10-payout-sent");
	});

	expect(errors).toEqual([]);
});

test("Achieng approves his leave and expense claim from the Approvals tab", async ({ page }) => {
	const errors = watchErrors(page);
	who ??= await seeded(page.request);
	await signIn(page, who.achieng_user, who.password);
	await page.goto("/my-desk/approvals");
	await expect(page.getByRole("heading", { name: "Approvals" }).first()).toBeVisible();
	const card = (text: RegExp) => page.locator("[data-slot=card]").filter({ hasText: text });
	await expect(card(/Leave for Otieno Ochieng/)).toBeVisible();
	await expect(card(/Expense claim from Otieno Ochieng/)).toBeVisible();
	await expect(card(/Time off claim from Otieno Ochieng/)).toBeVisible();
	await expect(card(/Timesheet from Otieno Ochieng/)).toBeVisible(); // read by a share (seal_desk 1.22.1, D191)
	await expect(approvalsTab(page)).toContainText("4");
	await expectNoSidewaysScroll(page);
	await shot(page, "11-approvals");

	await test.step("approves the leave", async () => {
		await card(/Leave for Otieno Ochieng/).getByRole("button", { name: "Approve" }).click();
		await expect(card(/Leave for Otieno Ochieng/)).toHaveCount(0);
		await expect.poll(async () => (await state(page.request)).leave[0]).toMatchObject({ status: "Approved", docstatus: 1 });
	});

	await test.step("approves the expense claim, confirming it is her", async () => {
		await harness(page.request, "stale", {}); // money leaves the company: a fresh check, not the sign-in's
		await card(/Expense claim from Otieno Ochieng/).getByRole("button", { name: "Approve" }).click();
		const dialog = page.getByRole("dialog");
		await expect(dialog.getByText("Confirm It Is You")).toBeVisible();
		await dialog.getByLabel("Password").fill(who.password);
		await dialog.getByRole("button", { name: "Confirm" }).click();
		await expect(card(/Expense claim from Otieno Ochieng/)).toHaveCount(0);
		await expect.poll(async () => (await state(page.request)).expenses[0]?.approval_status).toBe("Approved");
	});
	await expect(approvalsTab(page)).toContainText("2"); // the time off claim and the timesheet are still hers to decide
	await shot(page, "12-approved");
	expect(errors).toEqual([]);
});

/**
 * The timesheet reaches Achieng's Approvals tab although she reads it only through a share, by
 * design (`timesheets/approval.py`): seal_desk 1.22.1 checks read per document, not by role (D191).
 * Marked as a known failure until then.
 */
test("Achieng approves his timesheet from the Approvals tab", async ({ page }) => {
	who ??= await seeded(page.request);
	await signIn(page, who.achieng_user, who.password);
	const raw = (await (await page.request.get("/api/method/seal_desk.api.phone.approvals")).json()).message;
	expect(raw.failed).toEqual([]);
	expect(raw.items.map((i: { doctype: string }) => i.doctype)).toContain("Timesheet");
	await page.goto("/my-desk/approvals");
	const card = page.locator("[data-slot=card]").filter({ hasText: /Timesheet from Otieno Ochieng/ });
	await expect(card).toBeVisible({ timeout: 10_000 });
	await card.getByRole("button", { name: "Approve" }).click();
	await expect.poll(async () => (await state(page.request)).timesheets[0]).toMatchObject({ custom_approval_state: "Approved", docstatus: 1 });
});

test("the HR notices of the week: their kind on the phone, and nothing about pay on a locked screen", async ({ page }) => {
	who ??= await seeded(page.request);
	const answers = await harness<{ for_user: string; doctype: string; subject: string; kind: string | null; body: string }[]>(page.request, "push");
	const about = (user: string, doctype: string) => answers.filter((a) => a.for_user === user && a.doctype === doctype);
	// Njeri is asked to cover: an HR notice, which she may turn off.
	expect(about(who.njeri_user, "Task Assignment").map((a) => a.kind)).toEqual(["hr"]);
	// Achieng is asked to decide: approvals (seal_desk's kind), never "hr".
	expect(about(who.achieng_user, "Time Off in Lieu Claim").map((a) => a.kind)).toEqual([null]);
	// Kinds are worked out now, at the end of the week: she approved the timesheet above, so it no
	// longer waits on her and reads as an HR notice (null while it waited, as the time off claim still does).
	expect(about(who.achieng_user, "Timesheet").map((a) => a.kind)).toEqual(["hr"]);
	// HR is asked to confirm the payout change: theirs to decide, and only the subject would show.
	const payout = answers.filter((a) => a.doctype === "Payout Change Request");
	expect(payout.length).toBeGreaterThan(0);
	for (const a of payout) {
		expect(a.kind).toBeNull();
		expect(a.body).toBe(a.subject);
		expect(a.body).not.toMatch(/0722|8306|M-PESA/);
	}
});
