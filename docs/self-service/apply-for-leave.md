---
title: Apply for leave
type: howto
order: 10
audience:
- buyer
covers:
  forms:
  - Leave Application
sources:
- seal_hrms/public/js/leave_application.js
- seal_hrms/seal_hrms/overrides/leave_application.py
- seal_hrms/seal_hrms/task_assignment_actions.py
- seal_hrms/seal_hrms/toil/lapse.py
---

**You will have applied for leave with a handover, so someone covers your work while you are away.**

**Who:** Employee, Employee Self Service · **Before you start:** a leave approver on your employee record. You apply on Frappe HR's **Leave Application** form; SEAL HRMS adds the handover and a few checks.

## Steps

1. Open **Self Service**, click **Leave**, then **+ Add Leave Application**.
2. Fill in the leave type and dates as usual, and click **Save**.
3. Click **Prepare Handover**. The form saves if it has unsaved changes, and opens a new handover for this leave, filled with the open work on your to-do list and the approvals you give for others.
4. Name your stand-in there and submit it. See [Task Assignment](task-assignment.md).
5. Back on the leave application, submit it as usual.

## What happens next

The leave application shows who covers you and the handover's status at the top (for example **Cover: Amina Hassan (Accepted)**), and **Open Handover** instead of **Prepare Handover**. If the stand-in declined, a red notice asks you to choose someone else.

Your company's [Task Assignment Policy](setup/task-assignment-policy.md) decides whether the leave can go ahead without a handover: it may need a handover naming a stand-in before it moves on from draft, need the stand-in's acceptance before it moves on or is approved, or only warn the approver. It can apply only from a minimum length of leave, or only to some leave types. If the leave is rejected or cancelled, its handover is called off and any work handed over comes back to you.

Other checks:

- A new application cannot have a **Posting Date** before today.
- Where a leave type sets a minimum notice period, you cannot apply fewer than that many days before the leave starts.
- Leave of your time off in lieu type is refused if it would use time that will have lapsed by the time the leave starts, or time another application already relies on. See [Time Off in Lieu Claim](time-off-in-lieu-claim.md#use-your-time-off).
- Someone approving leave in another approver's place cannot approve their own leave. See [Cover for a colleague](cover-for-a-colleague.md#approve-in-someones-place).

## If something goes wrong

| You see | Do this |
|:---|:---|
| "Please save this Leave Application as draft first, then click 'Prepare Handover' …" | Save the application, then click **Prepare Handover**. |
| "A handover is mandatory for this leave application. …" | Click **Prepare Handover** and name your stand-in. |
| "Posting date cannot be before today." | Set **Posting Date** to today. |
| "You can only prepare a handover for your own leave." | Open your own leave application. |
| "This leave has been cancelled, so there is nothing to hand over." | No handover is needed. |
