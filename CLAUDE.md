# seal_hrms: notes for Claude Code

## Field Labelling Policy (Stelden standard, all seal_* / sigma* apps)

Labels name the field. Descriptions explain it. Never use one to do the other's job.

### Labels
- Use a short noun phrase: ideally 1–3 words, at most 4 words / ~30 characters. A longer label needs a clear reason.
- Use Title Case, matching ERPNext core style (e.g. "Posting Date", "Approved By", "Grand Total").
- No instructions or questions: never "Enter…", "Select…", "Please…", "Tick if…", "Is this…?".
- No trailing colons, question marks, full stops or exclamation marks.
- No explanatory parentheses. A unit or currency qualifier is the only exception: "Bid Period (Days)", "Rate (%)".
- Don't repeat the DocType name ("Requisition Department" → "Department") unless you need it to tell two similar fields apart (e.g. two dates on one form).
- Link fields: name the target concept ("Supplier", "Department"), not the action.
- Table (child) fields: plural noun ("Items", "Approvers", "Attachments").
- Check fields: a state or attribute ("Emergency Procurement", "Requires Approval", "Disabled"), not a question.
- Button fields: a short verb phrase is fine ("Fetch Items", "Get Quotations").
- Section Break: 1–3 words ("Budget", "Approval", "Supplier Details"). Tab Break: 1–2 words. Column Break: usually no label.
- Spell "Colour" (UK spelling), and write "and", not "&", in labels, sections, tabs and sidebar entries.
- Portal section and card headings follow these rules too.
- Standard abbreviations are fine: No., ID, KRA PIN, VAT, LPO, LSO, AGPO, IFMIS, PPADA. Don't invent new ones.
- Statutory or regulator-mandated names (e.g. form titles required by PPRA or a government circular) keep their official wording. Flag these instead of shortening them.

### Descriptions
- Put guidance, rules, constraints, examples and "when to use" text here.
- Write full sentences in sentence case, ending with a full stop. Keep it brief.
- Don't add a description that only repeats the label.
- Settings fields, technical fields and anything whose purpose is not obvious from its label always get a description, written for a non-technical user: what it is for and what changing it does. Aim for 150 characters or fewer.

### Scope
This applies to DocType JSON fields, Custom Fields (fixtures and `create_custom_fields` dicts in Python), Property Setters we own, Report columns and filters, Web Forms, Workspace/shortcut labels, list/filter labels set in JS, `frm.set_df_property(..., "label", ...)` calls, and form labels in any Vue/frappe-ui portal code in the app.

Never change fieldnames, DocType names or option values as part of a label change.

### Examples
| Before | Label | Description |
|---|---|---|
| Select the Department making this request | Department | |
| Is this an emergency procurement? (Tick if yes) | Emergency Procurement | Tick if this procurement is being processed under emergency provisions. |
| Name of the officer who approved the request | Approved By | |
| List of items to be procured | Items | |
| KRA PIN Number of the Supplier | KRA PIN | |
| Number of days the tender will remain open for bidding | Bid Period (Days) | Number of days the tender remains open for bid submission. |
| Amount including VAT in KES | Gross Amount | Inclusive of VAT. |
| Details about the Budget and Vote Head (section) | Budget | |

## Documentation travels with the change (Stelden standard, all apps)

Whenever this app changes, update the documentation the change affects **in the same commit**, without
being asked. A change is not finished while a document still describes the old behaviour.

- **What counts:** anything a user or developer can see or relies on: a field, label or description, a
  status or workflow step, a role or permission, a setting, a report, a portal page or its wording, an
  endpoint, a hook, a scheduler job, a new or retired feature.
- **Where to look:** `DOCUMENTATION.md` at the repo root (create it if the app has none); the user guide in
  `docs/` where the app has one; `README.md`; Custom HTML Block and workspace copy; print formats, email
  templates and help text that quote the changed thing; `dev_notes/<app>/HANDOVER.md` when what is open,
  the sites or the checks change.
- **Labels:** when a label changes, search the documentation for the old label and change every hit.
- **Write only what you confirmed in the code.** What you could not confirm goes in the handover under
  "Not checked".
- **When nothing is affected, say so** in the commit body (`Docs: none affected`), so a reviewer can tell
  "checked" from "forgot".

This is the app-level form of SEAL_DEV_RULES §1.19 (help-docs programme, `dev_notes/help_docs/PLAN.md`).
Once §1.19 and its `bench seal-docs` tooling land, follow them as well: they add `docs/` coverage and a
commit gate on top of this rule.

### Labels in this app

Existing labels were brought into line with the policy in November 2026. Keep them there: new and edited fields follow the policy. Programme record: `dev_notes/label_policy/README.md` in the bench.
