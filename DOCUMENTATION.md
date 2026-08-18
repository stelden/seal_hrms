# SEAL HRMS — Documentation

> Kenyan statutory payroll reporting, an employee self-service shell, and the
> handful of Employee-master additions Frappe HRMS does not ship.
>
> Copyright (c) 2026, Stelden EA Ltd and contributors.

---

## 1. What it is

A **thin layer on Frappe HRMS**, not a replacement for it. Leave, payroll,
attendance and the Employee master all remain HRMS's; this app adds the three
things a Kenyan employer needs on top:

1. **Statutory registers** — the returns that must be filed monthly.
2. **A Self Service workspace** — one place a member of staff goes, rather than
   the full HR module.
3. **Employee-master additions** — dependants and beneficiaries, separation
   types, and task hand-over.

Because it is a layer, the rule from SEAL_DEV_RULES applies with force: **never
modify hrms or erpnext.** Everything here compensates from our own app through
hooks, custom fields and overrides. A change upstream must be absorbed here, not
pushed there.

### Dependencies

`frappe/erpnext`, `frappe/hrms`.

---

## 2. Statutory reports

The reason the app exists. Each is a Query Report:

| Report | Files |
|---|---|
| `kenya_nssf_register` | NSSF contributions |
| `kenya_shif_register` | SHIF (formerly NHIF) |
| `kenya_helb_register` | HELB loan deductions |
| `kenya_salary_register` | The full monthly register |
| `payroll_bank_advice` | The instruction to the bank |
| `salary_register_summary_with_monthly_comparison` | Month-on-month movement |
| `employee_salary_register_with_monthly_comparison` | The same, per employee |

> **Query Reports must use unqualified table names.** A hardcoded `db-name.`
> prefix in report SQL survives on the site it was written on and breaks on
> restore or rename with `OperationalError 1142`. Write `` `tabSalary Slip` ``,
> never `` `mydb`.`tabSalary Slip` ``.

`payroll_bank_advice` is the seam to `seal_bank_integration` — a payroll run
becomes a bank batch there, not here.

---

## 3. The records

| Record | What it is for |
|---|---|
| **Employee Dependent and Beneficiary** | Who depends on a member of staff, and who benefits if something happens to them. Two different questions, one record, distinguished by `type`. |
| **Employee Separation Type** | Why someone left — resignation, retirement, end of contract. |
| **Task Assignment** | Who covers a member of staff's work while they are on leave, and what exactly is being handed over. |
| **SEAL HRMS Settings** | The Self Service banner image. |

> ⚠️ **`Task Assignment` also exists in `seal_customizations`.** Two apps ship a
> doctype of that name. This is the live one; the other belongs to the app being
> retired. A path lookup that globs across apps will find `seal_customizations`
> first — it sorts earlier — so always qualify which you mean.

---

## 4. Self Service

One workspace (`self_service`) with a Custom HTML Block overview, aimed at a
member of staff rather than an HR officer. It leans on stock HRMS doctypes —
Leave Application, Expense Claim, Shift Request, Travel Request — so there is
nothing to keep in sync when HRMS changes them.

The shell was copied from `seal_hrms`, not `seal_buying`, when it was reused for
WEL: the buying workspace assumes a procurement sidebar that a staff portal
does not want.

---

## 5. Testing

```bash
# Browser — 8 tests: every list and form, plus the Settings single
cd apps/seal_hrms/e2e && npx playwright test

# Python
bench --site dev.local run-tests --module seal_hrms.<module>
```

The browser suite asserts on `pageerror` and console errors rather than markup,
which is what catches a form script that throws on load — the failure mode that
leaves a blank form and no server-side trace.

---

## 6. Changelog

- **2026-08-18** — First `DOCUMENTATION.md`. Added the browser suite, standard
  filters on the two list doctypes, and descriptions for every user-set field.
