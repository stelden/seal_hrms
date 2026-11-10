---
title: Employee details
order: 60
audience:
- admin
covers:
  doctypes:
  - Employee Dependent and Beneficiary
  - Employee Separation Type
  forms:
  - Employee
  - Employee Separation
sources:
- seal_hrms/public/js/employee.js
- seal_hrms/seal_hrms/overrides/employee.py
- seal_hrms/seal_hrms/api.py
- seal_hrms/seal_hrms/custom/employee.json
- seal_hrms/seal_hrms/custom/employee_separation.json
- seal_hrms/seal_hrms/doctype/employee_dependent_and_beneficiary/**
- seal_hrms/seal_hrms/doctype/employee_separation_type/**
---

SEAL HRMS adds statutory numbers, payment details, dependants and beneficiaries, and separation types to Frappe HR's employee records. This page is for HR officers. For the rest of the employee record, see the [Frappe HR documentation](https://docs.frappe.io/hr).

## Statutory numbers

The **Statutory** section of the **Employee** form holds the **National ID**, **KRA PIN**, **SHA No.** and **NSSF No.**. The payroll registers read them. See [Statutory returns and bank advice](../payroll-reports/statutory-returns.md).

**Reports to Designation** and **Reports to Department** are filled in from the person chosen in **Reports To**.

## Payment details

An employee can be paid by bank transfer, by mobile money, or both; which is used is chosen when a payment is made. Until both are set, an orange notice at the top of the form says what is still missing.

**Set up the bank account**

1. Save the employee.
2. Click **Create Bank Account** (shown until a **Bank Account** is set) and fill in the account.

Only this employee's own bank accounts can be chosen, and saving refuses an account belonging to anyone else. **Bank Account Name**, **Bank Account No.** and **Bank** fill in from it. Payroll uses the same account when **Salary Mode** is Bank.

**Set up mobile money**

1. Make sure the employee has a login (**Create User**, if not).
2. In **Contact**, choose the contact belonging to their login.
3. To change the name or mobile number on it, click **Update Contact**, edit **Primary Mobile Number** or the name, and click **Update**.

Mobile money goes to the contact's main mobile number, in the contact's name. Saving refuses a contact that belongs to someone else's login, or a contact on an employee with no login.

## Dependants and beneficiaries

An **Employee Dependent and Beneficiary** record holds one person connected to a member of staff:

| Field | What it does |
| :--- | :--- |
| **Employee** | The member of staff |
| **First Name**, **Middle Name**, **Last Name** | As on their ID |
| **Gender**, **Date of Birth** | For benefit schemes that need them |
| **Type** | **Dependent**, **Beneficiary**, or **Dependent and Beneficiary** |
| **Relationship** | How they are related to the member of staff |
| **Contact Details** | How to reach them if the member of staff cannot be reached |

Find the list by searching for **Employee Dependent and Beneficiary** in the search bar. Only a **System Manager** can open it unless your site gives other roles access.

## Separation types

An **Employee Separation** (Frappe HR's record of someone leaving) must name a **Separation Type**: resignation, retirement, end of contract and so on. Keep the list of types under **Employee Separation Type**; each has just a name.
