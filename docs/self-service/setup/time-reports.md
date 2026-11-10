---
title: Time off and timesheet reports
order: 40
audience:
- admin
covers:
  reports:
  - Time Off in Lieu
  - Timesheets Against Attendance and Leave
sources:
- seal_hrms/seal_hrms/report/time_off_in_lieu/**
- seal_hrms/seal_hrms/report/timesheets_against_attendance_and_leave/**
---

Two reports under **Setup** in the Self Service sidebar: balances of time off in lieu (**TOIL Balances**), and timesheets checked against attendance and leave (**Timesheet Cross-Check**).

## Time Off in Lieu (TOIL Balances)

Each person's time off in lieu, from their approved claims: **Earned (days)**, **Used**, **Lapsed Unused**, **Left**, what is **Lapsing in 30 Days** and the **Next Lapse**. **HR User**, **HR Manager**, **System Manager** and **Leave Approver** can run it; an approver sees the staff whose claims they can see, HR sees everyone.

| Filter | What it does |
| :--- | :--- |
| **Company** | Only this company's staff |
| **Employee** | One person |
| **Time Left Only** | Only people with time still to use (ticked by default) |

Use **Lapsing in 30 Days** to remind people to book their time off before it lapses.

## Timesheets Against Attendance and Leave (Timesheet Cross-Check)

Each person's days at a company: **Timesheet Hours** beside **Kind of Day**, **Leave**, **Present**, **Expected** and **Accounted For**, with the **Issues** found. It applies the same rules as the weekly check on the timesheet form, and includes draft timesheets, so you can see a week before it is sent. **HR User**, **HR Manager** and **System Manager** can run it.

| Filter | What it does |
| :--- | :--- |
| **Company** | Required |
| **From**, **To** | Required; at most 62 days |
| **Department**, **Employee** | Narrow a large company |
| **Issues Only** | Only days with an issue (ticked by default) |

The issues are **Not accounted for**, **Hours on a day of leave** and **Hours, but not present**.
