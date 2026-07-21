# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.doctype.todo.todo import ToDo

#Show only My ToDos and Assigned To Me ToDos
def get_permission_query_conditions(user=None):
    user = frappe.db.escape(user or frappe.session.user)  # escape -> quoted, injection-safe
    return (
        f"(`tabToDo`.owner = {user} or `tabToDo`.assigned_by = {user}) "
        f"or `tabToDo`.allocated_to = {user}"
    )