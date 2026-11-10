---
title: Hand over your work before leave
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

A handover names a colleague, your stand-in, who covers your work while you are on leave. The stand-in agrees first. Your work moves to their to-do list when the leave starts, and whatever is still open comes back to you on your first working day after it.

## Prepare a handover

The quickest way is **Prepare Handover** on your leave application (see [Apply for leave](apply-for-leave.md)). To start one yourself:

1. Open **My HR** and click **Hand over**, then **+ Add Task Assignment**.
2. Choose yourself as **Employee**. Your open to-dos fill the **Work** tab.
3. Choose the **Leave Application** this handover is for. Only your own leave that has not ended is offered.
4. Choose your **Stand-in**. Only active colleagues in your company who are not on leave themselves on those dates are offered.
5. Write the **Handover Notes**: what has to be covered, in enough detail for someone who does not do your job.
6. On the **Work** tab, check the list. Remove what does not need covering, add anything missing, and fill in **Covered By** on a row if someone other than your stand-in should cover that task.
7. Save, then click **Find What I Approve** to list on the **Approvals** tab the approvals you give for others (such as their leave or expense claims). Name an **Acting Approver** on a row, or leave it blank for your stand-in.
8. Click **Submit**.

The stand-ins are emailed and asked to agree. The **Return Date** is worked out for you: the first working day after the leave on your holiday list.

:::note
You and every stand-in need a login. A handover is refused if a stand-in is you, is no longer active, or is on leave over the same dates.
:::

## What happens next

The banner at the top of the form says where the handover is (**Now**), what happens next (**Next**) and what you should do (**Do**).

| Status | What it means | Who acts |
| :--- | :--- | :--- |
| **Draft** | Not sent yet | You: **Submit** |
| **Awaiting Acceptance** | Sent; each stand-in answers for what they cover, and each acting approver for each approval | Stand-ins |
| **Declined** | Someone cannot cover. Nothing has moved. You are emailed with their reason. | You: **Cancel**, then **Amend** and name someone else |
| **Accepted** | Everyone agreed. You are emailed. Nothing moves yet. | Nobody |
| **Active** | The leave is approved and has started. Your work is on the stand-ins' lists. | Stand-ins |
| **Handed Back** | Open work has come back to you | Nobody |
| **Cancelled** | Called off; anything handed over has come back | Nobody |
| **Legacy** | Recorded before handovers could return work | Nobody |

Work moves only when all three hold: everyone has agreed, the leave is approved, and it has started. This is checked every day, and also when the last answer comes in or the leave is approved.

## While you are away

- Each stand-in's to-do is theirs while you are away. Documents behind your tasks are shared with them if they could not open them otherwise.
- The day before you return, the stand-ins are reminded to leave you a note.
- If you come back early, open the handover and click **I'm Back**. Everything still open comes back to you at once. HR can do the same with **Return the Work Now**.

## When you return

On your return date:

- work the stand-in finished stays finished, marked **Done while away**;
- anything still open comes back to your list;
- documents shared for the leave are unshared, and approvals passed on are taken back.

Read your stand-in's notes on each task, and their **Return Note** on the **Return** tab.

## Who can see a handover

You, the stand-ins it names, the approver of the leave, and HR. Stand-ins can read it but record their answers and notes only through the buttons on the form.

## If you have not prepared one

If your company's handover policy switches on the reminder, you are emailed a set number of days before your leave starts when nobody has been asked to cover yet. On My Desk, the reminder shows either way. See [Handover policy](setup/handover-policy.md).
