---
title: Who Is Covering Whom
type: report
order: 40
audience:
- admin
covers:
  reports:
  - Who Is Covering Whom
sources:
- seal_hrms/seal_hrms/report/who_is_covering_whom/**
---

**Who is away in a period, and who is covering for them?**

**Where:** My HR → Self Service → Setup → Who Is Covering Whom · **Who can run it:** HR User, HR Manager, System Manager.

## Filters

| Filter | Use it to |
|:---|:---|
| **Company** | Only this company's staff. |
| **From**, **To** | The dates to look at (required); starts from today. |
| **Status** | Only handovers at this status. |

## Columns

| Column | Shows |
|:---|:---|
| **Handover** | The task assignment; open it from here. |
| **Away**, **Department** | Who is on leave. |
| **From**, **Return Date** | The leave. |
| **Stand-in**, **Status** | Who covers, and where the handover has got to. |
| **Tasks**, **Others Covering**, **Approvals Handed Over** | What was handed over, and to how many people. |

## Reading it

One row per handover whose leave overlaps the dates. Handovers that were declined or are still waiting come first: that is leave with nobody behind it. Open the handover to chase its stand-in. See [Task Assignment](../task-assignment.md).
