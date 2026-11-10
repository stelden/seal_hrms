---
title: Kenya SHIF Register
type: report
order: 20
audience:
- admin
covers:
  reports:
  - Kenya SHIF Register
sources:
- seal_hrms/seal_hrms/report/kenya_shif_register/**
---

**What does each employee pay to the health fund this month?**

**Where:** My HR → search bar → **Kenya SHIF Register** (no sidebar entry) · **Who can run it:** HR User, HR Manager.

## Filters

| Filter | Use it to |
|:---|:---|
| **Company** | The company's salary slips. |
| **Start Date**, **End Date** | The period (required; by default the last month). |
| **Currency** | The currency to show. |
| **Document Status** | **Submitted** by default; **Draft** checks a payroll before you submit it. |
| **Salary Component** | The health-fund deduction (required; starts as NHIF). |

## Columns

| Column | Shows |
|:---|:---|
| **Payroll Entry** | The payroll run. |
| **Surname**, **Other Names**, **National ID**, **SHA No** | The employee. |
| **Amount** | The deduction. |

## Reading it

An empty register usually means **Salary Component** does not match your deduction's name. A blank **SHA No** needs filling on the employee record.
