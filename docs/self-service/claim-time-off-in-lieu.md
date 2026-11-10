---
title: Claim time off in lieu
order: 40
audience:
- buyer
covers:
  doctypes:
  - Time Off in Lieu Claim
sources:
- seal_hrms/seal_hrms/doctype/time_off_in_lieu_claim/**
- seal_hrms/seal_hrms/doctype/time_off_in_lieu_claim_line/**
- seal_hrms/seal_hrms/toil/**
---

If your grade is given time off for extra hours instead of being paid for them, you claim the hours here. Once your leave approver approves the claim, the time is added to your leave balance and you take it like any other leave.

Your company switches this on, and sets the rates and limits, in its Working Time Policy. See [Working Time Policy](setup/working-time-policy.md).

## Make a claim

1. Open **My HR** and click **Time off in lieu**, then **+ Add Time Off in Lieu Claim**. Your own record is filled in as **Employee**.
2. Under **Extra Hours**, add a row for each day: the **Date**, the **Hours Worked** (the extra hours only) and the **Work Done**. Or click **Fill from Records**, then **Attendance** or **Timesheets**, and choose the dates (at most 62 days at a time) to add the days your records show extra hours on.
3. Add a **Note** if the approver should know anything.
4. Click **Save**.

Each row shows the **Kind of Day** (working day, rest day or public holiday, from your holiday list), the **Rate** and the **Hours Credited**. The claim totals them as **Time Off (Days)**.

5. Click **Actions**, then **Send for Approval**.

Your leave approver is emailed. While the claim waits it cannot be changed.

:::note
**Fill from Records** leaves out days in the future, days under the company's minimum, and days already claimed, paid as overtime or on approved leave.
:::

## Rules a claim must meet

- Your grade is one that banks extra hours, and you are not paid by the hour from timesheets.
- Each date appears once, is not in the future, and has at least the company's minimum hours.
- No date is a day of approved leave, on another claim of yours, or paid as overtime. A day is either paid or given as time off, never both.
- The claim is sent within the company's claim deadline of the oldest day on it.

## If your company authorises extra work first

Some companies ask staff to agree extra work before doing it. Then:

1. List the days with the **Planned Hours** (future days are allowed) and save.
2. Click **Actions**, then **Send for Authorisation**. Your approver authorises it, returns it or rejects it.
3. After the work, enter the **Hours Worked** on each day, or use **Fill from Records**, and save.
4. Click **Actions**, then **Send for Approval**.

Only authorised days can be confirmed. A claim returned at this stage goes back to **Authorised**, not to the start. How a claim is agreed is set when it is made, so a later change of policy does not affect it.

## Approve, return or reject a claim

The claim's approver is the member of staff's leave approver (on their employee record, or their department's). Someone covering for the approver during their leave can decide in their place, and so can HR. Nobody decides their own claim.

1. Open the claim from the email, or from **Time off in lieu waiting for you** on My Desk.
2. Check each day. Under **Evidence**, each row shows the extra hours attendance, clock-ins and timesheets record, and the **Supporting Record**. **Approver only** means no record shows those hours, and you are confirming them yourself.
3. Click **Actions**, then **Approve**, **Authorise**, **Return** or **Reject**.

**Return** and **Reject** ask for a reason first; the person reads it. Approvers do not change hours: return the claim and say what to change. The person is emailed after each decision.

## When the claim is approved

The days are added to the person's balance of the time off leave type. If they are near the company's limit, what fits is added (**Days Credited**) and the rest shows as **Days Not Credited**. The **Time Off** tab shows the **Usable Until** date, and **Days Used**, **Days Lapsed** and **Days Left** as time is taken.

## Use your time off

1. Open the approved claim and click **Apply for Leave**.
2. Complete the leave application for the dates you want.

Time off is taken in full or half days. Leave uses the time that lapses soonest first. Each claim's unused time lapses on its own **Usable Until** date.

## Cancel an approved claim

HR can cancel an approved claim from the **Actions** menu. The time it added is taken back. If leave already relies on that time and nothing else could cover it, the cancellation is refused until that leave is cancelled.

## Time off is added only by claims

The time off leave type cannot be allocated, adjusted or paid out by hand, and a **Compensatory Leave Request** on it is refused. An **Overtime Slip** leaves out days sent or approved as time off, and says so in its timeline.
