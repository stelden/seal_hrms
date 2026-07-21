# Copyright (c) 2025, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.desk.calendar import get_event_conditions

@frappe.whitelist()
def get_events(start, end, filters=None):
    conditions = get_event_conditions("Leave Allocation", filters).replace("employee_name", "la.employee_name")

    return frappe.db.sql("""
        SELECT
            la.name, la.employee_name, la.from_date, la.to_date, 
            la.leave_type, lt.custom_default_color AS color, la.expired
        FROM `tabLeave Allocation` la
        LEFT JOIN `tabLeave Type` lt ON la.leave_type = lt.name
        WHERE (la.from_date <= %(end)s AND la.to_date >= %(start)s)
        AND la.expired = 0 {conditions}
    """.format(conditions=conditions), {
        "start": start,
        "end": end
    }, as_dict=True)
# def get_events(start, end, filters=None):
#     conditions = get_event_conditions("Leave Allocation", filters)

#     return frappe.db.sql("""
#         SELECT
#             name, employee_name, from_date, to_date, leave_type, expired
#         FROM `tabLeave Allocation`
#         WHERE (from_date <= %(end)s AND to_date >= %(start)s)
#         AND expired = 0 {conditions}
#     """.format(conditions=conditions), {
#         "start": start,
#         "end": end
#     }, as_dict=True)