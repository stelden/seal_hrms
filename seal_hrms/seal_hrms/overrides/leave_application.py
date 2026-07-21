# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import add_years, add_days, cint, get_link_to_form, getdate, flt, nowdate, now_datetime, nowtime, today, time_diff_in_hours
import datetime
import hrms.utils as utils
import seal_hrms.seal_hrms.seal_hr_api as seal_hr_api

def on_submit(doc, method=None):
    #Task Assignment was done independently, therefore we need to reverse if the leave application is not approved
    if doc.status == "Rejected" or doc.status == "Cancelled":
        update_task_assignments(doc)

def on_cancel(doc, method=None):
    from_date = getdate(doc.from_date)
    to_date = getdate(doc.to_date)
    current_date = getdate(nowdate())

    if to_date > current_date: #Leave application is current
        update_task_assignments(doc)

def validate(doc, method=None):
    # These are application-time (creation) rules only. Guarding on is_new()
    # prevents them from re-firing on every later save (approval, cancellation,
    # edits of historical leave), which would otherwise block those updates
    # because the original posting_date is now in the past.
    if not doc.is_new():
        return

    if getdate(doc.posting_date) < getdate(today()):
        frappe.throw(_("Posting date cannot be before today."))

    min_application_days = frappe.get_value(
        "Leave Type", doc.leave_type, "custom_minimum_leave_application_days"
    )

    if min_application_days:
        if time_diff_in_hours(doc.from_date, doc.posting_date) < (min_application_days * 24):
            frappe.throw(_(f"You cannot apply for <b>{doc.leave_type}</b> less than <b>{min_application_days}</b> days before the start date."))

#TODO Test this function
def update_task_assignments(doc):
    try:
        task_assignments = frappe.get_all("Task Assignment", filters={"leave_application": doc.name, "docstatus": 1}, fields=["name", "docstatus"])
           
        for task_assignment in task_assignments:
            row = frappe.get_doc("Task Assignment", task_assignment.name)
            if row:
                #Update all ToDos
                user = seal_hr_api.get_user_for_employee(row.employee)
                if row.assignment_todos and user:
                    for todo in row.assignment_todos:
                        todo = frappe.get_doc("ToDo", todo.todo)
                        todo.allocated_to = user.name
                        todo.assigned_by = user.name
                        todo.save(ignore_permissions=True) 

                row.cancel()

                #Optionally alert the assignee
                notify_assignee = frappe.db.get_single_value("HR Settings", "send_leave_notification")
                if notify_assignee:
                    email_address = utils.get_employee_email(row.task_assignee)
                    if email_address:
                        message=f"One or more Tasks that were assigned to you by {row.employee} have been reversed because {row.employee}'s Leave Application was Rejected or Cancelled. \n\n{row.task_description} \n\n"

                        try:
                            frappe.sendmail(
                                    recipients=email_address,
                                    subject=f"Task Assignment from {row.employee}'s Leave Application",
                                    message=message
                                )
                        except frappe.OutgoingEmailError:
                            pass

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title=str(e), reference_doctype="Leave Application", reference_name=doc.name)

#TODO Test this function
# TODO Fetch from attendance
@frappe.whitelist()
def is_employee_on_leave(employee_id, from_date, to_date):

    current_date = getdate()

    leave_starts = getdate(from_date)
    leave_ends = getdate(to_date)
    
    if leave_ends < current_date: #Hack: we are not dealing with the past
        return False

    filters = {
        'status': 'Approved',
        'from_date': ('>=', leave_starts),
        'to_date': ('<=', leave_ends),
        #'to_date': ('>=', current_date), 
        'employee': employee_id
    }
    
    leave_applications = frappe.get_all('Leave Application', filters, limit=1)

    return bool(leave_applications)
 
 