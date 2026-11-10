---
title: Handover policy
order: 20
audience:
- admin
covers:
  doctypes:
  - Task Assignment Policy
sources:
- seal_hrms/seal_hrms/doctype/task_assignment_policy/**
- seal_hrms/seal_hrms/doctype/task_assignment_policy_leave_type/**
- seal_hrms/seal_hrms/overrides/leave_application.py
- seal_hrms/seal_hrms/custom/hr_settings.json
- seal_hrms/seal_hrms/handover_jobs.py
---

A **Task Assignment Policy** decides, for one company, whether leave needs a stand-in who has agreed to cover before it goes ahead, and whether staff are reminded to prepare a handover. **HR Manager** creates and changes it.

## Set the policy

1. In the Self Service sidebar, under **Setup**, click **Task Assignment Policy**, then **+ Add Task Assignment Policy**.
2. Choose the **Company** and the **Handover Requirement**.
3. Set the fields under **Leave and Reminders** and save.

| Handover Requirement | What it does |
| :--- | :--- |
| **Off** | No check. |
| **Warn** | When the leave is approved, the approver is told nobody has agreed to cover. Approval goes ahead. |
| **Require on Approval** | The leave cannot be approved until a stand-in has accepted the handover. |
| **Require on Submission** | The application cannot move on from draft until a handover naming a stand-in exists, and cannot be approved until the stand-in has accepted. |
| **Require Acceptance before Submission** | The application cannot move on from draft until the stand-in has accepted. |

| Field | What it does |
| :--- | :--- |
| **Minimum Leave (Days)** | Only leave of at least this many days needs a handover. 0 applies to any length. |
| **Leave Types** | Only these kinds of leave need one. Empty applies to every kind. Sick leave is the usual one to leave out. |
| **Reminder Lead Time (Days)** | How many days before their leave staff see the reminder on My Desk. Starts at 7. |
| **Email Reminder** | Also email each person once, that many days ahead, if nobody has been asked to cover yet. |

## A company with no policy

Where a company has no Task Assignment Policy, the **Leave Handover Requirement** and **Leave Handover Minimum (Days)** in **HR Settings** apply, with the same choices. They show only when **Leave Approver Mandatory In Leave Application** is ticked; when it is not, no handover is needed. If the requirement is left blank, **Require on Submission** applies. No reminder email is sent.
