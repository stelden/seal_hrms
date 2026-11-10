---
title: Set up SEAL HRMS
type: howto
order: 10
audience:
- admin
sources:
- seal_hrms/hooks.py
- seal_hrms/seal_hrms/doctype/working_time_policy/**
- seal_hrms/seal_hrms/doctype/task_assignment_policy/**
- seal_hrms/health/**
---

**You will have a company ready for handovers, time off in lieu and timesheets.**

**Who:** HR Manager · **Before you start:** each member of staff has an **Employee** record with their login in **User ID**.

## Steps

1. Give each member of staff a **Leave Approver** on their employee record, or on their department. Handovers, time off claims and timesheets go to that person.
2. Decide whether leave needs a stand-in before it goes ahead, and create a [Task Assignment Policy](../self-service/setup/task-assignment-policy.md) for each company.
3. If staff bank extra hours as time off, or timesheets need approval or are kept by the week, create a [Working Time Policy](../self-service/setup/working-time-policy.md) for each company.
4. Open **App Health** for SEAL HRMS and fix anything it reports. The same warnings show as a banner on the **Working Time Policy** and **Payout Change Request** forms, including payout changes waiting more than three working days.

## What happens next

Staff see **My HR** on the Apps screen. A company with no Working Time Policy has time off in lieu switched off, and its timesheets work as Frappe HR ships them. A company with no Task Assignment Policy follows **HR Settings** for handovers.

## If something goes wrong

| You see | Do this |
|:---|:---|
| "Your login is not linked to a member of staff." | Set the person's login in **User ID** on their employee record. |
| "Nobody approves leave for …, so nobody can decide this claim. …" | Set a **Leave Approver** for that person or their department. |
