---
title: Cover reports
order: 30
audience:
- admin
covers:
  reports:
  - Who Is Covering Whom
  - Stand-in Load
sources:
- seal_hrms/seal_hrms/report/who_is_covering_whom/**
- seal_hrms/seal_hrms/report/stand_in_load/**
---

Two reports show HR who is away, who is covering for them, and who is covering too much. **HR User**, **HR Manager** and **System Manager** can run them, from **Setup** in the Self Service sidebar.

## Who Is Covering Whom

One row per handover whose leave overlaps the dates you choose. Handovers that were declined or are still waiting come first: that is leave with nobody behind it.

| Filter | What it does |
| :--- | :--- |
| **Company** | Only this company's staff |
| **From**, **To** | The dates to look at; starts from today |
| **Status** | Only handovers at this status |

Columns: **Handover**, **Away**, **Department**, **From**, **Return Date**, **Stand-in**, **Status**, **Tasks**, **Others Covering**, **Approvals Handed Over**. Open a handover from the first column to chase its stand-in.

## Stand-in Load

One row per person covering for colleagues in the period, with **People Covered**, **Covering For**, **Tasks**, **Approvals**, and **At Once**: the most colleagues they cover on any one day. Someone covering several people at once, on top of their own work, is where things get dropped. Filters: **Company**, **From**, **To**.
