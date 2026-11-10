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
afterEach(cleanup);

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
});
