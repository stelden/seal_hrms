# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Move Employee payment details onto the multi-rail model.

The old model asked an employee to nominate one rail — `custom_preferred_payment_method`
(`Mpesa`/`Cheque`) — and hid the other rail's fields behind `depends_on`. Payment
does not work that way: an employee holds whatever details they hold, and the
rail is chosen per payment. This carries the data across and removes the fields
that encoded the old assumption.

Order matters. Data is copied to the surviving fields FIRST, then the dead fields
are dropped — so an interrupted run loses nothing, and a re-run is a no-op.

`sync_customizations` upserts Custom Fields and never deletes ones missing from
`custom/employee.json` (frappe/modules/utils.py), so removing them from that file
is not enough on its own; they have to be deleted here.

Reports rather than throws: an employee whose Contact cannot be resolved is a
data-entry task, not a migration failure.
"""

import frappe

# Dead Employee fields. Supplier keeps its own same-named fields — they belong to
# seal_imprest_management and are out of scope here.
DEAD_FIELDS = [
    "custom_preferred_payment_method",
    "custom_bank_account",
    "custom_new_bank_account",
    "custom_mpesa_contact",
    "custom_new_mpesa_contact",
    "custom_account_name",
    "custom_account_no",
    "custom_mpesa_salary_contact",
    "custom_new_mpesa_salary_contact",
    "custom_mpesa_salary_mobile_no",
    "custom_new_salary_bank_account",
    "custom_create_contact",
]


def execute():
    if not frappe.db.count("Employee"):
        print("[seal_hrms] rebuild_employee_payee_model: no employees — dropping fields only")
    else:
        moved_contacts = _carry_contacts()
        moved_accounts = _carry_bank_accounts()
        released = _release_foreign_contacts()
        print(f"[seal_hrms] rebuild_employee_payee_model: contacts={moved_contacts} "
              f"bank_accounts={moved_accounts} released={released}")
        _resync_stock_fields()

    dropped = _drop_dead_fields()
    print(f"[seal_hrms] rebuild_employee_payee_model: dropped {dropped} dead field(s)")
    frappe.db.commit()


def _carry_contacts() -> int:
    """`custom_mpesa_contact` → `custom_contact`, where the Contact is the User's.

    A Contact belonging to somebody else is left behind deliberately: the whole
    point of the new model is that an employee's mobile number comes from their
    own User, and silently carrying a foreign Contact across would bake the bug
    in rather than surface it.
    """
    if not _has_column("custom_mpesa_contact"):
        return 0

    rows = frappe.db.sql("""
        SELECT name, user_id, custom_mpesa_contact
        FROM `tabEmployee`
        WHERE custom_mpesa_contact IS NOT NULL AND custom_mpesa_contact != ''
          AND (custom_contact IS NULL OR custom_contact = '')
    """, as_dict=True)

    moved, foreign = 0, []
    for row in rows:
        owner = frappe.db.get_value("Contact", row.custom_mpesa_contact, "user")
        if owner and owner == row.user_id:
            frappe.db.set_value("Employee", row.name, "custom_contact",
                                row.custom_mpesa_contact, update_modified=False)
            moved += 1
        else:
            foreign.append({"employee": row.name, "contact": row.custom_mpesa_contact,
                            "contact_user": owner, "employee_user": row.user_id})

    if foreign:
        frappe.log_error(
            title="[seal_hrms] Employee contacts not carried over",
            message=frappe.as_json(foreign),
        )
    return moved


def _carry_bank_accounts() -> int:
    """`custom_bank_account` → `custom_salary_bank_account`, if that is empty."""
    if not _has_column("custom_bank_account"):
        return 0

    rows = frappe.db.sql("""
        SELECT name, custom_bank_account
        FROM `tabEmployee`
        WHERE custom_bank_account IS NOT NULL AND custom_bank_account != ''
          AND (custom_salary_bank_account IS NULL OR custom_salary_bank_account = '')
    """, as_dict=True)

    for row in rows:
        frappe.db.set_value("Employee", row.name, "custom_salary_bank_account",
                            row.custom_bank_account, update_modified=False)
    return len(rows)


def _release_foreign_contacts() -> int:
    """Unlink Contacts that do not belong to the employee's own User.

    These predate the rule — a Contact with no User, or one belonging to somebody
    else. Leaving them linked would let a payment resolve a number the employee
    does not own, which is the precise failure the new model exists to prevent,
    and would also make the record unsaveable the moment anyone edited it.

    Only the link is cleared. The Contact itself, and `cell_number`, are left
    alone: the number may well be right, and this is not the place to decide.
    """
    rows = frappe.db.sql("""
        SELECT e.name, e.user_id, e.custom_contact, c.user AS contact_user
        FROM `tabEmployee` e
        LEFT JOIN `tabContact` c ON c.name = e.custom_contact
        WHERE e.custom_contact IS NOT NULL AND e.custom_contact != ''
          AND (e.user_id IS NULL OR e.user_id = ''
               OR c.user IS NULL OR c.user != e.user_id)
    """, as_dict=True)

    for row in rows:
        frappe.db.set_value("Employee", row.name, "custom_contact", None,
                            update_modified=False)

    if rows:
        frappe.log_error(
            title="[seal_hrms] Employee contacts released — reassign from the User's Contact",
            message=frappe.as_json(rows),
        )
    return len(rows)


def _resync_stock_fields():
    """Refresh `cell_number` and the default Bank Account flag from the links."""
    from seal_hrms.seal_hrms.payout_details import sync_payout_details

    report = sync_payout_details(commit=True)
    print(f"[seal_hrms] rebuild_employee_payee_model: phones_set={report['phones_set']} "
          f"contacts_linked={report['contacts_linked']} "
          f"defaults_fixed={report['defaults_fixed']} unpayable={len(report['skipped'])}")
    if report["skipped"]:
        frappe.log_error(
            title="[seal_hrms] Employees still not payable",
            message=frappe.as_json(report["skipped"]),
        )


def _drop_dead_fields() -> int:
    dropped = 0
    for fieldname in DEAD_FIELDS:
        name = frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": fieldname})
        if name:
            frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
            dropped += 1
        # Property Setters keyed to a field that no longer exists would fail
        # validate_fields_for_doctype on the next customisation save.
        frappe.db.delete("Property Setter", {"doc_type": "Employee", "field_name": fieldname})

    frappe.clear_cache(doctype="Employee")
    return dropped


def _has_column(fieldname: str) -> bool:
    """Whether `tabEmployee` still has the column.

    Columns outlive their Custom Field: on this bench several already exist with
    no Custom Field row, left behind when seal_customizations was uninstalled.
    Reading one that was properly dropped would be an OperationalError, so the
    column is checked rather than the field.
    """
    return fieldname in frappe.db.get_table_columns("Employee")
