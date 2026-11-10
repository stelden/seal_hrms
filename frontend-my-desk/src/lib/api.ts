// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Every server method the section calls. All but the last group are `seal_hrms.my_desk.api`, which
 * answers for the person signed in (MY_DESK_P5_PLAN §3); the rest are seal_hrms' existing endpoints the
 * desk uses too, so the phone obeys exactly the same rules.
 */

const API = "seal_hrms.my_desk.api.";

export const M = {
	home: `${API}home`,
	leaveList: `${API}leave_list`,
	leaveOptions: `${API}leave_options`,
	leaveRecord: `${API}leave_record`,
	applyForLeave: `${API}apply_for_leave`,
	colleagues: `${API}colleagues`,
	cover: `${API}cover`,
	handoverRecord: `${API}handover_record`,
	toilList: `${API}toil_list`,
	toilRecord: `${API}toil_record`,
	saveToilClaim: `${API}save_toil_claim`,
	toilAction: `${API}toil_action`,
	timesheets: `${API}timesheets`,
	timesheetWeek: `${API}timesheet_week`,
	timesheetRecord: `${API}timesheet_record`,
	saveTimesheetWeek: `${API}save_timesheet_week`,
	timesheetClaim: `${API}timesheet_claim`,
	expenseList: `${API}expense_list`,
	expenseOptions: `${API}expense_options`,
	expenseRecord: `${API}expense_record`,
	claimExpenses: `${API}claim_expenses`,
	advanceList: `${API}advance_list`,
	advanceRecord: `${API}advance_record`,
	requestAdvance: `${API}request_advance`,
	payslips: `${API}payslips`,
	payslipRecord: `${API}payslip_record`,
	payslipPdf: `${API}payslip_pdf`,
	checkinStatus: `${API}checkin_status`,
	checkIn: `${API}check_in`,
	attendanceRequests: `${API}attendance_requests`,
	attendanceOptions: `${API}attendance_options`,
	attendanceRecord: `${API}attendance_record`,
	requestAttendance: `${API}request_attendance`,
	requestShift: `${API}request_shift`,
	myDetails: `${API}my_details`,
	updateMyContact: `${API}update_my_contact`,
	payoutOptions: `${API}payout_options`,
	requestPayoutChange: `${API}request_payout_change`,
	setPayoutEvidence: `${API}set_payout_evidence`,
	payoutRequestRecord: `${API}payout_request_record`,
	// seal_hrms' own endpoints, the same the desk calls.
	respond: "seal_hrms.seal_hrms.task_assignment_actions.respond",
	respondAuthority: "seal_hrms.seal_hrms.task_assignment_actions.respond_authority",
	addNote: "seal_hrms.seal_hrms.task_assignment_actions.add_note",
	returnNote: "seal_hrms.seal_hrms.task_assignment_actions.leave_return_note",
	returnWork: "seal_hrms.seal_hrms.task_assignment_actions.return_work",
	extraTime: "seal_hrms.seal_hrms.toil.evidence.get_extra_time",
	sendPayoutChange: "seal_hrms.seal_hrms.payout_change.send",
	withdrawPayoutChange: "seal_hrms.seal_hrms.payout_change.withdraw",
} as const;

/** The payslip's PDF, opened by the browser as the person (never cached by the app, DESIGN §6.9). */
export function payslipPdfUrl(name: string): string {
	return `/api/method/${M.payslipPdf}?name=${encodeURIComponent(name)}`;
}
