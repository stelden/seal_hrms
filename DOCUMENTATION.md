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
| **Task Assignment** | Who covers a member of staff's work while they are on leave, and what exactly is being handed over. See §4. |
| **SEAL HRMS Settings** | The Self Service banner image. |

> ⚠️ **`Task Assignment` also exists in `seal_customizations`.** Two apps ship a
> doctype of that name. This is the live one; the other belongs to the app being
> retired. A path lookup that globs across apps will find `seal_customizations`
> first — it sorts earlier — so always qualify which you mean.

---

## 4. Cover during leave (Task Assignment)

A member of staff going on leave lists the work they are handing over and names
a stand-in. The work moves to the stand-in's list, and **comes back when the
leave ends**. Design and decisions: `dev_notes/seal_hrms/TASK_ASSIGNMENT_DESIGN.md`.

### How work moves

`seal_hrms/seal_hrms/handover.py` is the only code that moves work, so the form,
the daily job, the Leave Application hooks and the legacy patch all do it the
same way.

- **Going:** the stand-in gets a new ToDo through Frappe's own assignment path.
  That path posts the "assigned" comment, notifies them, and shares the document
  with them if they could not open it otherwise. The employee's ToDo is set to
  Cancelled, not edited, so whoever originally gave the work out is kept.
- **Coming back** (daily job, `handover_jobs.daily`, once the leave has ended):
  - work the stand-in finished stays finished, as "Done while away";
  - anything still open comes back to the employee from its original assignor;
  - a share opened for the stand-in is closed again;
  - an assignment the stand-in already had before the handover is left with them.
- **Leave rejected or cancelled:** the handover is cancelled, which gives back
  anything already moved.

Every step is idempotent. A row records how far it has got, and the handover is
locked for update before its work moves.

### Who can see it

The member of staff prepares their own. The stand-ins it names and the leave
approver can read it. HR and System Manager see everything. The Employee links
ignore User Permissions on purpose: HRMS gives every login an "Employee =
themselves" User Permission, which would otherwise hide the handover from its
own stand-in.

### Records from before 1.3.0

Before 1.3.0, a handover edited each ToDo to point at the stand-in and **never
pointed it back** after normal leave. The patch
`v1_11.return_stranded_task_assignments` marks those records **Legacy** and, per
decision T1, returns stranded work to its owner:
- only the most recent handover listing a task decides;
- work moved on since is left alone;
- a handover to oneself is ignored;
- owners and stand-ins are each emailed once.

The health check *Work returned after leave* shows anything it had to skip.

## 5. Self Service

One workspace (`self_service`) with a Custom HTML Block overview, aimed at a
member of staff rather than an HR officer. It leans on stock HRMS doctypes —
Leave Application, Expense Claim, Shift Request, Travel Request — so there is
nothing to keep in sync when HRMS changes them.

The shell was copied from `seal_hrms`, not `seal_buying`, when it was reused for
WEL: the buying workspace assumes a procurement sidebar that a staff portal
does not want.

---

## 6. Testing

```bash
# Browser — 8 tests: every list and form, plus the Settings single
cd apps/seal_hrms/e2e && npx playwright test

# Python
bench --site dev.local run-tests --module seal_hrms.<module>
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_legacy_return
```

The browser suite asserts on `pageerror` and console errors rather than markup,
which is what catches a form script that throws on load — the failure mode that
leaves a blank form and no server-side trace.

---

## 7. Changelog

- **2026-09-30** — 1.3.0. Task Assignment brings work back.
  - Work returns to the employee when their leave ends; before, it stayed with
    the stand-in for good.
  - The stand-in is given access to documents they could not open, and the
    original assignor is kept.
  - Typed-in tasks now record their ToDo.
  - The "stand-in also away" check tests overlap rather than containment.
  - Staff can prepare their own handover, and a status field shows how far it
    has got.
  - The patch returns work stranded under the old code: 35 ToDos on the MHC
    restore.
  - New health check: *Work returned after leave*.

- **2026-09-18** — 1.2.1. On My Desk this app's area chip reads **Staff Tasks**
  instead of "SEAL HRMS" (`hooks.py` → `seal_desk_group_labels`). Chosen because
  what reaches a desk from this module is Task Assignments, and "HR" is already
  the chip of the HRMS app's own module. Display only: filters and links still
  use the module name, and on a site without My Desk the declaration does
  nothing.
- **2026-08-18** — First `DOCUMENTATION.md`. Added the browser suite, standard
  filters on the two list doctypes, and descriptions for every user-set field.
