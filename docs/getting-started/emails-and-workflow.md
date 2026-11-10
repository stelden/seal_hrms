---
title: Emails and the time off workflow
type: concept
order: 30
audience:
- admin
sources:
- seal_hrms/seal_hrms/handover_notifications.py
- seal_hrms/seal_hrms/timesheets/notifications.py
- seal_hrms/seal_hrms/toil/notifications.py
- seal_hrms/seal_hrms/toil/workflow.py
- seal_hrms/health/**
---

**Every email SEAL HRMS sends is an Email Template HR can reword, and time off claims move by a Workflow your site owns.**

## Why it matters

Rewording an email or changing who takes a step needs no change to the system. Removing a workflow state, though, stops claims moving.

## How it works

| Templates named | Sent about |
|:---|:---|
| **Task Assignment - ...** | Handovers: asked to cover, agreed, declined, now covering, back tomorrow, welcome back, called off, and the reminder to prepare a handover. |
| **Time Off in Lieu - ...** | Time off claims: asked to authorise, asked to approve, authorised, approved, returned, rejected. |
| **Timesheet - ...** | Timesheets: asked to approve, approved, returned. |

Each of these emails also puts its subject on the person's bell, so My Desk on the phone can tell them too. Payout change requests send their own fixed emails and bell lines: see [Payout Change Request](../self-service/payout-change-request.md).

The time off and timesheet templates are created once and then left alone, so your wording stays.

Time off claims move through the workflow **Time Off in Lieu Claim**. It is created for you and then belongs to your site: HR can change which role takes each action, or rename an action. Keep its eight states: **Draft**, **Waiting for Authorisation**, **Authorised**, **Waiting for Approval**, **Returned**, **Approved**, **Rejected**, **Cancelled**.

## Where you see it

The **Email Template** and **Workflow** lists. App Health reports a workflow that is missing, switched off or short of a state.
