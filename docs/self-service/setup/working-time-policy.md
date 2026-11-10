---
title: Working Time Policy
type: doctype
order: 10
audience:
- admin
covers:
  doctypes:
  - Working Time Policy
sources:
- seal_hrms/seal_hrms/doctype/working_time_policy/**
- seal_hrms/seal_hrms/doctype/working_time_policy_grade/**
- seal_hrms/seal_hrms/working_time/policy.py
- seal_hrms/health/working_time.py
---

**A working time policy is a master that sets, for one company, the length of a working day, whether staff bank extra hours as time off, and how timesheets are kept and approved.**

A company without one has time off in lieu off and ordinary timesheets. Grace Wanjiru sets Mwangaza Foods Ltd's policy: an 8-hour day, time off in lieu for supervisors, and weekly timesheets approved by line managers.

**Where:** My HR → Self Service → Setup → Working Time Policy

## Before you start

- For time off in lieu, a leave type with **Is Compensatory** ticked, kept for this purpose, and a leave period covering today.
- **HR Manager** creates and changes policies; **HR User** can read them.

## Create a working time policy

1. Open the **Working Time Policy** list and click **+ Add Working Time Policy**.
2. Choose the **Company**.
3. Set the **Normal Working Day (Hours)** (starts at 8).
4. Fill in the tabs you need, below, and click **Save**.

A banner at the top lists anything that stops time off in lieu or timesheet approval working for this company, such as a missing leave type, leave period, grades or approvers. App Health reports the same.

## Time off in lieu (off by default)

Tick **Time Off in Lieu** to let staff bank extra hours.

| Field | What it does |
| :--- | :--- |
| **Leave Type** | The leave the time is added to. It must have **Is Compensatory** ticked; keep one for this purpose. It should not carry forward, allow a negative balance or be paid out. |
| **Eligible Grades** | Staff in these grades claim time off; everyone else stays on paid overtime. Empty means nobody can claim. |
| **Authorisation** | **Claim afterwards**, or **Authorise first, then confirm the hours** (staff ask before the work). |
| **After-Hours Rate**, **Rest Day Rate**, **Public Holiday Rate** | How many hours of time off each extra hour counts as on each kind of day. Start at 1.5, 2 and 2. |
| **Daily Minimum (Hours)** | Shorter extra time on a day does not count. Starts at 1. |
| **Daily Limit (Hours)** | The most extra hours that count on a day. 0 means no limit. |
| **Validity (Days)** and **Validity Start** | How long the time can be used, counted from the last day worked or from approval. Starts at 90 days. Never beyond the end of the leave year. |
| **Claim Deadline (Days)** | Claims must be sent within this many days of the work. 0 means any time. Starts at 30. |
| **Balance Limit (Days)** | The most time off a person can hold. 0 means no limit. Starts at 10. |
| **Attendance and Clock-ins**, **Timesheets** | Show approvers what these records show beside each claim, and let staff fill claims from them. |
| **Overdue Claim Alert (Days)** | App Health lists claims waiting for a decision longer than this. 0 turns it off. |

:::caution
Approved time goes into the leave period covering the day of approval. Set up the next leave period before the current one ends, or approvals stop. App Health warns 30 days ahead.
:::

## Timesheets (approval and weekly timesheets off by default)

| Field | What it does |
| :--- | :--- |
| **Requires Approval** | Staff send timesheets to their approver, who approves (which submits) or returns them. Staff can no longer submit their own. |
| **Approver** | **Leave approver**, or **Line manager** (the person's **Reports To**; the leave approver steps in where the line manager has no login). |
| **Overdue Timesheet Alert (Days)** | App Health lists timesheets waiting longer than this. 0 turns it off. |
| **Weekly Timesheets** | One timesheet per person per week, filled in as a grid. |
| **Default Activity Type** | The kind of work a new line in the grid starts with. |
| **Day Start Time** | Each day's hours are recorded from this time, one piece of work after another. |
| **Unaccounted Time** | **Point out gaps**, or **Refuse to send a week that is not accounted for**. |

See [Timesheets](../timesheets.md) for what staff and approvers see.

:::note
If timesheets have a submission deadline set in SEAL Common, App Health warns where approval is also on: the deadline is checked when the approver approves, so a timesheet sent on time could be refused.
:::

## If you see a message

| Message | Why | What to do |
|:---|:---|:---|
| "Enter the hours in a normal working day." | | Fill in **Normal Working Day (Hours)**. |
| "… is not a leave type for time off in lieu. …" | The leave type does not have **Is Compensatory** ticked. | Pick one that does. |
