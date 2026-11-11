---
title: Release notes
type: release-notes
order: 90
audience:
- buyer
- admin
sources:
- DOCUMENTATION.md
---

**What changed for users, newest first.** Dates are when each version was committed.

## 1.28.1 (2026-11-11)

- **Fixed:** the [Kenya Salary Register](payroll-reports/kenya-salary-register.md) is for HR User and HR Manager only, and shows only the salary slips the person running it may open. Staff could otherwise have been shown everyone's pay where a site let them report on salary slips.

## 1.28.0 (2026-11-11)

- **New:** [Compensatory leave requests](self-service/compensatory-leave-request.md) on the phone: ask for leave in return for working a public holiday or your day off. Your leave approver approves it from Approvals, and the days are added to your leave. Leave types used for time off in lieu are not offered.
- **Changed:** a link to Frappe HR's own phone app for a new compensatory leave request opens the new request form.

## 1.27.0 (2026-11-11)

- **Changed:** **My HR** is now **Self Service**: the tile on the Apps screen and the section of the phone app, the same name as the page they open; see [Self Service on the phone](self-service/my-hr-on-the-phone.md).
- **Fixed:** before you send a leave application, time off claim, timesheet, expense claim or shift request, the phone now says who **will** approve it ("Achieng Odhiambo will approve it."); it used to read as if it were already approved.
- **New:** payslips and where you are paid ask for your fingerprint or password first, so nobody can read them off an unlocked phone. HR chooses which screens ask, and for how long a check lasts, in [SEAL HRMS Settings](self-service/setup/seal-hrms-settings.md).
- **New:** [Travel requests](self-service/travel-request.md) on the phone and the desk: ask to travel for work, and your line manager approves it.
- **Changed:** amounts on a new advance request show the company's currency, as expense claims already did.

## 1.26.0 (2026-11-11)

- **New:** a **Line Manager** page for My Desk: approvals, who in your team is away this week, cover, timesheets and time off waiting for you, and quick links to your team's records. It goes to everyone with people reporting to them; see [Line Manager page](self-service/line-manager.md).
- **Changed:** a new payout change request is sent only to HR Managers who look after the employee's company.
- **Changed:** where your site controls changes to staff records, an HR Manager's approval of a payout change is that control: the change is applied, and the employee record notes which request made it and who approved it.
- **New:** App Health says when staff cannot get the My Desk phone app because My Desk is not installed.

## 1.25.0 (2026-11-11)

- **New:** on the phone, a timesheet week, an expense claim and a leave application you started are kept on the phone until you send them; see [My HR on the phone](self-service/my-hr-on-the-phone.md).
- **New:** HR notices reach your phone as their own kind, **HR**, which you can turn off; a notice about pay or about medical leave shows only a safe subject on a locked phone.
- **Changed:** Apply for Leave on the phone is one page: the handover shows beneath the leave instead of as a second step.
- **Fixed:** on the phone, the leave type no longer clears itself once both dates are chosen; Request a Change opens for staff who cannot see the list of banks; expense claims made on the phone can be approved (each expense now carries its account and cost centre, as on the desk).

## 1.24.0 (2026-11-10)

- **New:** [My HR on the phone](self-service/my-hr-on-the-phone.md): where your site has My Desk, apply for leave (with the handover), answer handovers, claim time off, fill your week's timesheet, claim expenses with receipt photos, ask for an advance, read payslips, check in, send attendance and shift requests, and see your details on your phone.
- **Changed:** links to Frappe HR's own phone app (`/hrms`) open the same thing in My Desk, or on the desk where there is no My Desk.
- **Changed:** staff on the Employee Self Service user type can open everything My HR shows, once the site is updated.

## 1.23.0 (2026-11-10)

- **New:** on My Desk, leave, expense claims, time off claims and timesheets waiting for you (or for someone you approve for) show under **Waiting for my approval** and can be approved there; see [SEAL HRMS on My Desk](self-service/my-desk.md).
- **New:** **Balances**, **Cover** and **HR work** for desk pages, and up to three HR headlines.
- **New:** [Payout Change Request](self-service/payout-change-request.md): staff ask to be paid into a new account or number; HR confirms it first, and the old number and address are told.
- **Changed:** HR's emails also put a line on the person's bell.
- **Changed:** the **Employee Self-Service** page adds Balances, Cover, Time off in lieu, Timesheets, new actions and three first steps.

## 1.22.0 (2026-11-10)

- **New:** this user guide: **SEAL HRMS User Guide** in the desk's Help menu, and a link to the right page in the Help menu of each form and report SEAL HRMS adds or changes.

## 1.21.0 (2026-11-10)

- **Changed:** shorter, clearer field names and descriptions across time off claims, the Working Time Policy, handovers, the handover policy, statutory numbers on the employee record and timesheet approval.
- **New:** the Self Service sidebar shows **TOIL Balances** and **Timesheet Cross-Check**.

## 1.20.1 (2026-11-09)

- **Fixed:** a new site gets the time off workflow and email templates when SEAL HRMS is installed, not only after its first migrate.

## 1.20.0 (2026-11-09)

- **Changed:** time off claims move by a workflow: send, authorise, approve, return and reject are in the claim's **Actions** menu, and **Return** or **Reject** ask for the reason first. HR can change who takes each step.
- **Changed:** where your site runs its own workflow on timesheets, that workflow approves them.

## 1.19.4 (2026-11-09)

- **Changed:** My HR shows a larger greeting, with tiles for time off in lieu and timesheets.

## 1.19.3 (2026-11-09)

- **Changed:** time off claim lines no longer ask for a project and task.

## 1.19.2 (2026-11-09)

- **Changed:** My HR greets you by name instead of showing a banner picture.

## 1.19.1 (2026-11-09)

- **Changed:** new Working Time Policies start with 1.5 for an extra hour on a working day, 2 on a rest day or public holiday, at least 1 hour, usable for 90 days, claims within 30 days, at most 10 days held.

## 1.19.0 (2026-11-09)

- **New:** **Claim as Time Off in Lieu** on an approved timesheet with extra hours.

## 1.18.0 (2026-11-09)

- **New:** the weekly check on timesheets, and the **Timesheets Against Attendance and Leave** report for HR.

## 1.17.0 (2026-11-09)

- **New:** timesheets by the week, in a grid, with **Copy last week**.

## 1.16.0 (2026-11-09)

- **New:** timesheet approval, where a company asks for it.
- **Fixed:** staff opening a new timesheet no longer meet a permission error.

## 1.15.0 (2026-11-09)

- **New:** **Authorise first, then confirm the hours** for time off claims, emails at each step, and the claim's process map.

## 1.14.0 (2026-11-09)

- **New:** time off claims show what attendance, clock-ins and timesheets record beside each day, with **Fill from Records**, and **Apply for Leave** once approved.

## 1.13.0 (2026-11-09)

- **New:** unused time off in lieu lapses claim by claim, and the **Time Off in Lieu** report shows each person's balance.

## 1.12.0 (2026-11-09)

- **New:** time off in lieu: claim extra hours, have them approved and take them as leave.
