---
title: Time Off in Lieu Claim
type: doctype
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

**A time off in lieu claim is a transaction that sends extra hours you worked to your leave approver, to be added to your leave balance as time off.**

It is for grades given time off for extra hours instead of being paid for them. Once approved, you take the time like any other leave. Amina Hassan worked a Saturday stock count at Mwangaza Foods Ltd and claims it; Grace Wanjiru approves it and two days are added to her balance.

**Where:** Self Service → Leave & Attendance → Time Off in Lieu

## Before you start

Your company has a [Working Time Policy](setup/working-time-policy.md) with **Time Off in Lieu** ticked and your grade among its **Eligible Grades**, and you have a leave approver.

## Create a time off in lieu claim

1. Open **Self Service**, click **Time off in lieu**, then **+ Add Time Off in Lieu Claim**. Your own record is filled in as **Employee**.
2. Under **Extra Hours**, add a row for each day: the **Date**, the **Hours Worked** (the extra hours only) and the **Work Done**. Or click **Fill from Records**, then **Attendance** or **Timesheets**, and choose the dates (at most 62 days at a time).
3. Click **Save**. Each row shows the **Kind of Day** (working day, rest day or public holiday, from your holiday list), the **Rate** and the **Hours Credited**; the claim totals them as **Time Off (Days)**.
4. Click **Actions**, then **Send for Approval**. Your leave approver is emailed. While the claim waits it cannot be changed.

**Fill from Records** leaves out days in the future, days under the company's minimum, and days already claimed, paid as overtime or on approved leave. An approved timesheet with extra hours can also start a claim: see [Timesheets](timesheets.md#claim-extra-hours-as-time-off).

## Fields worth knowing

| Field | What it does |
|:---|:---|
| **Note** | Anything the approver should know. |
| **Approver** | The person's leave approver, set for you. |
| **Authorisation** | How extra work is agreed, set from the policy when the claim is made, so a later change of policy does not affect it. |
| **Approver's Note** | Why it was returned or rejected. |
| **Usable Until**, **Days Credited**, **Days Not Credited**, **Days Used**, **Days Lapsed**, **Days Left** | On the **Time Off** tab once approved. |

A claim must meet these rules: your grade banks extra hours and you are not paid by the hour from timesheets; each date appears once, is not in the future, and has at least the company's minimum hours; no date is a day of approved leave, on another of your claims, or paid as overtime; and the claim is sent within the company's claim deadline of its oldest day.

## Statuses

| Status | Means | Moves on when |
|:---|:---|:---|
| **Draft** | Being prepared. | You send it for authorisation or approval. |
| **Waiting for Authorisation** | Planned hours wait for the approver to agree (authorise-first companies). | The approver authorises, returns or rejects. |
| **Authorised** | Agreed; enter the hours worked after the work. | You send it for approval. |
| **Waiting for Approval** | Hours wait for a decision. | The approver approves, returns or rejects. |
| **Returned** | Sent back with a reason. A claim returned at approval in authorise-first goes back to **Authorised**. | You correct it and send it again. |
| **Approved** | The time is added to your balance. | HR cancels it. |
| **Rejected** | Refused, with a reason. | |
| **Cancelled** | The time it added is taken back. | |

## If your company authorises extra work first

1. List the days with the **Planned Hours** (future days are allowed) and save.
2. Click **Actions**, then **Send for Authorisation**.
3. After the work, enter the **Hours Worked** on each day, or use **Fill from Records**, and save.
4. Click **Actions**, then **Send for Approval**. Only authorised days can be confirmed.

## Approve, return or reject a claim

The approver is the person's leave approver (on their employee record, or their department's). Someone covering for the approver can decide in their place, and so can HR. Nobody decides their own claim.

1. Open the claim from the email, or from **Time off in lieu waiting for you** on My Desk.
2. Check each day. Under **Evidence**, each row shows the extra hours attendance, clock-ins and timesheets record, and the **Supporting Record**. **Approver only** means no record shows those hours and you are confirming them yourself.
3. Click **Actions**, then **Approve**, **Authorise**, **Return** or **Reject**. **Return** and **Reject** ask for a reason first.

Approvers do not change hours: return the claim and say what to change. The person is emailed after each decision, and sees it on their bell. Where your site has My Desk, approvers can also decide from **Waiting for my approval**.

## After you submit

The days are added to the person's balance of the time off leave type. Near the company's limit, what fits is added (**Days Credited**) and the rest shows as **Days Not Credited**.

### Use your time off

1. Open the approved claim and click **Apply for Leave**.
2. Complete the leave application for the dates you want.

Time off is taken in full or half days. Leave uses the time that lapses soonest first; each claim's unused time lapses on its own **Usable Until** date.

HR can cancel an approved claim from **Actions**. If leave already relies on that time and nothing else could cover it, the cancellation is refused until that leave is cancelled.

The time off leave type cannot be allocated, adjusted or paid out by hand, and a **Compensatory Leave Request** on it is refused (requests are for the other compensatory types: see [Compensatory leave requests](compensatory-leave-request.md)). An **Overtime Slip** leaves out days sent or approved as time off.

## If you see a message

| Message | Why | What to do |
|:---|:---|:---|
| "Add the days you worked extra." | No rows under **Extra Hours**. | Add the days. |
| "Nobody approves leave for …, so nobody can decide this claim. …" | No leave approver. | Ask HR to set one. |
| "This claim is with … Ask them to return it before changing it." | It is waiting for a decision. | Ask the approver to return it. |
| "Say why: the person reads this to know what to change or why it was refused." | **Return** or **Reject** without a reason. | Enter the reason. |
| "Approve or reject the claim from its Actions menu." | | Use **Actions**. |
| "This is your own claim. Someone else must decide it." | | Ask another approver or HR. |
| "You can only send your own claims." | | Open your own claim. |
| "Approved time off claims have added time to this allocation. Cancel those claims instead." | Someone changed the time off allocation by hand. | Cancel the claims instead. |
| "Only an approved Time Off in Lieu Claim can add time off in lieu." | Time off allocated by hand. | Use a claim. |
