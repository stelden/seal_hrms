---
title: Roles and permissions
type: concept
order: 20
audience:
- admin
sources:
- seal_hrms/seal_hrms/doctype/*/*.json
- seal_hrms/seal_hrms/task_assignment_access.py
- seal_hrms/seal_hrms/toil/access.py
- seal_hrms/seal_hrms/timesheets/approval.py
---

**Who can see and decide handovers, time off claims and timesheets follows the leave approver, not only the role.**

## Why it matters

An approver who is not the person's leave approver cannot decide their claim, and nobody decides their own leave, time off claim or timesheet, HR included.

## How it works

| Role | What they can do |
|:---|:---|
| **Employee** or **Employee Self Service** | Prepare their own handover, claim time off in lieu, send their timesheets for approval, ask to change where their pay goes. |
| Named stand-in | Read the handover that names them, accept or decline it, and leave notes while covering. |
| **Leave Approver** | Decide time off claims and read the handovers for leave they approve; approve timesheets where the company says so. |
| **HR User** | See and change every handover and claim; read the policies and the HR reports. |
| **Line Manager** | Given to everyone with people reporting to them, and taken away when nobody does (unless it was given by hand or by a role profile). It allows nothing by itself: it decides who gets the [Line Manager page](../self-service/line-manager.md) on My Desk. |
| **HR Manager** | As **HR User**, and create and change the Task Assignment Policy and the Working Time Policy; approve or reject [payout change requests](../self-service/payout-change-request.md), except their own. |

An HR officer who is also an employee is, by Frappe HR's default, limited to records linked to their own employee record: turn off **Create User Permission** on their employee record so they can decide other people's requests.

Someone covering for an approver during their leave can decide in their place. See [Cover for a colleague](../self-service/cover-for-a-colleague.md).

## Where you see it

| Message | Means |
|:---|:---|
| "This is your own claim. Someone else must decide it." | You cannot decide your own time off claim. |
| "This is your own timesheet. Someone else must approve it." | The same for timesheets. |
| "You can only see your own time, or the time of staff whose leave you approve." | You opened another person's time off. |
