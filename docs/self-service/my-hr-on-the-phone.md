---
title: Self Service on the Phone
type: concept
order: 26
audience:
- buyer
- admin
sources:
- frontend-my-desk/src/**
- seal_hrms/my_desk/api.py
- seal_hrms/my_desk/section.py
- seal_hrms/my_desk/links.py
- seal_hrms/www/my-hr-go.py
- seal_hrms/my_desk/push.py
- seal_hrms/seal_hrms/working_time/user_type.py
- seal_hrms/seal_hrms/sensitive.py
- seal_hrms/seal_hrms/travel.py
- seal_hrms/seal_hrms/compensatory_leave.py
---

**Where your site has My Desk, everything you do for yourself in HR also works on your phone, under Apps → Self Service.**

## Why it matters

Leave, time off, timesheets, claims and payslips are things people deal with away from a desk. Self Service puts them in the My Desk app, with the same rules as on the desk: whoever approves on the desk approves here, and nothing you send skips a check.

## How it works

| Screen | What you do there |
|:---|:---|
| **Self Service** | See leave and time off left, what is waiting for a decision, and the quick actions: Apply for Leave, Claim Time Off, This Week's Timesheet, New Expense Claim, Check In. |
| **Leave** | Apply, and see each application. When your company asks for cover on leave like this, a **Handover** part shows beneath the leave once you have chosen the dates: who covers you, which work and which approvals to hand over. Applying sends the handover to them. |
| **Cover** | Agree or decline a handover (say why when you decline), leave notes on work you cover, leave a note for their return, and say I'm Back when you return early. |
| **Time Off in Lieu** | Claim extra hours a day at a time, or use **Fill from Records** to bring in the days attendance or timesheets show; send it for approval or authorisation; apply for leave from what an approved claim gave you. |
| **Timesheets** | Fill your week one day at a time, copy last week's lines, read the weekly check, and send it for approval. Once approved, claim its extra hours as time off. Only where your company keeps weekly timesheets; otherwise timesheets show read only. |
| **Expense Claims**, **Advances** | Claim expenses with a photo of each receipt; ask for an advance and see what is left to settle. |
| **Payslips** | Each month's slip, and the PDF in your company's own payslip layout. You confirm it is you first (see below). |
| **Check-in** | Check in and out, where HR allows it. Where HR asks, where you are is recorded with it. |
| **Attendance Requests**, **Shift Requests** | Ask for days worked away to count, or for another shift. |
| **Travel Requests** | Ask to travel for work: the journeys, and what the trip is expected to cost. Your line manager approves it. See [Travel requests](travel-request.md). |
| **Compensatory Leave** | Ask for leave in return for working a public holiday or your day off; your leave approver approves it. Shown where your site has a compensatory leave type that time off in lieu does not use. See [Compensatory leave requests](compensatory-leave-request.md). |
| **My Details** | Your details, your mobile number, your dependants and beneficiaries, and where you are paid (only the last four digits, once you confirm it is you). **Request a Change** asks HR to pay you somewhere else: you confirm it is you first, and HR confirms it before any pay goes there. See [Payout Change Request](payout-change-request.md). |

**Before anything is sent, each form says who will decide it**: "7 days. Achieng Odhiambo will approve it." on a leave application, and the same on time off, timesheets, expense claims, shift, travel and compensatory leave requests. Where nobody is set to approve that kind of request yet, the form says so: ask HR to set your approver.

**Payslips and where you are paid ask "is it still you?" first.** A phone left signed in on a desk should not show your pay to whoever picks it up, so these screens ask for your fingerprint or password before they show anything, and again once a few minutes have passed (five, unless HR sets otherwise). My Details still shows the rest of your details; press **Confirm** to see where you are paid. HR chooses which of these screens ask in [SEAL HRMS Settings](setup/seal-hrms-settings.md).

**Long forms are kept on your phone until you send them.** A timesheet week, an expense claim, a leave application and a travel request you have started come back as you left them if the app closes, with **Restored From This Phone** at the top; **Discard** or **Start Again** throws the kept copy away. Receipt photos are not kept: add them again. Nothing is kept once you send, and signing out of My Desk removes everything kept on that phone.

**Notifications.** HR's notices about your own leave, claims, timesheets and pay, and handovers asked of you, come to your phone as the **HR** kind: turn them off under Me → Settings → Notifications if you do not want them on this phone. Anything waiting for your decision comes as **Approvals**, so silencing HR never hides work you must approve. On a locked phone, notices about pay, payout details and advances show only their subject, a payslip notice never shows an amount, and a notice about sick, medical, maternity or paternity leave does not name the leave.

Everything you create is yours, in your own company, sent to your own approvers. Approvers open your records from their Approvals and see them read only.

Links to Frappe HR's own phone app (`/hrms`, and the links in its notifications) now open the same thing in My Desk. On a site without My Desk they open the desk.

## Where you see it

My Desk on the phone → Apps → Self Service. For HR: after the site is updated, staff on the Employee Self Service user type can open everything Self Service shows.

On the desk the same things are under the **Self Service** tile on the Apps screen.
