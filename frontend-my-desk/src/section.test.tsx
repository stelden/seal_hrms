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
const errors: Record<string, unknown> = {};
const reloads: Record<string, ReturnType<typeof vi.fn>> = {};
const posts: Record<string, ReturnType<typeof vi.fn>> = {};

vi.mock("@stelden/seal-frontend", async (original) => {
	const real = await original<typeof import("@stelden/seal-frontend")>();
	return {
		...real,
		useGet: (method: string) => {
			reloads[method] ??= vi.fn();
			return { data: answers[method], error: errors[method], errorMessage: undefined, isLoading: false, isValidating: false, hasLoaded: true, mutate: reloads[method] };
		},
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
	for (const key of Object.keys(errors)) delete errors[key];
	for (const key of Object.keys(reloads)) delete reloads[key];
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

describe("Self Service home", () => {
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

describe("who will approve, before anything is sent (Keith, 2026-11-11)", () => {
	it("says the leave approver will approve it, never that it is approved", () => {
		answers[M.leaveOptions] = { leave_types: [{ name: "Annual Leave", left: 14, allocated: 21 }], approver_name: "Achieng Odhiambo", days: 7, handover: { needed: false, required: false, rule: null }, work: [], approvals: [] };
		// The choices come back as a kept draft (the select is not a native one to type into).
		const value = { leave_type: "Annual Leave", from_date: "2026-12-01", to_date: "2026-12-09", half_day: false, description: "", stand_in: "", handover_notes: "", todos: [], approvals: [] };
		window.localStorage.setItem(`seal-draft:${OTIENO}:leave-application:new`, JSON.stringify({ saved: Date.now(), value }));
		draw("leave/new", shell());
		return waitFor(() => {
			expect(screen.getByText("7 days. Achieng Odhiambo will approve it.")).toBeTruthy();
			expect(screen.queryByText(/approved by/i)).toBeNull();
		});
	});

	it("says the same on an expense claim, and what to do when nobody approves", () => {
		answers[M.expenseOptions] = { types: [{ name: "Travel", description: null }], currency: "KES", approver_name: "Achieng Odhiambo" };
		const first = draw("expenses/new", shell());
		expect(screen.getByText("Achieng Odhiambo will approve it.")).toBeTruthy();
		first.unmount();
		answers[M.expenseOptions] = { types: [], currency: "KES", approver_name: null };
		draw("expenses/new", shell());
		expect(screen.getByText("Nobody approves this yet. Ask HR to set your approver.")).toBeTruthy();
	});
});

describe("screens that ask who is holding the phone", () => {
	it("asks once on arrival when the server refuses payslips, then reads them again", async () => {
		errors[M.payslips] = { exc_type: "VerificationNeeded" };
		const api = shell();
		draw("pay", api);
		expect(screen.getByText("Confirm It Is You")).toBeTruthy();
		await waitFor(() => expect(api.verify).toHaveBeenCalledTimes(1));
		await waitFor(() => expect(reloads[M.payslips]).toHaveBeenCalled());
	});

	it("reads nothing again when the person closes the check, and offers Confirm", async () => {
		errors[M.payslips] = { exc_type: "VerificationNeeded" };
		const api = shell({ verify: vi.fn().mockResolvedValue(false) });
		draw("pay", api);
		await waitFor(() => expect(api.verify).toHaveBeenCalledTimes(1));
		expect(reloads[M.payslips]).not.toHaveBeenCalled();
		fireEvent.click(screen.getByText("Confirm"));
		await waitFor(() => expect(api.verify).toHaveBeenCalledTimes(2));
	});

	it("holds back where pay goes on My Details until the person confirms", async () => {
		answers[M.myDetails] = {
			employee: { name: "HR-EMP-00031", employee_name: "Otieno Ochieng", designation: null, department: null, company: "Kilimani Community Trust", date_of_joining: null, company_email: null, personal_email: null },
			mobile_no: "•••• 5678",
			has_contact: true,
			dependants: [],
			payout_locked: true,
			payout: null,
			payout_request: null,
			payout_requests: [],
		};
		const api = shell();
		draw("me", api);
		expect(screen.getByText("Your payout details show once you confirm it is you.")).toBeTruthy();
		expect(api.verify).not.toHaveBeenCalled(); // not asked on arrival: most visits are not about pay
		fireEvent.click(screen.getByText("Confirm"));
		await waitFor(() => expect(reloads[M.myDetails]).toHaveBeenCalled());
	});

	it("confirms before opening a payslip's PDF in the browser", async () => {
		answers[M.payslipRecord] = { name: "Sal Slip/HR-EMP-00031/00010", employee_name: "Otieno Ochieng", start_date: "2026-10-01", end_date: "2026-10-31", posting_date: "2026-10-31", currency: "KES", gross_pay: 85000, total_deduction: 21000, net_pay: 64000, earnings: [], deductions: [], print_format: "Standard" };
		posts[M.confirmScreen] = vi.fn().mockRejectedValueOnce({ exc_type: "VerificationNeeded" }).mockResolvedValueOnce({ ok: true });
		const opened = vi.spyOn(window, "open").mockReturnValue({ opener: {} } as Window);
		const api = shell();
		draw("pay/Sal%20Slip%2FHR-EMP-00031%2F00010", api);
		fireEvent.click(screen.getByText("Open Payslip"));
		await waitFor(() => expect(opened).toHaveBeenCalled());
		expect(api.verify).toHaveBeenCalledTimes(1);
		expect(posts[M.confirmScreen]).toHaveBeenCalledWith({ screen: "payslips" });
		expect(String(opened.mock.calls[0][0])).toContain("payslip_pdf");
		opened.mockRestore();
	});
});

describe("travel requests", () => {
	beforeEach(() => {
		answers[M.travelOptions] = { purposes: ["Field Visit"], expense_types: ["Travel", "Accommodation"], travel_types: ["Domestic", "International"], funding: ["Require Full Funding"], modes: ["Flight", "Train", "Taxi", "Rented Car"], currency: "KES", approver_name: "Achieng Odhiambo" };
	});

	it("lists the person's requests with where they go and where they are", () => {
		answers[M.travelList] = [{ name: "HR-TRQ-2026-00003", purpose_of_travel: "Field Visit", travel_type: "Domestic", state: "Pending Approval", creation: "2026-11-10 09:00:00", travel_from: "Nairobi", travel_to: "Kisumu", departure_date: "2026-11-20 07:30:00" }];
		draw("travel", shell());
		expect(screen.getByText("Nairobi to Kisumu")).toBeTruthy();
		expect(screen.getByText("Pending Approval")).toBeTruthy();
	});

	it("names the line manager who will approve, and sends the journeys and costs typed", async () => {
		posts[M.requestTravel] = vi.fn().mockResolvedValue({ name: "HR-TRQ-2026-00004", state: "Pending Approval" });
		const api = shell();
		// The selects come back as a kept draft (they are not native ones to type into); the places are typed.
		const value = { travel_type: "Domestic", purpose_of_travel: "Field Visit", travel_funding: "", description: "", itinerary: [{ travel_from: "", travel_to: "", mode_of_travel: "", departure_date: "", arrival_date: "", lodging_required: false }], costings: [] };
		window.localStorage.setItem(`seal-draft:${OTIENO}:travel-request:new`, JSON.stringify({ saved: Date.now(), value }));
		draw("travel/new", api);
		expect(screen.getByText("Achieng Odhiambo will approve it.")).toBeTruthy();
		fireEvent.change(screen.getByLabelText(/^From/), { target: { value: "Nairobi" } });
		fireEvent.change(screen.getByLabelText(/^To/), { target: { value: "Kisumu" } });
		fireEvent.click(screen.getByText("Send for Approval"));
		await waitFor(() => expect(posts[M.requestTravel]).toHaveBeenCalled());
		const sent = posts[M.requestTravel].mock.calls[0][0];
		expect(sent.send).toBe(1);
		expect(sent.employee).toBeUndefined(); // the server takes the person's own record and company
		expect(sent.company).toBeUndefined();
		expect(JSON.parse(sent.itinerary)).toEqual([expect.objectContaining({ travel_from: "Nairobi", travel_to: "Kisumu" })]);
		expect(JSON.parse(sent.costings)).toEqual([]);
		await waitFor(() => expect(api.navigate).toHaveBeenCalledWith("travel/HR-TRQ-2026-00004"));
	});

	it("offers a draft's owner Send for Approval, and a manager only the way to Approvals", () => {
		answers[M.travelRecord] = { name: "HR-TRQ-2026-00004", employee_name: "Otieno Ochieng", state: "Draft", docstatus: 0, travel_type: "Domestic", purpose_of_travel: "Field Visit", travel_funding: null, description: null, currency: "KES", approver_name: "Achieng Odhiambo", itinerary: [{ travel_from: "Nairobi", travel_to: "Kisumu", mode_of_travel: "Flight", departure_date: "2026-11-20 07:30:00", arrival_date: "", lodging_required: true }], costings: [{ expense_type: "Accommodation", total_amount: 12000, comments: null }], mine: true, can_send: true };
		const first = draw("travel/HR-TRQ-2026-00004", shell());
		expect(screen.getByText("Send for Approval")).toBeTruthy();
		expect(screen.getByText("Accommodation")).toBeTruthy();
		first.unmount();
		answers[M.travelRecord] = { ...(answers[M.travelRecord] as object), state: "Pending Approval", mine: false, can_send: false };
		draw("travel/HR-TRQ-2026-00004", shell());
		expect(screen.queryByText("Send for Approval")).toBeNull();
		expect(screen.getByText("Decide this request from Approvals.")).toBeTruthy();
	});
});
