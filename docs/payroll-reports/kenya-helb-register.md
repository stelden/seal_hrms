---
title: Kenya HELB Register
type: report
order: 30
audience:
- admin
covers:
  reports:
  - Kenya HELB Register
sources:
- seal_hrms/seal_hrms/report/kenya_helb_register/**
---

**Which employees repay a HELB loan this month, and how much?**

**Where:** My HR → search bar → **Kenya HELB Register** (no sidebar entry) · **Who can run it:** HR User, HR Manager.

## Filters

| Filter | Use it to |
|:---|:---|
| **Company** | The company's salary slips. |
| **Start Date**, **End Date** | The period (required; by default the last month). |
| **Currency** | The currency to show. |
| **Document Status** | **Submitted** by default; **Draft** checks a payroll before you submit it. |
| **Salary Component** | The HELB deduction (required; starts as HELB). |

## Columns

| Column | Shows |
|:---|:---|
| **Employee ID**, **Employee Name**, **National ID** | The employee. |
| **Amount** | The loan repayment. |

## Reading it

Only employees with a HELB deduction appear. An empty register usually means **Salary Component** does not match your deduction's name.
