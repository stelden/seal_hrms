---
title: Timesheets
type: howto
order: 50
audience:
- buyer
covers:
  forms:
  - Timesheet
sources:
- seal_hrms/public/js/timesheet.js
- seal_hrms/seal_hrms/timesheets/**
- seal_hrms/seal_hrms/custom/timesheet.json
---

**You will have filled in a week's timesheet, sent it for approval, and claimed any extra hours as time off.**

**Who:** Employee, Employee Self Service; approvers · **Before you start:** your company's [Working Time Policy](setup/working-time-policy.md) may add approval, a weekly grid and a weekly check to Frappe HR's **Timesheet** form. Where it adds none, the form works as Frappe HR ships it; see the [Frappe HR documentation](https://docs.frappe.io/hr).

## Steps

Where your company keeps timesheets by the week, the form shows a grid at the top: a line per piece of work and a column per day.

1. Open **My HR** and click **Timesheets**, then **+ Add Timesheet**. **Week Starting** is set to this week's Monday; change it for another week.
2. For each piece of work, click **Add a line** and choose the **Activity Type**, and the **Project**, **Task** and **Work Done** where they apply. Or click **Copy last week** to start from last week's lines.
3. Enter the hours in each day's column.
4. Click **Save**.

Under the grid you see each day's total and your attendance hours. Rest days, public holidays and leave are marked on the day. The time lines below are written from the grid when you save, so you cannot edit them directly, and the timer is hidden.

You keep one timesheet per week; a second one for the same week is refused.

## What happens next

### The weekly check

Once saved, a weekly timesheet lists under the grid what does not add up, day by day:

- a working day whose hours plus approved leave are short of a full day;
- hours on a day of approved leave;
- hours on a day attendance does not show you present (only where your attendance is kept).

Extra hours on one day do not make up for a short day. Depending on your company, these are only pointed out, or the week cannot be sent for approval until it is put right.

### Send a timesheet for approval

Where your company asks for approval, you do not submit your own timesheet.

1. Save the timesheet.
2. Click **Send for Approval**.

Your approver is emailed. The **Approval** section shows the **Approval Status** and the **Approver**: your leave approver, or your line manager (**Reports To**) where the company chooses it. While it waits, the timesheet cannot be changed.

If it is returned, the **Return Reason** says what to change. Correct it and click **Send for Approval** again.

### Approve or return a timesheet

1. Open the timesheet from the email, or from **Timesheets waiting for you** on My Desk.
2. Click **Approve**, which submits it, or **Return** and enter the **Return Reason**.

The person is emailed either way. Someone covering for the approver during their leave can decide in their place, and so can HR. Nobody approves their own timesheet. Once approved, staff cannot cancel their own timesheet; their approver or HR can.

:::note
If your site runs its own workflow on timesheets, that workflow approves them and this approval stands down.
:::

### Claim extra hours as time off

If your grade banks extra hours as time off, an approved timesheet that records extra hours (any hours on a rest day or holiday, or beyond a normal working day) shows **Claim as Time Off in Lieu**.

1. Click **Claim as Time Off in Lieu**.
2. Check the new claim: a line per day, linked to the timesheet, with what the work was.
3. Save it and send it as usual. See [Time Off in Lieu Claim](time-off-in-lieu-claim.md).

Days already claimed, paid as overtime or on leave are left out. Nothing is saved until you save the claim. Once the claim is approved, the timesheet cannot be cancelled.

## If something goes wrong

| You see | Do this |
|:---|:---|
| "Enter the hours worked in the week." | Enter hours in the grid before saving. |
| "The week could not be read. Reload the timesheet and enter it again." | Reload and re-enter the week. |
| "Only a timesheet not yet sent, or returned, can be sent." | It is already waiting; wait for the decision. |
| "This timesheet is not waiting for approval." | Nothing to decide. |
| "Say what needs changing: the person reads this to put it right." | Enter a **Return Reason**. |
| "This is your own timesheet. Someone else must approve it." | Ask another approver or HR. |
| "Your approver approved this timesheet. Ask them or HR to cancel it." | Ask your approver or HR. |
| "Claim from a timesheet once it is approved (submitted)." | Wait for approval. |
