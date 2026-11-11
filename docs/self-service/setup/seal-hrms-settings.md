---
title: SEAL HRMS Settings
type: doctype
order: 40
audience:
- admin
covers:
  doctypes:
  - SEAL HRMS Settings
sources:
- seal_hrms/seal_hrms/doctype/seal_hrms_settings/**
- seal_hrms/seal_hrms/sensitive.py
- seal_hrms/health/my_desk.py
---

**SEAL HRMS Settings is a single form for the whole site; it chooses which phone screens ask "is it still you?" before they show anything.**

A phone left signed in on a desk should not show someone's pay to whoever picks it up. Grace Wanjiru in HR leaves payslips and payout details asking first, and lets one check last five minutes.

**Where:** search bar → **SEAL HRMS Settings** · **Who:** System Manager.

## Confirm it is you

| Field | What it does |
| :--- | :--- |
| **Payslips** | Ticked (the default): the payslip list, each slip and its PDF ask for the person's fingerprint or password first. |
| **Payout Details** | Ticked (the default): where the person is paid, and their requests to change it, ask first. The rest of **My Details** still shows. |
| **Check Lasts (Minutes)** | How long one check lets these screens open without asking again. Between 1 and 60; 5 when left blank. Signing in counts as a check. |

Sending a payout change and approving an expense claim always ask, whatever is set here.

A banner at the top of the form, and App Health, say when a screen is set to ask but the site cannot ask yet (its SEAL Common is older than 1.35.0). The screens then show without asking.

## Other fields

**ESS Banner Image** is kept from an earlier release; nothing shows it now.
