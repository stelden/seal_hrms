# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import seal_hrms.seal_hrms.seal_hr_api as seal_hr_api
import seal_hrms.seal_hrms.overrides.leave_application as leave_application

class TaskAssignment(Document):
    
    def validate(self):
        assignee_is_on_leave = leave_application.is_employee_on_leave(self.task_assignee, self.leave_from, self.leave_to)
        
        if assignee_is_on_leave:
            frappe.throw(_(f"Cannot assign tasks. <b>{self.task_assignee_name}</b> is/will be on leave betweeen <b>{self.leave_from}</b> and <b>{self.leave_to}</b>. Pick another assignee or change the leave dates."))

    #TODO Test this function
    def on_submit(self):
        employee_user = seal_hr_api.get_user_for_employee(self.employee)
        assignee_user = seal_hr_api.get_user_for_employee(self.task_assignee)
    
        for task in self.assignment_todos:
            if not employee_user or not assignee_user:
                frappe.log_error(
                    title="Task Assignment: missing linked user",
                    message=_("Cannot create or reassign ToDo. No user is linked to Employee or Assignee."),
                    reference_doctype="Task Assignment",
                    reference_name=self.name,
                )
                continue

            if task.todo: #if there's a todo, update and reallocate
                todo = frappe.get_doc('ToDo', task.todo)
                todo.description = task.description
                todo.priority = task.priority
                todo.date = task.due_date
                todo.reference_type = task.reference_type
                todo.reference_name = task.reference_name
                
                todo.allocated_to = assignee_user.name
                todo.assigned_by = employee_user.name
                
                todo.save(ignore_permissions=True)
                
            else:#if there's a new task, create todo
                todo = frappe.new_doc('ToDo')
                todo.status = 'Open'
                todo.priority = task.priority
                todo.description = task.description
                todo.allocated_to = assignee_user.name
                todo.assigned_by = employee_user.name

                if task.due_date: 
                    todo.date = task.due_date
                if task.reference_type:
                    todo.reference_type = task.reference_type
                if task.reference_name:
                    todo.reference_name = task.reference_name
                
                todo.insert(ignore_permissions=True)

        self.notify_task_assignee(self)

    def notify_task_assignee(self, doc):
        assignor = frappe.get_doc('Employee', doc.employee)
        assignee = frappe.get_doc('Employee', doc.task_assignee)

        if not assignor or not assignee:
            frappe.throw("Task assignor and assignee are required.")

        assignor_name = assignor.employee_name
        assignor_email = assignor.user_id

        assignee_name = assignee.employee_name
        assignee_email = assignee.user_id

        if assignee_email:
            # Fetch TODOs assigned to the user
            todos = frappe.get_all("ToDo", filters={"allocated_to": assignee_email, "assigned_by": assignor_email,"status": "Open"}, fields=["*"])

            if todos:
                email_subject = "Task Assignment by " + assignor_name
                email_content = f"Dear {assignee_name},\n\nI have allocated the following tasks to you via {doc.name}:\n\n"
                
                for todo in todos:
                    email_content += f"- {todo['description']} - Due On: {todo['date']} - Priority: {todo['priority']}\n"

                email_content += "\nPlease remember to complete the tasks on time."

                # Send the email
                frappe.sendmail(
                    recipients=assignee_email,
                    subject=email_subject,
                    message=email_content,
                    reference_doctype=doc.doctype,
                    reference_name=doc.name
                )

@frappe.whitelist()
def get_employee_tasks(employee):
    if not employee:
        frappe.throw("Employee is required.")

    # Fetch the user ID associated with the employee
    user_id = frappe.db.get_value('Employee', employee, 'user_id')

    if not user_id:
        frappe.throw(f"No user associated with employee {employee}.")
    
    todos = frappe.get_list('ToDo', 
        filters={
            'allocated_to': user_id,
            'status': 'Open'
        },
        fields=['*'],
        order_by='date asc'
    )
    
    return todos

@frappe.whitelist()
def get_assignable_employees(doctype, txt, searchfield, start, page_len, filters):
    employee = filters.get('employee')
    leave_application = filters.get('leave_application')
    
    if not employee or not leave_application:
        return []
    
    company, department = frappe.get_value('Employee', employee, ['company', 'department'])
    
    restrict_task_assignment = frappe.get_value('Company', company, 'custom_restrict_task_assignment')

    leave_app = frappe.get_doc('Leave Application', leave_application)
    from_date = leave_app.from_date
    to_date = leave_app.to_date

    employee_filters = {
        'company': company,
        'status': 'Active',
        'name': ['!=', employee]
    }

    #if the company restricts task assignment to employees in the same department
    if restrict_task_assignment:
        employee_filters['department'] = department

    employees = frappe.get_all('Employee', fields=['name', 'employee_name'], filters=employee_filters, ignore_permissions=True)

    assignable_employees = []

    for emp in employees:
        # Query Leave Application to check if the employee is on approved leave within the given date range
        leave_exists = frappe.db.sql("""
            SELECT name FROM `tabLeave Application`
            WHERE employee = %s
            AND status = 'Approved'
            AND (from_date <= %s AND to_date >= %s)  -- Overlapping leave condition
            """, (emp.name, to_date, from_date))

        # If no overlapping leave is found, add the employee to the assignable list
        if not leave_exists:
            assignable_employees.append([emp.name, emp.employee_name])

    # frappe.errprint(len(assignable_employees))

    return assignable_employees

