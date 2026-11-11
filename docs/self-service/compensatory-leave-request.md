---
title: Compensatory Leave Requests
type: concept
order: 28
audience:
- buyer
- admin
covers:
  forms:
  - Compensatory Leave Request
sources:
- seal_hrms/seal_hrms/compensatory_leave.py
- seal_hrms/my_desk/api.py
- seal_hrms/my_desk/approvals.py
- frontend-my-desk/src/pages/Compensatory.tsx
---

**A compensatory leave request asks for leave in return for working a public holiday or your day off; your leave approver approves it, and the days are added to your leave.**

Otieno Ochieng ran the Utamaduni Day immunisation outreach at Kibera clinic. On his phone he asks for a day off in return; Achieng Odhiambo, who approves his leave, approves it from her Approvals, and a day of **Holiday Duty Off** is added to his leave balance.

## How it works

1. On the phone: **Self Service → Compensatory Leave → New Request**. On the desk: the **Compensatory Leave Request** list.
2. Choose the **Leave Type**, the **Work From Date** and **Work End Date** (the holidays or days off you worked), tick **Half Day** if one of them was a half day, and say what you worked on in **Reason**.
3. The form says who will approve it ("Achieng Odhiambo will approve it.") and how many days of leave it would give. **Send Request** sends it at once.
4. Frappe HR checks that each day was a holiday or day off on your holiday list and that your attendance shows you present. If not, it says which day is wrong.
5. Your leave approver (the same person who approves your leave) is assigned the request. They **Approve** or **Reject** it from Approvals on My Desk; a rejection says why. Anyone approving their leave while they are away can decide it too. Nobody decides their own.
6. Approved, the days are added to that leave type, from the day after the last day worked. Rejected, the reason shows on your request; **Withdraw** removes a request that is not yet approved.

| State | Means |
| :--- | :--- |
| Waiting for Approval | With your leave approver |
| Approved | The days are in your leave balance |
| Rejected | Not approved; the reason is on the request |

Staff see only their own requests; the approver sees the requests assigned to them.

## Compensatory leave or time off in lieu

Two ways earn leave for extra work, and each leave type belongs to one of them:

- **Time off in lieu** counts hours of extra work, day by day, on your company's [time off in lieu](time-off-in-lieu-claim.md) leave type.
- **Compensatory leave requests** give whole (or half) days for holidays and days off worked, on any other compensatory leave type.

The leave types a company banks time off in lieu into are never offered here, and a request on one is refused. Where every compensatory leave type is time off in lieu, Self Service shows no Compensatory Leave screen and the form points you to **Claim Time Off**.

## For HR

A compensatory leave type is a **Leave Type** with **Is Compensatory** ticked. A leave period must cover the day after the work, or approving the request is refused until you add one.

HR can still submit a request on the desk as Frappe HR allows. Where your site runs its own approval workflow on compensatory leave requests, that workflow decides them instead: nothing is assigned, and Approvals shows the workflow's steps.
