---
title: Payout Change Request
type: doctype
order: 65
audience:
- buyer
- admin
covers:
  doctypes:
  - Payout Change Request
sources:
- seal_hrms/seal_hrms/doctype/payout_change_request/**
- seal_hrms/seal_hrms/payout_change.py
- seal_hrms/seal_hrms/step_up.py
- seal_hrms/health/my_desk.py
---

**A payout change request is how a member of staff asks to be paid into a new bank account or mobile money number; HR checks it and confirms it before any payment uses it.**

Changing where pay goes is what a thief would want most, so the old number and address are told, and nothing changes until an HR Manager approves. Otieno Ochieng moves his salary to a new account at his bank; Halima Abdi in HR checks his bank letter and approves it from the 1st of next month.

**Where:** My Desk → Employee Self-Service → New → Payout Change Request

## Before you start

You have an employee record with a login. For mobile money, HR has linked the contact of your own login on your employee record (see [Employee details](employee-details.md)).

## Ask for a change

1. Click **New**, then **Payout Change Request**. Your own record is filled in as **Employee**.
2. Choose the **Change**: **Bank Account** or **Mobile Money**.
3. For a bank account: choose the **Bank**, enter the **Account No.**, the **Branch** if your bank uses one, and the **Account Name** exactly as the bank has it, then attach a bank letter or the top of a statement under **Evidence**. For mobile money: enter the **Mobile No.**; the **Provider** is found from the number.
4. Say why under **Reason**, and click **Save**.
5. Click **Send to HR**. Where your site asks, confirm your password first.

Your old mobile number gets a text and your old email address an email: "A change to where your pay goes was requested in My Desk. If this wasn't you, call HR." HR Managers are emailed and see it on their bell. Until HR decides, you are paid as before.

## Fields worth knowing

| Field | What it does |
|:---|:---|
| **Account Name** | Must share your name: at least two of the words in your name (one, if your name is one word). Pay goes to the account holder. |
| **Previous Details** | What your employee record said when you sent the request, so HR can compare. |
| **Effective From** | Set by HR when approving. Payments before this day use the old details. |
| **Decision Note** | Why HR rejected the request. |
| **New Bank Account** | The bank account made from your request, once applied. |

## Statuses

| Status | Means | Moves on when |
|:---|:---|:---|
| **Draft** | Being prepared; you can change it. | You send it. |
| **Waiting for HR** | HR is checking it; it cannot be changed. | HR approves or rejects it, or you withdraw it. |
| **Approved** | The new details are used from **Effective From**. | |
| **Rejected** | Refused, with the reason in **Decision Note**. | |
| **Withdrawn** | You took it back before HR decided. | |

You can have one request waiting at a time.

## Approve or reject a request

**Who:** HR Manager. Nobody decides a request about themselves or one they raised.

1. Open the request from the email, from the bell, or from **Payout changes to confirm** on My Desk.
2. Compare the new details with the **Evidence** and the **Previous Details**.
3. Click **Decide**, then **Approve**, and choose **Effective From** (today, or a later day). Or click **Reject** and give the reason; the employee reads it. Where your site asks, confirm your password first.

On approval, a bank account becomes the employee's **Bank Account** and default account; the old one is kept, no longer the default. A mobile number becomes the main mobile number on the employee's own contact and their **Cell Number**. A later **Effective From** is applied by the overnight run on that day. The employee is emailed either way.

## If you see a message

| Message | Why | What to do |
|:---|:---|:---|
| "You can only ask to change your own payout details." | The request names someone else. | Choose your own record. |
| "Fill in … before sending." | A bank change needs the bank, account number, account name and evidence. | Fill them in and save. |
| "The account name … does not match …" | The account is not in your name. | Use an account in your own name. |
| "… already has a request waiting for HR." | Only one at a time. | Wait for HR, or withdraw the first. |
| "Confirm it is you to continue." | Your site asks for your password before this step. | Enter your password. |
| "This request is about you. Another HR Manager must decide it." | | Ask another HR Manager. |
| "… has no contact on their employee record. …" | Mobile money needs the employee's own contact. | Link it on the employee record, then approve. |
| "Effective From cannot be in the past …" | | Choose today or later. |

App Health reports requests waiting more than three working days, and a site whose SEAL Common cannot ask for a fresh check.
