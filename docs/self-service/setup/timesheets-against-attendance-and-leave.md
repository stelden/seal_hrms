---
title: Timesheets Against Attendance and Leave
type: report
order: 70
audience:
- admin
covers:
  reports:
  - Timesheets Against Attendance and Leave
sources:
- seal_hrms/seal_hrms/report/timesheets_against_attendance_and_leave/**
---

**Do each person's timesheet hours agree with their attendance and leave, day by day?**

**Where:** Self Service → Setup → Timesheet Cross-Check · **Who can run it:** HR User, HR Manager, System Manager.

## Filters

| Filter | Use it to |
|:---|:---|
| **Company** | Required. |
| **From**, **To** | Required; at most 62 days. |
| **Department**, **Employee** | Narrow a large company. |
| **Issues Only** | Only days with an issue (ticked by default). |

## Columns

| Column | Shows |
|:---|:---|
| **Employee**, **Name**, **Date** | The person and day. |
| **Timesheet Hours** | Hours on their timesheets, drafts included. |
| **Kind of Day**, **Leave**, **Present** | What the holiday list, leave and attendance say. |
| **Expected**, **Accounted For** | Hours due, and hours covered by timesheets and leave. |
| **Issues** | **Not accounted for**, **Hours on a day of leave** or **Hours, but not present**. |

## Reading it

It applies the same rules as the weekly check on the timesheet form and includes draft timesheets, so you can see a week before it is sent. Ask the person to correct the timesheet. See [Timesheets](../timesheets.md).
