---
title: Travel Requests
type: concept
order: 27
audience:
- buyer
- admin
sources:
- seal_hrms/seal_hrms/travel.py
- seal_hrms/my_desk/api.py
- frontend-my-desk/src/pages/Travel.tsx
- seal_hrms/health/my_desk.py
---

**A travel request asks to travel for work; your line manager approves it before you go.**

Otieno Ochieng needs to visit Kisumu for a county health outreach review. He asks on his phone with the flight there and back and what the trip should cost; Achieng Odhiambo, whom he reports to, approves it from her Approvals.

## How it works

1. On the phone: **Self Service → Travel Requests → New Travel Request**. On the desk: the **Travel Request** list.
2. Choose the **Travel Type** and **Purpose of Travel**, add each journey (**From**, **To**, how, when, whether you need lodging) and, if you know them, the **Expected Costs**.
3. The form says who will approve it, then **Send for Approval** sends it. It is yours, in your own company.
4. Your line manager (the person your employee record says you report to) sees it under Approvals, and **Approve**s or **Reject**s it. HR can decide any request on the desk. Nobody decides their own.

| Step | Who |
| :--- | :--- |
| Draft, Send for Approval | You (or HR for you) |
| Pending Approval → Approved or Rejected | Your line manager, or HR |
| Approved → Cancelled | HR |

Staff see only their own requests; a line manager sees their own and those of the people who report directly to them. HR, and anyone else your site gives travel requests to, see them as the site decides.

Passport and identity details, the sponsor and the organiser are filled in on the desk, not on the phone.

## For HR

After the site is updated it has an approval workflow named **Travel Request** (if it had none for travel requests), staff (**Employee**) may create and read their own requests, and **Line Manager** may read and decide their team's. These are created once; change them as your site needs and they stay as you leave them. A site that already ran its own travel workflow keeps it. App Health says when travel requests cannot be sent or decided.

Someone with no line manager set can still send a request; the form tells them nobody is set to approve it, and HR decides it.
