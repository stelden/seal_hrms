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

**Where staff find it (1.11.0).** The **My HR** tile on the Apps screen opens Self
Service, and its rail is its own (it was a row in Frappe HR's rail). It is the one Self
Service on every site: client apps ship their own tiles and workspaces for their own
records, not a Self Service of their own, and each person's daily work is on My Desk.
The page keeps the name "Self Service", so `/desk/self-service` and people's default
page do not move. The tile shows to anyone who may open the page (Employee Self Service);
its gate is `seal_hrms/desk_navigation.py` and never raises.

One workspace (`self_service`) with a Custom HTML Block overview, aimed at a
member of staff rather than an HR officer. It leans on stock HRMS doctypes —
Leave Application, Expense Claim, Shift Request, Travel Request — so there is
nothing to keep in sync when HRMS changes them.

The shell was copied from `seal_hrms`, not `seal_buying`, when it was reused for
WEL: the buying workspace assumes a procurement sidebar that a staff portal
does not want.

### Time off, overtime and timesheets

Self Service links to three stock Frappe HR features: **Compensatory Leave
Request** (a holiday worked becomes a day off), **paid overtime** (clock-ins
through payroll) and **Timesheet**. How to set each up and where each stops is
in `dev_notes/seal_hrms/GUIDE_TIME_OFF_OVERTIME_TIMESHEETS.md`, written for HR
and staff.

Timesheet approval, weekly entry and checks are being added phase by phase; the design and its open decisions are in
`dev_notes/seal_hrms/WORKING_TIME_DESIGN.md`. The Frappe HR behaviour that
design relies on is pinned by `tests/test_hrms_time_behaviour.py`: if it fails
after an upgrade, re-read the design before anything else.

### Time off in lieu (1.12.0)

Staff in some grades are given time off for extra hours instead of being paid
for them. A company switches it on in its **Working Time Policy** (one per
company, under Setup in the Self Service sidebar): the hours in a normal
working day, the leave type the time goes into (one marked "Is Compensatory",
kept for this), which grades bank their hours, how an hour counts on a weekday
evening, a rest day and a public holiday, the smallest claim, a daily cap, how
long the time can be used for, how soon a claim must be sent, and the most a
person may hold.

The steps:

1. The member of staff opens **Time Off in Lieu** in Self Service, lists the
   days they worked extra (date, hours, what the work was) and saves. The kind
   of day comes from their holiday list, and the form shows what the hours
   count as and the days of time off.
2. **Send for Approval** sends it to their leave approver (on their Employee
   record, or their department's). While it waits it cannot be changed.
3. The approver **Approves**, **Returns** it with a reason (the person
   corrects and sends again) or **Rejects** it with a reason. Approvers do not
   change hours. Nobody decides their own claim, HR included.
4. On approval the days are added to the person's balance of that leave type,
   and they take the time off with an ordinary Leave Application. If the person
   is near the company's limit, what fits is added and the rest is shown as not
   added.

**What the records show (1.14.0).** Beside each day, the claim shows the extra
hours that attendance, the clock-in reader and the person's submitted timesheets
record, and which of them bears the claim out. "Approver only" means none does:
the supervisor's word is enough, and the form tells the approver they are
confirming those days themselves. **Fill from Records → Attendance / Timesheets**
adds the days the records show extra hours on (up to 62 days at a time), leaving
out days already claimed, paid as overtime or on leave. A company can stop
showing either record in its Working Time Policy ("What approvers see").

The form says where the claim is, what happens next and what the reader should
do (Now / Next / Do), worked out for whoever is looking (`toil/stage.py`, drawn
by `public/js/where_it_is.js`). Once approved, **Apply for Leave** opens a leave
application for the time off type.

**Authorise first, then confirm the hours (1.15.0).** A company can choose, in
its policy ("When extra work is agreed"), that staff ask before the extra work:
they list the days with the hours planned (future days allowed) and click
**Send for Authorisation**; the approver clicks **Authorise** (or returns or
rejects it); after the work the person enters the hours actually worked (or
fills them from the records) and clicks **Send for Approval**; the approver then
approves as usual. Only authorised days can be confirmed, and a return after
authorisation goes back to Authorised, not to the start. The way a claim is
agreed is stamped on it when it is made, so a change of policy does not move
claims already in flight.

The approver is emailed when a claim is sent, and the person when it is
authorised, approved, returned or rejected. The six emails are Email Templates
named "Time Off in Lieu - ...", created once after migrate and never overwritten,
so HR's rewording stays. My Desk has a "Time off in lieu waiting for you" list
(claims to decide, claims returned, hours to confirm, drafts not sent, time
lapsing within 14 days), and Self Service counts claims waiting for a decision.
The claim's Approval tab draws its process map.

### Timesheet approval (1.16.0)

A company can say, in its Working Time Policy ("Timesheets" tab), that
timesheets need approval. Then a person's timesheet is submitted only by
approving it: they (or HR) click **Send for Approval**; their approver opens it
from My Desk ("Timesheets waiting for you") or the email, and clicks **Approve**
(which submits it) or **Return** with what to change. Staff can no longer submit
or cancel their own; nobody approves their own, HR included. The approver is the
person's leave approver, or their line manager ("Reports To") where the company
chooses it (the leave approver steps in when the line manager has no login).
Someone covering an approver's leave approves in their place (handover line
"Approving timesheets", also covered by a Head of Department's line). Where the
company does not ask for approval, the Timesheet form is exactly as ERPNext
ships it.

Also fixed for staff on every site: opening **New Timesheet** raised a
Permission Error, because ERPNext looks the person up by their login and this
app keeps the login field at a level staff cannot read. The form now gets the
person's own record through `task_assignment_access.my_employee_fields`
(own record, harmless fields only).

App Health reports staff with nobody to approve their timesheets, timesheets
waiting too long, and a timesheet submission deadline (SEAL Common) left on
where approval is on: the deadline is checked when the approver approves, so a
timesheet sent on time would be refused.

### Timesheets by the week (1.17.0)

A company can say, in its Working Time Policy ("Filling them in"), that each
person keeps one timesheet per week, filled in as a week. The Timesheet form
then shows a grid at the top: a line per piece of work (kind of work, project,
task, what it was) and a column per day, with each day's total and the person's
attendance hours underneath; rest days, public holidays and leave are marked on
the day. **Add a line** adds one; **Copy last week** starts from last week's
lines. On save the time lines are written from the grid, one piece of work
after another from the company's "Day starts at", so the form's own time lines
are read-only and ERPNext's timer is hidden. A second timesheet for the same
week is refused. Leave and holidays are shown, not written as time lines.

Rules a claim must meet: the person's grade banks hours and they are not paid
by the hour; each date once, not in the future, at least the smallest claim;
not a day of approved leave, not already claimed, and **not paid as overtime**:
a day is either paid or given as time off. An Overtime Slip made by payroll
leaves out a day that has been sent or approved as time off, and says so in its
timeline; a day typed into a slip by hand is refused.

Underneath (`seal_hrms/seal_hrms/toil/`): the balance stays Frappe HR's. Each
person has one allocation of the time off leave type per leave period, started
at zero, and each approved claim adds one leave ledger row tagged with the claim
(`Leave Ledger Entry.custom_toil_claim`). Cancelling an approved claim writes a
matching negative row, and is refused if leave relies on that time and no other
banked time could cover it. The time off leave type cannot be allocated, adjusted
or paid out by hand, and a Compensatory Leave Request on it is refused.

**Time off is taken in full or half days** (Frappe's leave), so a person needs at
least half a day banked to use it. There is no hourly time off (decided
2026-11-09); claims still earn in hours, which add up.

**Unused time lapses claim by claim (1.13.0).** Each approved claim is usable
until its own date (the company's "days the time off can be used for", counted
from the last day worked or from approval, and never past the end of the leave
year). Leave uses the time that lapses soonest first, so nothing lapses that
could have been used. Leave that starts after the time it would need has lapsed
is refused with what is usable. Each claim shows its days used, lapsed and left,
and the **Time Off in Lieu** report (Self Service sidebar, Setup: "Time Off in Lieu Balances") shows each person's
earned, used, lapsed and left, with what lapses in the next 30 days.

Underneath (`toil/lapse.py`, `toil/fifo.py`): Frappe HR's year-end job never
lapses an allocation that has been topped up, and cancelling any leave
application can delete an unrelated lapse row (both pinned by
`tests/test_hrms_time_behaviour.py`). So lapse rows are never trusted once
written: `reconcile` works out every claim's lapse from scratch and changes only
the rows that differ. It runs on approval and cancellation, after each leave
application of the type is submitted or cancelled, and daily. A lapse written
by Frappe's own job or its "Expire Allocation" button is undone.

Who sees what: the person, their approver, whoever approves in the approver's
place during their leave (a handover's "Approving time off in lieu" line, which
a Head of Department's line also covers), and HR. Sites with Employee Self
Service *users* (a User Type) get the claim added to it after each migrate.
App Health, and a banner on the policy form, report a company that switched it
on without a leave type, with an unsuitable leave type, without a leave period
covering today, without grades, or with claimants who have no approver.

The Self Service sidebar's **Compensatory Leave Request** link is replaced by
**Time Off in Lieu** on every site (decided 2026-11-09). Compensatory Leave
Request still works from its own list for other leave types.

---

## 6. Testing

```bash
# Browser — every list and form (ours, plus Leave Application, which carries our script), and the Settings single.
# Point it at dev.local's own nginx port: port 80 may answer from another site (2026-11-09).
cd apps/seal_hrms/e2e && SEAL_E2E_BASE_URL=http://localhost:8002 npx playwright test
# 03-time-off-in-lieu.spec.ts walks a claim in two logins (Otieno sends, Achieng approves); it seeds
# with _toil_fixtures.browser_set_up and puts everything back in browser_tear_down.
# 04-timesheet-approval.spec.ts does the same for a timesheet (Otieno sends, Achieng approves);
# 05-week-grid.spec.ts fills a week in the grid and checks the time lines it writes.

# Python
bench --site dev.local run-tests --module seal_hrms.<module>
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_legacy_return
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_lifecycle
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_acting
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_surfaces
bench --site dev.local run-tests --module seal_hrms.tests.test_task_assignment_emails
bench --site dev.local run-tests --module seal_hrms.tests.test_hrms_time_behaviour
bench --site dev.local run-tests --module seal_hrms.tests.test_seal_hrms_settings
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_days
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_claim
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_paid_vs_banked
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_endpoints_guarded
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_fifo
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_lapse
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_evidence
bench --site dev.local run-tests --module seal_hrms.tests.test_toil_authorise_first
bench --site dev.local run-tests --module seal_hrms.tests.test_timesheet_approval
bench --site dev.local run-tests --module seal_hrms.tests.test_timesheet_week
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

- **2026-11-09** — 1.17.0. **Timesheets by the week**, per company: a grid of work lines by day on
  the Timesheet form, with leave, holidays and attendance shown; the time lines are written from it
  on save; one timesheet per person per week; "Copy last week". Needs `bench migrate` and a restart.
- **2026-11-09** — 1.16.0. **Timesheet approval**, per company: staff send, their approver (leave
  approver or line manager) approves or returns; approving submits; staff no longer submit or
  cancel their own. Stand-ins and Heads of Department approve in an approver's place. My Desk list,
  emails, a Self Service count and three health checks. **Fixed:** staff opening New Timesheet met
  a Permission Error. Needs `bench migrate` and a restart.
- **2026-11-09** — 1.15.0. **Authorise first, then confirm the hours**, per company: staff ask
  before the extra work, the approver authorises, and afterwards the hours worked are confirmed
  and approved. **Emails** at each step (HR-editable templates, created once), a **My Desk** list
  "Time off in lieu waiting for you", a Self Service count, the claim's **process map**, and a
  health check for claims waiting longer than the company allows. Needs `bench migrate` and a
  restart.
- **2026-11-09** — 1.14.0. **What the records show** on time off claims: attendance, clock-ins
  and timesheets beside each day, with "Approver only" where none bears it out, and **Fill from
  Records** to add the days they show. The claim form gains the Now / Next / Do banner and an
  **Apply for Leave** button once approved. Fixed: staff could not save a claim (it linked to
  the grade master they cannot read), and filling a new claim left a blank first row. A browser
  walk now covers the two-login path. Needs `bench migrate` and a restart.
- **2026-11-09** — 1.13.0. **Time off in lieu lapses claim by claim** (§5): each approved claim is
  usable until its own date, leave uses the time that lapses soonest, leave relying on time that
  will have lapsed is refused, and a daily run writes the lapses that fall due. Claims show days
  used, lapsed and left; a new **Time Off in Lieu** report shows each person's balance and what
  lapses soon. Cancelling a claim is refused only when leave relies on time nothing else covers.
  The time off leave type can no longer be adjusted or paid out by hand. Four more health checks.
  Needs `bench migrate`.
- **2026-11-09** — 1.12.0. **Time off in lieu** (§5): staff in chosen grades claim extra hours
  worked, their leave approver approves, returns or rejects, and approved time is added to their
  leave balance. One **Working Time Policy** per company sets the rules. A day is either paid as
  overtime or given as time off, enforced on both sides. A Head of Department's handover covers
  these approvals too. The Self Service sidebar shows Time Off in Lieu in place of Compensatory
  Leave Request. Needs `bench migrate` and a restart.
- **2026-11-09** — 1.11.2. **SEAL HRMS Settings save again**: the form still checked the
  leave-planning settings that moved to seal_leave_planning, so every save failed before it
  reached the database. Groundwork for time off in lieu and timesheets (§5): a guide to what
  Frappe HR already does, the design, and tests that pin the Frappe HR behaviour it relies on.
  Among them: allocations topped up by Compensatory Leave Requests never lapse at year end, and
  cancelling a leave application deletes an unrelated lapse of the same leave type.
- **2026-11-07** — 1.11.1. Handovers keep what they give (found while seal_procurement's
  approvals were made to follow an officer on leave). **A role a handover grants survives a save
  of the stand-in's user record**: a role profile rebuilt their roles on every save and dropped it.
  **What comes to wait on the person away is shared hourly** with whoever approves for them, for
  every app's kinds of approval, not only at the start of the leave. **Documents that cannot be
  submitted can be shared** (a supplier registration): every share asked for submit rights,
  which Frappe refuses there, and the whole handover stopped. On sites without the leave-planning
  fields, **Leave Type and Leave Application save again** and the leave calendar loads: each read
  another app's field as if it were always there.
- **2026-10-21** — 1.11.0. Self Service gets its own **My HR** tile and its own rail
  (no longer mounted on Frappe HR), as the one Self Service on every site; client apps stop
  shipping their own (dev_notes/navigation_v16/CLIENT_SITE_REALIGNMENT.md). The workspace file
  now says it is standard, so a new site does not hold it as its own copy. Needs
  `bench migrate` and a restart for the tile.

- **2026-10-08** — 1.10.0. Frappe 16.50's new navigation. **Self Service** now sits in the Frappe HR app's left-hand rail, after Frappe HR's own areas, instead of on the desktop: open Frappe HR from the Apps screen and pick Self Service. Its menu is the one it always had. Ships a dock mounted on the host (`dock/`) and the module sidebar; the old `workspace_sidebar/` and `desktop_icon/` files stay for sites on older Frappe. `test_desk_navigation.py` checks the wiring. Needs `bench migrate`.

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
