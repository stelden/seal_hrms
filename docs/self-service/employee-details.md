---
title: Employee details
type: howto
order: 60
audience:
- admin
covers:
  forms:
  - Employee
  - Employee Separation
sources:
- seal_hrms/public/js/employee.js
- seal_hrms/seal_hrms/overrides/employee.py
- seal_hrms/seal_hrms/api.py
- seal_hrms/seal_hrms/custom/employee.json
- seal_hrms/seal_hrms/custom/employee_separation.json
---

**You will have an employee record with the statutory numbers payroll needs and the details to pay them by bank or mobile money.**

**Who:** HR User, HR Manager · **Before you start:** the employee exists in Frappe HR. For the rest of the record, see the [Frappe HR documentation](https://docs.frappe.io/hr).

## Steps

1. Open the employee. In the **Statutory** section, enter the **National ID**, **KRA PIN**, **SHA No.** and **NSSF No.**. The payroll registers read them. See [Payroll reports](../payroll-reports/index.md).
2. Choose **Reports To**. **Reports to Designation** and **Reports to Department** fill in from that person.
3. Save the employee.
4. To pay by bank: click **Create Bank Account** (shown until a **Bank Account** is set) and fill in the account. Only this employee's own bank accounts can be chosen. **Bank Account Name**, **Bank Account No.** and **Bank** fill in from it; payroll uses it when **Salary Mode** is Bank.
5. To pay by mobile money: make sure the employee has a login (**Create User**, if not), then choose the contact belonging to that login in **Contact**. To change the name or mobile number on it, click **Update Contact**, edit **Primary Mobile Number** or the name, and click **Update**.

## What happens next

An employee can be paid by bank transfer, mobile money or both; which is used is chosen when a payment is made. Until both are set, an orange notice at the top of the form says what is still missing. Mobile money goes to the contact's main mobile number, in the contact's name.

When someone leaves, the **Employee Separation** must name a **Separation Type**. Keep that list as described in [Keep the lists your forms offer](setup/lists.md). Dependants and beneficiaries have their own records: see [Employee Dependent and Beneficiary](employee-dependent-and-beneficiary.md).

## If something goes wrong

| You see | Do this |
|:---|:---|
| "Bank Account … belongs to …, not to this employee." | Choose an account belonging to this employee. |
| "Contact … belongs to …, not to this employee's User (…). …" | Choose the contact for this employee's own login. |
| "… has a Contact but no User. …" | Create the employee's login first, or clear **Contact**. |
| "Invalid Kenyan mobile number." | Enter the number as a Kenyan mobile number. |
| "A contact with this phone number already exists." | Use that contact, or another number. |
| "A contact needs a first name." | Enter the first name. |
