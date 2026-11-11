---
title: Task Assignment (handover)
type: doctype
order: 20
audience:
- buyer
covers:
  doctypes:
  - Task Assignment
sources:
- seal_hrms/seal_hrms/doctype/task_assignment/**
- seal_hrms/seal_hrms/doctype/task_assignment_todo/**
- seal_hrms/seal_hrms/task_assignment_actions.py
- seal_hrms/seal_hrms/task_assignment_access.py
- seal_hrms/seal_hrms/handover.py
- seal_hrms/seal_hrms/handover_jobs.py
---

**A task assignment (handover) is a transaction that names a colleague, your stand-in, to cover your work while you are on leave.**

The stand-in agrees first. Your work moves to their to-do list when the leave starts, and whatever is still open comes back to you on your first working day after it. Peter Otieno hands his supplier follow-ups to Amina Hassan for his two weeks' leave.

**Where:** Self Service → Leave & Attendance → Task Assignment

## Before you start

- A [leave application](apply-for-leave.md) of your own that has not ended.
- You and every stand-in need a login.

## Create a task assignment

The quickest way is **Prepare Handover** on your leave application. To start one yourself:

1. Open **Self Service**, click **Hand over**, then **+ Add Task Assignment**.
2. Choose yourself as **Employee**. Your open to-dos fill the **Work** tab.
3. Choose the **Leave Application**. Only your own leave that has not ended is offered.
4. Choose your **Stand-in**. Only active colleagues in your company who are not on leave on those dates are offered.
5. Write the **Handover Notes**: what has to be covered, in enough detail for someone who does not do your job.
6. On the **Work** tab, remove what does not need covering, add anything missing, and fill in **Covered By** on a row if someone other than your stand-in covers that task.
7. Click **Save**, then **Find What I Approve** to list on the **Approvals** tab the approvals you give for others. Name an **Acting Approver** on a row, or leave it blank for your stand-in.
8. Click **Submit**. The stand-ins are emailed and asked to agree.

The **Return Date** is worked out for you: the first working day after the leave on your holiday list.

## Statuses

The banner at the top says where the handover is (**Now**), what happens next (**Next**) and what you should do (**Do**).

| Status | Means | Moves on when |
|:---|:---|:---|
| **Draft** | Not sent yet. | You submit it. |
| **Awaiting Acceptance** | Each stand-in answers for what they cover, and each acting approver for each approval. | Everyone accepts, or someone declines. |
| **Declined** | Someone cannot cover; nothing has moved. You are emailed with their reason. | You **Cancel**, then **Amend** and name someone else. |
| **Accepted** | Everyone agreed. You are emailed. Nothing moves yet. | The leave is approved and has started. |
| **Active** | Your work is on the stand-ins' lists. | Your return date, or **I'm Back**. |
| **Handed Back** | Open work has come back to you. | |
| **Cancelled** | Called off; anything handed over has come back. | |
| **Legacy** | Recorded before handovers could return work. | |

Work moves only when everyone has agreed, the leave is approved, and it has started. This is checked every day, and also when the last answer comes in or the leave is approved.

## While you are away

- Each stand-in's to-do is theirs. Documents behind your tasks are shared with them if they could not open them otherwise.
- The day before you return, the stand-ins are reminded to leave you a note.
- If you come back early, click **I'm Back**: everything still open comes back at once. HR can do the same with **Return the Work Now**.

## After you submit

On your return date, work the stand-in finished stays finished, marked **Done while away**; anything still open comes back to your list; documents shared for the leave are unshared, and approvals passed on are taken back. Read your stand-in's notes on each task, and their **Return Note** on the **Return** tab.

Who can see a handover: you, the stand-ins it names, the approver of the leave, and HR. Stand-ins record their answers and notes only through the buttons on the form. See [Cover for a colleague](cover-for-a-colleague.md).

If your company's [Task Assignment Policy](setup/task-assignment-policy.md) switches on the email reminder, you are emailed a set number of days before your leave when nobody has been asked to cover yet.

## If you see a message

| Message | Why | What to do |
|:---|:---|:---|
| "You cannot cover your own work. Choose a colleague." | You named yourself. | Choose a colleague. |
| "… is no longer an active member of staff. Choose someone else." | | Choose someone else. |
| "… is on leave themselves between … and … (…). …" | The stand-in is away on those dates. | Choose someone else, or change the dates. |
| "… has no login, so work cannot be passed to them. …" | | Ask HR to give them a login, or choose someone else. |
| "This leave belongs to someone else. …" | | Choose your own leave application. |
| "This leave application has been cancelled, so there is nothing to cover." | | No handover is needed. |
| "… is listed twice under Approvals." | | Remove the duplicate row. |
| "Row … of Approvals is not an approval this site knows about. Use Find What I Approve." | | Click **Find What I Approve**. |
| "You can only prepare a handover for yourself." | | Choose yourself as **Employee**. |
