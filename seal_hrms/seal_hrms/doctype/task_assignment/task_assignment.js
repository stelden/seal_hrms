// Copyright (c) 2024, Stelden EA Ltd and contributors
// For license information, please see license.txt
frappe.ui.form.on("Task Assignment", {

    onload: function (frm) {
        frm.set_value("posting_date", frappe.datetime.nowdate());
    },

    on_submit: function(frm) {
        //alert = '';

        //Show alert of reassigned todos
        // if (frm.doc.assignment_todos.length != 0) {
        //     forEach(frm.doc.assignment_todos, function (todo) {
        //         alert += "Todo: {todo.description}\n";
        //     });

        //     alert += "Assigned/reassigned to " + frm.doc.assignee;

        //     frappe.show_alert({ message: __(alert), indicator: 'green'}, 5);
        // }
    },

    setup: function (frm) {
		frm.set_query("reference_type", "assignment_todos", function (doc, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: [
					["DocType", "issingle", "=", 0],
				],
			};
		});
	},

	refresh(frm) { 
        if (frm.doc.__islocal) {
            let message = __('You can only assign tasks to employees who are not on leave and, depending on company policy, from the same department.');
            frm.dashboard.add_comment(message, 'orange', true);
        }

        //Only allow current employee to be selected
        frm.set_query("employee", function () {
            if (!frappe.user.has_role("System Manager")) {
                return {
                    filters: [
                        ["user_id", "=", frappe.session.user],
                        ["status", "=", "active"],
                    ],
                };
            }
        });

        frm.set_query("task_assignee", function () {
            if (!frm.doc.employee) {
                frappe.msgprint(__("Please select Employee."));
                return;
            }

            if (!frm.doc.leave_application) {
                frappe.msgprint(__("Please select Employee's leave application."));
                return;
            }

            return {
                query: "seal_hrms.seal_hrms.doctype.task_assignment.task_assignment.get_assignable_employees",
                filters: filters = {
                    "employee": frm.doc.employee,
                    //"company": frm.doc.company,
                    //"department": frm.doc.department,
                    "leave_application": frm.doc.leave_application,
                }
            };
        });

        frm.set_query("leave_application", function () {
            return {
                filters: [
                    ["employee", "=", frm.doc.employee],
                    ["status", "=", "Open"],
                    ["to_date", ">=", frappe.datetime.nowdate()], //application is still valid
                ],
            };
        });
 
	},

    //load todos for the selected employee
    employee: function(frm) {
        if (frm.doc.employee) {
            frappe.call({
                method: "seal_hrms.seal_hrms.doctype.task_assignment.task_assignment.get_employee_tasks",
                args: {
                    employee: frm.doc.employee,
                },
                callback: function (r) {
                    if (r.message) {
                        frm.clear_table("assignment_todos");
                        r.message.forEach(function (todo) {
                            let row = frappe.model.add_child(frm.doc, "Task Assignment ToDo", "assignment_todos");
                            row.todo = todo.name;
                            row.reference_type = todo.reference_type;
                            row.reference_name = todo.reference_name;
                            row.description = todo.description;
                            row.priority = todo.priority;
                            row.due_date = todo.date;
                        });
                        frm.refresh_field("assignment_todos");
                    }
                },
            });
        }
    },
});