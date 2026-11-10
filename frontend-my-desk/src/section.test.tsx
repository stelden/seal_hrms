// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * The section drawn as the shell draws it: inside a ShellProvider and the shell's router. The data hooks
 * are replaced by fixtures keyed by method (Otieno Ochieng's), so these tests are about the screens, not
 * the server (tests/test_my_desk_section.py covers that).
 */

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ShellProvider, isSectionDefinition, type ShellApi } from "@stelden/seal-frontend/section";
import { SealProvider } from "@stelden/seal-frontend/ui";

const answers: Record<string, unknown> = {};
const posts: Record<string, ReturnType<typeof vi.fn>> = {};

vi.mock("@stelden/seal-frontend", async (original) => {
	const real = await original<typeof import("@stelden/seal-frontend")>();
	return {
		...real,
		useGet: (method: string) => ({ data: answers[method], error: undefined, errorMessage: undefined, isLoading: false, isValidating: false, hasLoaded: true, mutate: vi.fn() }),
		usePost: (method: string) => {
			posts[method] ??= vi.fn().mockResolvedValue(undefined);
			return { run: posts[method], loading: false, error: undefined, errorMessage: undefined, isCompleted: false, reset: vi.fn() };
		},
	};
});

const { default: section } = await import("./section");
const { M } = await import("./lib/api");

function shell(overrides: Partial<ShellApi> = {}): ShellApi {
	return { user: "otieno.ochieng@kilimani-office.co.ke", company: "Kilimani Community Trust", navigate: vi.fn(), openRecord: vi.fn(), openList: vi.fn(), verify: vi.fn().mockResolvedValue(true), extra: {}, ...overrides };
}

function draw(path: string, api: ShellApi) {
	const Home = section.home;
	return render(
		<SealProvider>
			<ShellProvider value={api}>
				<MemoryRouter initialEntries={[`/my-desk/apps/my-hr/${path}`]}>
					<Routes>
						<Route path="/my-desk/apps/my-hr" element={<Home />} />
						{section.routes.map((r) => (
							<Route key={r.path} path={`/my-desk/apps/my-hr/${r.path}`} element={r.element} />
						))}
					</Routes>
				</MemoryRouter>
			</ShellProvider>
		</SealProvider>,
	);
}

beforeEach(() => {
	for (const key of Object.keys(answers)) delete answers[key];
	for (const key of Object.keys(posts)) delete posts[key];
});
afterEach(() => {
	cleanup();
	window.localStorage.clear();
});

const OTIENO = "otieno.ochieng@kilimani-office.co.ke";

describe("the section", () => {
	it("is a checked definition the shell accepts", () => {
		expect(isSectionDefinition(section)).toBe(true);
		expect(section.key).toBe("seal_hrms.my_hr");
		expect(section.records["Leave Application"].create).toBe("leave/new");
	});
});

describe("My HR home", () => {
	beforeEach(() => {
		answers[M.home] = {
			employee: { name: "HR-EMP-00031", employee_name: "Otieno Ochieng", company: "Kilimani Community Trust" },
			balances: [{ key: "leave_left:Annual Leave", label: "Annual Leave left", value: 14 }],
			in_flight: [{ key: "claims_in_approval", label: "Claims in approval", count: 2, doctype: "Expense Claim" }],
			checkin: { offered: true, location: false },
		};
	});

	it("shows balances, what is in flight and every area", () => {
		draw("", shell());
		expect(screen.getByText("Otieno Ochieng")).toBeTruthy();
		expect(screen.getByText("Annual Leave left")).toBeTruthy();
		expect(screen.getByText("14 days")).toBeTruthy();
		expect(screen.getByText("Claims in approval")).toBeTruthy();
		for (const area of ["Leave", "Cover", "Time Off in Lieu", "Timesheets", "Expense Claims", "Advances", "Payslips", "Check-in", "My Details"]) {
			expect(screen.getAllByText(area).length).toBeGreaterThan(0);
		}
	});

	it("opens screens through the shell, relative to the section", () => {
		const api = shell();
		draw("", api);
		fireEvent.click(screen.getByText("Apply for Leave"));
		expect(api.navigate).toHaveBeenCalledWith("leave/new");
		fireEvent.click(screen.getByText("Claims in approval"));
		expect(api.navigate).toHaveBeenCalledWith("expenses");
	});
});

describe("a payout change request", () => {
	beforeEach(() => {
		answers[M.payoutRequestRecord] = { name: "PCR-2026-00004", status: "Draft", change: "Bank Account", bank: "Kilimani Cooperative Bank", account_no: "•••• 6311", account_name: "Otieno Ochieng", mobile_no: null, has_evidence: true, mine: true };
	});

	it("asks the person to confirm it is them when the server wants it, then sends", async () => {
		const api = shell();
		posts[M.sendPayoutChange] = vi.fn().mockRejectedValueOnce({ exc_type: "VerificationNeeded" }).mockResolvedValueOnce("Waiting for HR");
		draw("me/payout/PCR-2026-00004", api);
		expect(screen.getByText("•••• 6311")).toBeTruthy();
		fireEvent.click(screen.getByText("Send to HR"));
		await waitFor(() => expect(posts[M.sendPayoutChange]).toHaveBeenCalledTimes(2));
		expect(api.verify).toHaveBeenCalledTimes(1);
	});

	it("sends nothing more when the person cancels the check", async () => {
		const api = shell({ verify: vi.fn().mockResolvedValue(false) });
		posts[M.sendPayoutChange] = vi.fn().mockRejectedValue({ exc_type: "VerificationNeeded" });
		draw("me/payout/PCR-2026-00004", api);
		fireEvent.click(screen.getByText("Send to HR"));
		await waitFor(() => expect(api.verify).toHaveBeenCalled());
		expect(posts[M.sendPayoutChange]).toHaveBeenCalledTimes(1);
	});
});

describe("the timesheet week", () => {
	beforeEach(() => {
		answers[M.timesheetWeek] = {
			weekly: true,
			checks: ["03-11-2026: 6 of 8 hours accounted for."],
			week_start: "2026-11-02",
			hours_per_day: 8,
			default_activity_type: "Community Outreach",
			days: ["02", "03", "04", "05", "06", "07", "08"].map((d, i) => ({ date: `2026-11-${d}`, kind: i > 4 ? "Rest day" : "Working day", leave: null, leave_fraction: 0, attendance_hours: i === 0 ? 7.5 : null })),
			previous_entries: [{ row: 1, activity_type: "Training", description: "First aid course", hours: [8, 0, 0, 0, 0, 0, 0] }],
			activity_types: ["Community Outreach", "Training"],
			approval: true,
			timesheet: null,
		};
	});

	it("copies last week's lines and sends the week with the hours entered", async () => {
		posts[M.saveTimesheetWeek] = vi.fn().mockResolvedValue({ name: "TS-2026-00012", state: "Waiting for Approval" });
		// A past week opens on its Monday (the current week opens on today).
		draw("timesheet/week/2026-11-02", shell());
		expect(screen.getByText("Monday")).toBeTruthy();
		expect(screen.getByText("03-11-2026: 6 of 8 hours accounted for.")).toBeTruthy();
		fireEvent.click(screen.getByText("Copy Last Week"));
		fireEvent.change(screen.getByLabelText("Hours on Monday"), { target: { value: "7.5" } });
		fireEvent.click(screen.getByText("Send for Approval"));
		await waitFor(() => expect(posts[M.saveTimesheetWeek]).toHaveBeenCalled());
		const sent = posts[M.saveTimesheetWeek].mock.calls[0][0];
		expect(sent.send).toBe(1);
		expect(JSON.parse(sent.entries)).toEqual([{ row: 1, activity_type: "Training", project: null, task: null, description: "First aid course", is_billable: 0, hours: [7.5, 0, 0, 0, 0, 0, 0] }]);
	});

	it("keeps the week on the phone as it is typed, restores it, and forgets it once sent", async () => {
		const key = `seal-draft:${OTIENO}:timesheet-week:2026-11-02`;
		const first = draw("timesheet/week/2026-11-02", shell());
		fireEvent.click(screen.getByText("Copy Last Week"));
		fireEvent.change(screen.getByLabelText("Hours on Monday"), { target: { value: "6" } });
		await waitFor(() => expect(window.localStorage.getItem(key)).toContain('"hours":[6,0,0,0,0,0,0]'));
		first.unmount();

		// The app was closed before saving; opening the week again brings the hours back.
		posts[M.saveTimesheetWeek] = vi.fn().mockResolvedValue({ name: "TS-2026-00012", state: "Waiting for Approval" });
		draw("timesheet/week/2026-11-02", shell());
		expect(screen.getByText("Restored From This Phone")).toBeTruthy();
		expect((screen.getByLabelText("Hours on Monday") as HTMLInputElement).value).toBe("6");
		fireEvent.click(screen.getByText("Send for Approval"));
		await waitFor(() => expect(posts[M.saveTimesheetWeek]).toHaveBeenCalled());
		expect(JSON.parse(posts[M.saveTimesheetWeek].mock.calls[0][0].entries)[0].hours).toEqual([6, 0, 0, 0, 0, 0, 0]);
		await waitFor(() => expect(window.localStorage.getItem(key)).toBeNull());
	});

	it("drops a kept week the server no longer lets the person change", () => {
		const key = `seal-draft:${OTIENO}:timesheet-week:2026-11-02`;
		window.localStorage.setItem(key, JSON.stringify({ saved: Date.now(), value: [{ row: 1, activity_type: "Training", description: "", hours: [3, 0, 0, 0, 0, 0, 0] }] }));
		answers[M.timesheetWeek] = {
			...(answers[M.timesheetWeek] as object),
			timesheet: { name: "TS-2026-00012", docstatus: 0, state: "Waiting for Approval", return_reason: null, approver_name: "Achieng Wanjiru", entries: [{ row: 1, activity_type: "Training", description: "", hours: [8, 0, 0, 0, 0, 0, 0] }], total_hours: 8, can_edit: false, can_send: false, can_claim: false },
		};
		draw("timesheet/week/2026-11-02", shell());
		expect(screen.queryByText("Restored From This Phone")).toBeNull();
		expect((screen.getByLabelText("Hours on Monday") as HTMLInputElement).value).toBe("8");
		expect(window.localStorage.getItem(key)).toBeNull();
	});
});

describe("drafts of the other long forms", () => {
	beforeEach(() => {
		answers[M.expenseOptions] = { types: [{ name: "Travel", description: null }], currency: "KES", approver_name: "Achieng Wanjiru" };
		answers[M.leaveOptions] = { leave_types: [{ name: "Annual Leave", left: 14, allocated: 21 }], approver_name: "Achieng Wanjiru", days: null, handover: { needed: false, required: false, rule: null }, work: [], approvals: [] };
	});

	it("an expense claim comes back as typed, and is forgotten once sent", async () => {
		const key = `seal-draft:${OTIENO}:expense-claim:new`;
		window.localStorage.setItem(
			key,
			JSON.stringify({ saved: Date.now(), value: { lines: [{ expense_date: "2026-11-09", expense_type: "Travel", amount: 1450, description: "Matatu to Kibera outreach" }], remark: "Field visit" } }),
		);
		posts[M.claimExpenses] = vi.fn().mockResolvedValue("HR-EXP-2026-00044");
		const api = shell();
		draw("expenses/new", api);
		expect(screen.getByText("Restored From This Phone")).toBeTruthy();
		expect(screen.getByDisplayValue("Matatu to Kibera outreach")).toBeTruthy();
		fireEvent.click(screen.getByText("Send Claim"));
		await waitFor(() => expect(posts[M.claimExpenses]).toHaveBeenCalled());
		expect(JSON.parse(posts[M.claimExpenses].mock.calls[0][0].lines)[0].amount).toBe(1450);
		await waitFor(() => expect(window.localStorage.getItem(key)).toBeNull());
	});

	it("a leave application is kept as it is typed and Start Again forgets it", async () => {
		const key = `seal-draft:${OTIENO}:leave-application:new`;
		const first = draw("leave/new", shell());
		fireEvent.change(screen.getByLabelText("Reason"), { target: { value: "Daughter's graduation in Kisumu" } });
		await waitFor(() => expect(window.localStorage.getItem(key)).toContain("graduation in Kisumu"));
		first.unmount();
		draw("leave/new", shell());
		expect(screen.getByDisplayValue("Daughter's graduation in Kisumu")).toBeTruthy();
		fireEvent.click(screen.getByText("Start Again"));
		expect(window.localStorage.getItem(key)).toBeNull();
		await waitFor(() => expect(screen.queryByDisplayValue("Daughter's graduation in Kisumu")).toBeNull());
	});
});
