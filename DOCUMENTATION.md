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
| **Task Assignment Policy** | Per company: whether leave needs a stand-in who has agreed before it can be approved. |
| **SEAL HRMS Settings** | The Self Service banner image. |

> ⚠️ **`Task Assignment` also exists in `seal_customizations`.** Two apps ship a
> doctype of that name. This is the live one; the other belongs to the app being
> retired. A path lookup that globs across apps will find `seal_customizations`
> first — it sorts earlier — so always qualify which you mean.

---

## 4. Cover during leave (Task Assignment)

A member of staff going on leave lists the work they are handing over and names
a stand-in. The stand-in agrees, the work moves to them when the leave starts,
and **it comes back on the first working day after**. Design and decisions:
`dev_notes/seal_hrms/TASK_ASSIGNMENT_DESIGN.md`.

### The steps

| Status | What it means | Who acts |
|---|---|---|
| Draft | Being prepared: from **Prepare Handover** on the Leave Application, or a new Task Assignment | The member of staff, then **Submit** |
| Awaiting Acceptance | Sent. Each stand-in answers for what they cover. A task can name its own stand-in. | Stand-ins: **Accept** or **Decline** (a reason is required) |
| Declined | Someone cannot cover it. Nothing has moved. | The member of staff: **Cancel**, then **Amend** with someone else |
| Accepted | Everyone has agreed. Nothing moves yet. | Nobody |
| Active | The leave is approved and has begun, and the work is on the stand-ins' lists | Stand-ins: **Leave a Note**, **Note for Return**. The owner: **I'm Back** if early |
| Handed Back | Open work has returned to its owner | Nobody |
| Legacy / Cancelled | Before 1.3.0, or called off | Nobody |

Work moves only when **all three** hold: the stand-in agreed, the leave is
approved, and it has started. The daily job (`handover_jobs.daily`) checks
this, and so does approving the leave or the last stand-in's answer, whichever
comes last. The stand-ins are reminded the day before the return. The return
date skips holidays, read from the employee's Holiday List Assignment for that
date.

### Before leave is approved: Task Assignment Policy

One record per company:
- **Off**: approve as usual.
- **Warn**: the approver is told that nobody has agreed to cover.
- **Require**: leave cannot be approved until someone has.

It can apply only from a minimum length of leave, or only to chosen leave types.
Sick leave is the usual exception. The check runs in the Leave Application's
validate, so it holds whether leave is approved by submitting or by setting the
status.

### Approving in someone's place

A handover can pass on approvals as well as work. The **Approvals** tab lists
what the member of staff approves for others. **Find What I Approve** fills it
from who names them as approver. Each row names who approves in their place.
It is **answered on its own**, because agreeing to cover someone's tasks is not
agreeing to sign for them (decision T2).

While the handover is Active, the stand-in:
- is given the approver role, if they lack it, and the principal's pending
  documents are shared with them (read, write, submit);
- also gets documents raised for the principal while they are away;
- leaves a timeline note on each approval they give, naming both people and the
  handover;
- **cannot approve their own request**, even though their own approver is the
  person they are standing in for.

On return, the role and shares the handover added are taken back. A role the
stand-in already held is left alone. There is no chaining: if the stand-in goes
on leave too, nobody inherits it, and a health check says so.

**A Head of Department** hands over their department's approvals as one line,
*Approving for my department as Head of Department*. "Department head" means
named on a department's own leave or expense approver lists, not a line
manager. The line grants both approver roles and covers both kinds: anyone
asking who approves leave or expense claims for them gets the stand-in, and
seal_leave_planning's plan review follows too. When it is offered, the two kinds
it covers are not offered separately. A kind declares this with
`covers: [...]`, and `roles: [...]` for more than one role.

Kinds of approval come from the hook `task_assignment_authorities`. It is read
from each app's hooks module, because it is a nested dict (SEAL_DEV_RULES §2.17).
seal_hrms ships **leave** and **expense claims**. Another app declares its own
the same way, with `label`, `role`, `holds(user)`, `pending(user)` and
optionally `enabled`. See the docstring in `seal_hrms/seal_hrms/acting.py`.

The role is added and removed on the user's role list directly, not by saving
the User. Saving a User can be refused by site governance, or reset to a role
profile.

**Other apps ask through seal_common.** This app answers `seal_common.delegation`'s
`acting_delegation_providers` hook (`acting.delegations`). It announces each
start and end, so seal_buying can re-stamp documents waiting on the officer
(Head of Department, Head of Procurement, Accounting Officer), and
seal_leave_planning can let the stand-in review the team's leave plans.
seal_common is optional for this app and is imported only where installed.

On return the handover is marked finished **before** the end is announced, so
an app re-stamping at that moment already gets the officer back. A test pins
the order.

### How work moves

`seal_hrms/seal_hrms/handover.py` is the only code that moves work, so the form,
the daily job, the Leave Application hooks and the legacy patch all do it the
same way.

- **Going:** the stand-in gets a new ToDo through Frappe's own assignment path.
  That path posts the "assigned" comment, notifies them, and shares the document
  with them if they could not open it otherwise. The employee's ToDo is set to
  Cancelled, not edited, so whoever originally gave the work out is kept.
- **Coming back** (on the first working day after the leave, or on **I'm Back**):
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

### The emails, and rewording them

Every handover email is an **Email Template** named `Task Assignment - ...`,
shipped as a fixture. HR rewords them in Desk (Email Template list, filter on the
name), with no code change:

| Template | Sent to | When |
|---|---|---|
| Prepare Your Handover | the member of staff | leave coming up and nobody asked to cover (see below) |
| Asked to Cover | each stand-in | the handover is submitted |
| Agreed / Declined | the member of staff | everyone agreed / someone declined |
| Now Covering | each stand-in | the leave starts and the work moves |
| Back Tomorrow | each stand-in | the day before the return |
| Welcome Back | the member of staff | the work returns |
| Called Off | each stand-in | the leave is rejected or cancelled |
| Old Work Returned to You / to Its Owner | owner / stand-in | the one-off return of pre-1.3.0 work |

Every template gets the same variables:
- `employee_name`, `stand_in_name`, `leave_from`, `leave_to`, `return_date`;
- `handover` and `link`;
- `items` (the work, one line each);
- `reason`, `done_count`, `has_note`, `days_until`, `leave_application`.

User-entered text is escaped before it reaches a template. Frappe refuses to save
a template whose Jinja is broken. If one is missing or fails anyway, the
built-in wording is sent and the problem is logged; a handover email never
silently stops.

A template reworded in Desk stays reworded until this app ships a newer
version of the same template (fixtures re-import on migrate when the shipped
copy is newer).

**The pre-leave reminder email** goes to each member of staff once per leave
application:
- only when their company's **Task Assignment Policy** has *Also Email the
  Reminder* on, and for the leave types and lengths that policy is about;
- *Remind Staff to Hand Over (Days Before)* sets how far ahead;
- no email if a handover already exists for that leave;
- a company with no policy gets no email; My Desk shows the reminder either way.

The flag that stops a second email is the hidden
`Leave Application.custom_handover_reminder_sent`.

### Where handovers show up

- **My Desk** (if installed): a "Handovers waiting for you" list an admin places
  on any desk page (`hooks.py` → `seal_desk_cue_groups`, `renders_as: "list"`;
  `seal_hrms/desk/providers.py`, SEAL_DEV_RULES §3.15: seal_desk is never imported
  at module level, and a test says so). It shows:
  - "Hand over your work before your leave on …", within the policy's reminder
    window;
  - an unsent draft;
  - a declined handover, to its owner;
  - a request to cover, or to approve in someone's place, to the stand-in;
  - "Covering for … until …";
  - "Welcome back", for three days after the work returns.
- **Self-Service on My Desk** (since 1.9.0): figures for a person's own Employee —
  leave awaiting a decision, claims in approval and approved but unpaid, advances not
  yet paid and to settle, timesheets in draft — each counted through their own
  permissions and opening the list it counted (`seal_desk_cue_groups` →
  `seal_hrms.self_service`, `renders_as: "cues"`; questions in
  `seal_hrms/self_service_status.py`). Someone with no Employee gets none.
  seal_hrms ships a standard **"Employee Self-Service"** page with its parts
  (`seal_hrms/desk_page/`, `seal_hrms/desk_widget/`): it arrives as a draft with no
  audience; an admin chooses who gets it and publishes it (seal_desk D104). Without
  seal_desk the files are inert.

  The questions are answered in `handover_work.py`, which knows nothing about
  the desk.
- **Self Service.** A **Hand over** tile on the overview, a Task Assignment
  shortcut, and sidebar links. A **Setup** section at the bottom holds the two
  reports and the policy; the sidebar hides links a person cannot open.
- **Reports** (HR):
  - *Who Is Covering Whom* lists everyone away or about to be, with undecided
    cover first.
  - *Stand-in Load* shows people covering several colleagues, and the most at
    once.

The form learns who is looking from `task_assignment_access.my_employee`, not
from the browser. Staff may not filter Employee on `user_id` client-side, and
the browser suite found every non-HR stand-in getting a permission error
instead of an Accept button.

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
# Browser — every list and form (ours, plus Leave Application, which carries our script), and the Settings single
cd apps/seal_hrms/e2e && npx playwright test

# Python
bench --site dev.local run-tests --module seal_hrms.<module>
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_legacy_return
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_lifecycle
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_acting
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_surfaces
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_emails
```

`02-handover.spec.ts` walks a real handover in two logins: HR prepares and
submits one from the Leave Application, and the stand-in logs in and accepts.
After any Python change, **reload gunicorn before running it**: this bench
preloads the app, so stale workers serve a mix of old and new code, and the
suite then fails intermittently for reasons that are not in the code.

The browser suite asserts on `pageerror` and console errors rather than markup,
which is what catches a form script that throws on load — the failure mode that
leaves a blank form and no server-side trace.

---

## 7. Changelog

- **2026-10-02** — 1.9.0. My Desk "Self-Service" figures and a shipped "Employee
  Self-Service" page (seal_desk P6).
- **2026-10-01** — 1.8.1. On My Desk, handovers are now a "Handovers waiting for
  you" list an admin places on a page (`seal_desk_cue_groups`, `renders_as:
  "list"`), because My Desk's old feed and its `seal_desk_providers` contract were
  retired. The rows are the same; the area chip (`seal_desk_group_labels`) is gone.
- **2026-09-30** — 1.8.0. Editable emails, a pre-leave reminder email, and the
  Head of Department.
  - Every handover email is an Email Template HR can reword; a missing or
    broken one falls back to the built-in wording.
  - People with leave coming up and no handover are emailed once, when their
    company's policy says so.
  - A Head of Department hands over their department's leave and expense
    approvals as one line (`covers`, `roles`).
- **2026-09-30** — 1.7.0. Handovers on My Desk, in Self Service, and in two HR
  reports.
  - The browser suite walks the whole path: HR prepares from the leave, and
    the stand-in accepts.
  - Fixed on the way: stand-ins could not use the form at all (see §4 *Where
    handovers show up*), and a stand-in was offered a Cancel the server would
    refuse.
- **2026-09-30** — 1.6.0. Other apps learn who is acting, through seal_common.
  - This app answers `seal_common.delegation` and announces when acting starts
    and ends.
  - seal_buying's procurement capacities, and seal_leave_planning's plan
    review, follow a handover.
  - On return the handover is finished before the end is announced.
- **2026-09-30** — 1.5.0. Approving in someone's place while they are away.
  - A handover's Approvals tab, filled by **Find What I Approve**; each row is
    answered on its own.
  - While away, the stand-in gets the approver role and the pending documents,
    both taken back on return.
  - They cannot approve their own request, and every approval they give is
    noted on the document.
  - Kinds of approval are a hook (`task_assignment_authorities`); leave and
    expense claims ship.
  - New health check: *Approvals while away*.
- **2026-09-30** — 1.4.0. A handover is agreed before anything moves.
  - Stand-ins accept or decline, and a task can name its own stand-in.
  - Work moves when the leave starts, not when the form is submitted, and
    returns on the first working day after, holidays included.
  - Stand-ins leave notes per task, plus a note for the owner's return, and
    are reminded the day before the return.
  - The owner can end the cover early.
  - New *Task Assignment Policy*: Off, Warn or Require, per company, for leave
    being approved.
  - **Prepare Handover** on the Leave Application, and a banner on the form
    saying Now, Next and Do.
  - `leave_from` and `leave_to` are now real dates; patch `v1_12` clears any
    value that is not one first.
  - New health check: *Cover agreed before leave*.
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
