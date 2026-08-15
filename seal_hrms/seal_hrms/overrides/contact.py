# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt
"""
Keep an employee's payment fields in step with their Contact.

The Employee fields below are declared `fetch_from` the Contact, but `fetch_from`
only resolves when the **Employee** is saved. A Contact can be edited on its own
form, or through the Employee's Edit Contact dialog, and neither saves the
Employee — so without this the number a payment rail reads
(`Employee.cell_number`) would keep whatever it was when the Employee was last
saved, while the form showed the new one. Money would follow the stale value.

So the Contact pushes its values down instead of waiting to be pulled.
"""

import frappe
from frappe import _

#: Employee field  ->  Contact field. Mirrors the `fetch_from` declarations in
#: custom/employee.json; both must change together.
FETCHED_FROM_CONTACT = {
    "cell_number": "mobile_no",
    "custom_cell_number_provider": "custom_mno",
    "custom_mobile_account_name": "full_name",
    "custom_mobile_account_no": "mobile_no",
}


def on_update(doc, method=None):
    employees = frappe.get_all(
        "Employee", filters={"custom_contact": doc.name}, pluck="name"
    )
    if not employees:
        return

    values = {
        employee_field: (doc.get(contact_field) or "")
        for employee_field, contact_field in FETCHED_FROM_CONTACT.items()
        if frappe.get_meta("Employee").has_field(employee_field)
    }

    for employee in employees:
        # `update_modified=False`: this mirrors a change made elsewhere, so it
        # should not claim to be an edit of the Employee record itself.
        frappe.db.set_value("Employee", employee, values, update_modified=False)

    if not doc.get("mobile_no") and not doc.get("phone"):
        # Worth saying out loud — the employee has just become unpayable by
        # mobile money, and nothing else on the form would show that.
        frappe.msgprint(
            _("{0} has no primary mobile number, so {1} cannot be paid by mobile money "
              "until one is set.").format(doc.name, ", ".join(employees)),
            title=_("No Mobile Number"),
            indicator="orange",
            alert=True,
        )
