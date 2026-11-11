---
title: SEAL HRMS on My Desk
type: concept
order: 25
audience:
- buyer
- admin
sources:
- seal_hrms/desk/providers.py
- seal_hrms/my_desk/**
- seal_hrms/seal_hrms/notify.py
- seal_hrms/seal_hrms/desk_widget/**
- seal_hrms/seal_hrms/desk_page/**
---

**Where your site has My Desk, the HR approvals waiting for you, your balances and who is covering whom show there, and HR's emails reach your bell too.**

## Why it matters

Leave, expense claims, time off and timesheets are approved by a named person, not by a workflow step, so My Desk's **Waiting for my approval** could not see them. Approvers, and anyone approving in their place during their leave, now find them with everything else.

## How it works

| On My Desk | What it shows |
|:---|:---|
| **Waiting for my approval** and the phone's Approvals | Leave waiting for you as leave approver; expense claims waiting for you as expense approver; time off claims to authorise or approve; timesheets to approve; [travel requests](travel-request.md) from the people who report to you (through the travel workflow). Also those of anyone whose approvals you give while they are away, marked with whom they are for. Never your own. |
| **Balances** | Leave left for up to four leave types, most used first; time off in lieu left and lapsing in the next 30 days, where your grade banks extra hours. |
| **Cover** | Who is covering your work and until when, whose work you are covering, and whose approvals you give. |
| **Time off in lieu waiting for you**, **Timesheets waiting for you** | Claims and timesheets to decide or put right. |
| **HR work** | For HR Managers: payout changes to confirm. |
| **Who's Away This Week** | For managers: their team's leave this week, as far as they may open it. |
| Headlines | At most three, only when true: that you are approving for someone; time off in lieu lapsing within two weeks; last week's timesheet not sent, where your company keeps weekly timesheets with approval. |

Approving from My Desk does exactly what the form does: the same people may decide, a refusal needs a reason, and nobody decides their own. Approving an expense claim from the phone asks you to confirm it is you first. Where your site runs its own workflow on leave or expense claims, that workflow's steps show instead.

Every email SEAL HRMS sends about a handover, a time off claim, a timesheet or a payout change also puts a line on the person's bell (the subject only), so the phone can tell them too. On the phone those lines arrive as **HR** notifications, which each person can turn off, except anything waiting for their decision, which arrives as **Approvals**; see [Self Service on the phone](my-hr-on-the-phone.md). On the phone, payslips and payout details ask you to confirm it is you before they show.

The **Employee Self-Service** page shipped with SEAL HRMS now carries Balances, Cover, Time off in lieu and Timesheets, the actions **Time Off in Lieu Claim**, **Payout Change Request** and **My Details**, and three first steps: get the app, turn on fingerprint sign-in, check your payout details. A site that already published the page sees these in its draft and publishes again.

## Where you see it

My Desk, on the desk and on the phone. Managers get their own page: see [Line Manager page](line-manager.md). An admin can place **Balances**, **Cover**, **Time off in lieu waiting for you**, **Timesheets waiting for you** and **HR work** on any desk page. See [Payout Change Request](payout-change-request.md). Your own HR on the phone is [Self Service on the phone](my-hr-on-the-phone.md).
