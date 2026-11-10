---
title: Statutory returns and bank advice
order: 10
audience:
- admin
covers:
  reports:
  - Kenya NSSF Register
  - Kenya SHIF Register
  - Kenya HELB Register
  - Kenya Salary Register
  - Payroll Bank Advice
sources:
- seal_hrms/seal_hrms/report/kenya_nssf_register/**
- seal_hrms/seal_hrms/report/kenya_shif_register/**
- seal_hrms/seal_hrms/report/kenya_helb_register/**
- seal_hrms/seal_hrms/report/kenya_salary_register/**
- seal_hrms/seal_hrms/report/payroll_bank_advice/**
---

These reports give you the monthly returns and the instruction to the bank from the salary slips in a period.

## Filters

All five take **Company**, **Start Date** and **End Date** (required; by default the last month), **Currency**, and **Document Status** (**Submitted** by default; **Draft** lets you check a payroll before submitting it).

## The reports

| Report | What it shows | Extra filters |
| :--- | :--- | :--- |
| **Kenya NSSF Register** | Each employee's **Payroll No**, **Surname**, **Other Names**, **National ID**, **KRA PIN**, **NSSF No**, **Gross Pay** and the contribution **Amount** | **Salary Component** (required; starts as Employee NSSF) |
| **Kenya SHIF Register** | Each employee's deduction for the health fund | **Salary Component** (required; starts as NHIF) |
| **Kenya HELB Register** | Each employee's **Employee ID**, **Employee Name**, **National ID** and HELB loan **Amount** | **Salary Component** (required; starts as HELB) |
| **Kenya Salary Register** | The full monthly register: one row per salary slip with the statutory numbers, each earning and deduction, **Gross Pay**, **Total Deduction**, **Net Pay** and bank details | **Employee** |
| **Payroll Bank Advice** | What to pay into each account: **Employee ID**, **Employee Names**, **National ID**, **Bank Name**, **Account No**, **Branch**, **Amount** | **Bank** |

:::tip
If a register comes out empty, check that **Salary Component** matches the name your salary structures use for that deduction.
:::
