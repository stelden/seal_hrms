---
title: My HR and Self Service
order: 20
audience:
- buyer
covers:
  workspaces:
  - Self Service
sources:
- seal_hrms/seal_hrms/workspace/self_service/**
- seal_hrms/seal_hrms/sidebar/self_service/**
- seal_hrms/fixtures/custom_html_block.json
- seal_hrms/desk/providers.py
---

**My HR** is your own HR in one place: leave, handovers, time off, timesheets, expenses and payslips, without going through anyone.

## Open it

1. Open the Apps screen.
2. Click **My HR**.

The **Self Service** page opens. It greets you by name, with your designation and department, and shows a tile for each thing you can do. Each tile opens its list.

## What is on the page

| Tile | What you do there |
| :--- | :--- |
| **Leave** | Apply for leave and track what is left. See [Apply for leave](apply-for-leave.md). |
| **Hand over** | Before leave, pass your work and approvals to a colleague. See [Hand over your work before leave](hand-over-your-work.md). |
| **Attendance** | Ask for a day's attendance to be corrected. |
| **Time off in lieu** | Claim time off for extra hours you worked. See [Claim time off in lieu](claim-time-off-in-lieu.md). |
| **Timesheets** | Record your week and send it for approval. See [Timesheets](timesheets.md). |
| **Expenses** | Claim what you spent, or ask for an advance. |
| **Shifts** | Request a shift change. |
| **Travel** | Request travel for work. |
| **Payroll** | Your payslips, benefits and tax declarations. |
| **Training** | Programmes you are on, and feedback. |
| **HR** | Raise a grievance or refer someone. |

Two cards beside them open **My profile** (your own employee record) and **Before you plan** (the holiday list).

## The sidebar

The sidebar on the left lists the same things in groups: **Leave and Attendance**, **Expenses**, **Shifts and Travel**, **Payroll and Benefits**, **Training**, **HR and Others**, and **Setup** for HR officers. You see only the entries you are allowed to open.

Attendance requests, expense claims, advances, shifts, travel, payroll and training work as Frappe HR ships them. See the [Frappe HR documentation](https://docs.frappe.io/hr).

## On My Desk

If your site uses My Desk, your administrator can add these lists to a desk page:

- **Self-Service**: figures for your own leave awaiting a decision, expense claims in approval or approved but not yet paid, advances, timesheets in draft and time off claims waiting. Each opens the list it counts.
- **Handovers waiting for you**: a handover to prepare before your leave, one to send, a request to cover, who you are covering for, and a welcome back when your work returns.
- **Time off in lieu waiting for you** and **Timesheets waiting for you**: what you have to decide, correct or send.
