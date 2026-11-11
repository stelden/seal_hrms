// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * The Self Service section of the My Desk phone app (HR_ON_MY_DESK §3; SECTIONS_CONTRACT §2): every self-service
 * screen, under /my-desk/apps/my-hr. The shell loads this module at run time and lends React, the router,
 * the SDK and the library; the hook `seal_desk_app_sections` (seal_hrms/hooks.py) points at its build.
 */

import "./section.css";

import { defineSection } from "@stelden/seal-frontend/section";

import { RECORDS } from "./lib/paths";
import { AttendanceForm, AttendanceList, CheckIn, RequestRecord, ShiftForm, ShiftList } from "./pages/Attendance";
import { CoverList, HandoverRecord } from "./pages/Cover";
import { MyHrHome } from "./pages/Home";
import { LeaveForm, LeaveList, LeaveRecord } from "./pages/Leave";
import { MyDetails, PayoutForm, PayoutRecord } from "./pages/Me";
import { AdvanceForm, AdvanceList, AdvanceRecord, ExpenseForm, ExpenseList, ExpenseRecord, PayList, PayRecord } from "./pages/Money";
import { TimesheetList, TimesheetRecord, TimesheetWeek } from "./pages/Timesheet";
import { ToilForm, ToilList, ToilRecord } from "./pages/Toil";
import { TravelForm, TravelList, TravelRecord } from "./pages/Travel";

export const ROUTES = [
	{ path: "leave", element: <LeaveList /> },
	{ path: "leave/new", element: <LeaveForm /> },
	{ path: "leave/:name", element: <LeaveRecord /> },
	{ path: "cover", element: <CoverList /> },
	{ path: "cover/:name", element: <HandoverRecord /> },
	{ path: "toil", element: <ToilList /> },
	{ path: "toil/new", element: <ToilForm /> },
	{ path: "toil/:name", element: <ToilRecord /> },
	{ path: "timesheet", element: <TimesheetList /> },
	{ path: "timesheet/week/:week", element: <TimesheetWeek /> },
	{ path: "timesheet/:name", element: <TimesheetRecord /> },
	{ path: "expenses", element: <ExpenseList /> },
	{ path: "expenses/new", element: <ExpenseForm /> },
	{ path: "expenses/:name", element: <ExpenseRecord /> },
	{ path: "advances", element: <AdvanceList /> },
	{ path: "advances/new", element: <AdvanceForm /> },
	{ path: "advances/:name", element: <AdvanceRecord /> },
	{ path: "pay", element: <PayList /> },
	{ path: "pay/:name", element: <PayRecord /> },
	{ path: "check-in", element: <CheckIn /> },
	{ path: "attendance", element: <AttendanceList /> },
	{ path: "attendance/new", element: <AttendanceForm /> },
	{ path: "attendance/:name", element: <RequestRecord doctype="Attendance Request" /> },
	{ path: "shifts", element: <ShiftList /> },
	{ path: "shifts/new", element: <ShiftForm /> },
	{ path: "shifts/:name", element: <RequestRecord doctype="Shift Request" /> },
	{ path: "me", element: <MyDetails /> },
	{ path: "me/payout/new", element: <PayoutForm /> },
	{ path: "me/payout/:name", element: <PayoutRecord /> },
	{ path: "travel", element: <TravelList /> },
	{ path: "travel/new", element: <TravelForm /> },
	{ path: "travel/:name", element: <TravelRecord /> },
];

export default defineSection({
	key: "seal_hrms.my_hr",
	home: MyHrHome,
	routes: ROUTES,
	records: RECORDS,
	settings: [{ key: "hr_notifications", label: "HR", kind: "push-category" }],
});
