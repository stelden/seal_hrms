---
title: Getting started
order: 10
audience:
- admin
sources:
- seal_hrms/hooks.py
- seal_hrms/desk_navigation.py
- seal_hrms/seal_hrms/workspace/self_service/**
- seal_hrms/seal_hrms/doctype/working_time_policy/**
- seal_hrms/seal_hrms/doctype/task_assignment_policy/**
- seal_hrms/seal_hrms/toil/workflow.py
---

This page is for HR officers: what to set up so staff can use SEAL HRMS, and who can do what.

## How staff reach it

Staff open **My HR** on the Apps screen. It opens the **Self Service** page, which lists everything a member of staff can do for themselves. The tile shows for anyone allowed to open that page, which needs the **Employee Self Service** role. See [My HR and Self Service](../self-service/index.md).

Each member of staff needs an **Employee** record linked to their login (the **User ID** on the employee record). Handovers, time off claims and timesheet approval all work from that link.

## What to set up first

1. Make sure each member of staff has a **Leave Approver** on their employee record, or on their department. Handovers, time off claims and timesheets go to that person.
2. Decide whether leave needs a stand-in before it goes ahead, and create a **Task Assignment Policy** for each company. See [Handover policy](../self-service/setup/handover-policy.md).
3. If staff bank extra hours as time off, or if timesheets need approval or are kept by the week, create a **Working Time Policy** for each company. See [Working Time Policy](../self-service/setup/working-time-policy.md).
4. Open **App Health** for SEAL HRMS and fix anything it reports. The same warnings show as a banner on the **Working Time Policy** form.

:::note
A company with no Working Time Policy has time off in lieu switched off, and its timesheets work exactly as Frappe HR ships them.
:::

## Who can do what

| Role | What they can do |
| :--- | :--- |
| **Employee** or **Employee Self Service** | Prepare their own handover, claim time off in lieu, send their timesheets for approval |
| Named stand-in | Read the handover that names them, accept or decline it, and leave notes while covering |
| **Leave Approver** | Decide time off claims and read the handovers for leave they approve; also approve timesheets where the company says so |
| **HR User** | See and change every handover and claim; read the policies and the HR reports |
| **HR Manager** | As **HR User**, and create and change the Task Assignment Policy and the Working Time Policy |

Nobody approves their own leave, time off claim or timesheet, HR included.

## Emails you can reword

Every email SEAL HRMS sends is an **Email Template** that HR can reword in the **Email Template** list, without any change to the system:

| Templates named | Sent about |
| :--- | :--- |
| **Task Assignment - ...** | Handovers: asked to cover, agreed, declined, now covering, back tomorrow, welcome back, called off, and the reminder to prepare a handover |
| **Time Off in Lieu - ...** | Time off claims: asked to authorise, asked to approve, authorised, approved, returned, rejected |
| **Timesheet - ...** | Timesheets: asked to approve, approved, returned |

The time off and timesheet templates are created once and then left alone, so your wording stays.

## The time off claim workflow

Time off claims move through a workflow called **Time Off in Lieu Claim** (in the **Workflow** list). It is created for you and then belongs to your site: HR can change which role takes each action or rename an action. Keep its eight states (**Draft**, **Waiting for Authorisation**, **Authorised**, **Waiting for Approval**, **Returned**, **Approved**, **Rejected**, **Cancelled**): App Health reports a workflow that is missing, switched off or short of one.
