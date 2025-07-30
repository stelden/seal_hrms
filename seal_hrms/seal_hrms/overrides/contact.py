import json
import frappe
from frappe import _

"""
When a Contact is updated, if it has no phone or mobile number,
checks for linked Employees and clears their custom contact fields.
Useful for maintaining data integrity when a Contact is no longer valid.
"""
def on_update(doc, method=None):
    if not doc.phone and not doc.mobile_no:
        linked_employees = frappe.get_all(
            "Employee",
            filters={"custom_contact": doc.name},
            fields=["name", "employee_name"]
        )

        if linked_employees:
            for emp in linked_employees:
                # Reload the document so changes are reflected
                frappe.get_doc("Employee", emp.name, emp.employee_name).db_set({
                    "custom_contact": "",
                    "cell_number": "",
                    "custom_cell_number_provider": ""
                }, notify=True)

            employee_list = ", ".join(f"{emp.employee_name}" for emp in linked_employees)
            frappe.msgprint(
                _("Contact {0} was linked to: {1}. The contact fields have been cleared since primary phone or mobile number is not set.").format(
                    doc.name, employee_list
                ),
                alert=True
            )
    elif doc.phone or doc.mobile_no:
        pass
        #TODO: How to reassign contact to employees if phone or mobile number is set?