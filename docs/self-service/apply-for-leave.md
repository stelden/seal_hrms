---
title: Apply for leave
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

You apply for leave with Frappe HR's **Leave Application** form. SEAL HRMS adds a handover to it, so someone covers your work while you are away, and a few checks. For the form itself, see the [Frappe HR documentation](https://docs.frappe.io/hr).

## Apply, and prepare your handover

1. Open **My HR** and click **Leave**, then **+ Add Leave Application**.
2. Fill in the leave type and dates as usual, and save.
3. Click **Prepare Handover**.

The form saves if it has unsaved changes, and opens a new handover for this leave, already filled with the open work on your to-do list and the approvals you give for others. Name your stand-in there and submit it. See [Hand over your work before leave](hand-over-your-work.md).

Once a handover exists, the leave application shows who covers you and the handover's status at the top (for example **Cover: Wanjiru Kamau (Accepted)**), and an **Open Handover** button instead of **Prepare Handover**. If the stand-in declined, a red notice asks you to open the handover and choose someone else.

## When a handover is needed

Your company's handover policy decides whether the leave can go ahead without one. Depending on it:

- the application cannot be sent on until a handover naming a stand-in exists;
- it cannot be sent on, or cannot be approved, until the stand-in has accepted;
- or the approver is only warned that nobody has agreed to cover.

The policy can apply only from a minimum length of leave, or only to some leave types. HR sets it; see [Handover policy](setup/handover-policy.md). If the leave is rejected or cancelled, its handover is called off and any work already handed over comes back to you.

## Other checks

- A new application cannot have a **Posting Date** before today.
- Where a leave type sets a minimum notice period, you cannot apply for it fewer than that many days before the leave starts.
- Leave of your time off in lieu type is refused if it would use time that will have lapsed by the time the leave starts, or time another leave application already relies on. The message says how many days you can use. See [Claim time off in lieu](claim-time-off-in-lieu.md#use-your-time-off).
- Someone approving leave in another approver's place cannot approve their own leave. See [Cover for a colleague](cover-for-a-colleague.md#approve-in-someones-place).
