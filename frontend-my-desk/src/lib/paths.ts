// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Where each screen lives, relative to the section's own route (/my-desk/apps/my-hr), and how the shell
 * opens a DocType's list, record and new form here (SECTIONS_CONTRACT §2 `records`). The hook's `claims`
 * (seal_hrms/hooks.py) lists exactly the DocTypes in RECORDS.
 */

/** A record's name inside a path: one segment, whatever it holds (a Salary Slip's name has slashes). */
export const seg = (name: string) => encodeURIComponent(name);

/** A name back from a route parameter, whichever way the router decoded it. */
export function nameFrom(param: string | undefined): string {
	if (!param) return "";
	try {
		return decodeURIComponent(param);
	} catch {
		return param;
	}
}

export const P = {
	leave: "leave",
	leaveNew: "leave/new",
	leaveRecord: (n: string) => `leave/${seg(n)}`,
	cover: "cover",
	handover: (n: string) => `cover/${seg(n)}`,
	toil: "toil",
	toilNew: "toil/new",
	toilRecord: (n: string) => `toil/${seg(n)}`,
	timesheet: "timesheet",
	week: (monday: string) => `timesheet/week/${monday}`,
	timesheetRecord: (n: string) => `timesheet/${seg(n)}`,
	expenses: "expenses",
	expenseNew: "expenses/new",
	expenseRecord: (n: string) => `expenses/${seg(n)}`,
	advances: "advances",
	advanceNew: "advances/new",
	advanceRecord: (n: string) => `advances/${seg(n)}`,
	pay: "pay",
	payRecord: (n: string) => `pay/${seg(n)}`,
	checkIn: "check-in",
	attendance: "attendance",
	attendanceNew: "attendance/new",
	attendanceRecord: (n: string) => `attendance/${seg(n)}`,
	shifts: "shifts",
	shiftNew: "shifts/new",
	shiftRecord: (n: string) => `shifts/${seg(n)}`,
	me: "me",
	payoutNew: "me/payout/new",
	payoutRecord: (n: string) => `me/payout/${seg(n)}`,
	travel: "travel",
	travelNew: "travel/new",
	travelRecord: (n: string) => `travel/${seg(n)}`,
} as const;

export type Opener = { list?: string; record?: (name: string) => string; create?: string };

/** How /my-desk/r/<DocType>/<name> and /my-desk/l/<DocType> open in this section. */
export const RECORDS: Readonly<Record<string, Opener>> = {
	"Leave Application": { list: P.leave, record: P.leaveRecord, create: P.leaveNew },
	"Leave Allocation": { list: P.leave },
	"Task Assignment": { list: P.cover, record: P.handover },
	"Time Off in Lieu Claim": { list: P.toil, record: P.toilRecord, create: P.toilNew },
	Timesheet: { list: P.timesheet, record: P.timesheetRecord },
	"Expense Claim": { list: P.expenses, record: P.expenseRecord, create: P.expenseNew },
	"Employee Advance": { list: P.advances, record: P.advanceRecord, create: P.advanceNew },
	"Salary Slip": { list: P.pay, record: P.payRecord },
	Employee: { list: P.me, record: () => P.me },
	"Employee Checkin": { list: P.checkIn, record: () => P.checkIn, create: P.checkIn },
	"Attendance Request": { list: P.attendance, record: P.attendanceRecord, create: P.attendanceNew },
	"Shift Request": { list: P.shifts, record: P.shiftRecord, create: P.shiftNew },
	"Employee Dependent and Beneficiary": { list: P.me, record: () => P.me },
	"Payout Change Request": { list: P.me, record: P.payoutRecord, create: P.payoutNew },
	"Travel Request": { list: P.travel, record: P.travelRecord, create: P.travelNew },
};

/** Where a count on the home screen opens: the list its DocType has here. */
export function listFor(doctype: string): string | undefined {
	return RECORDS[doctype]?.list;
}
