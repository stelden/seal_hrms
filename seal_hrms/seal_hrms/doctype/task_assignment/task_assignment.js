// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt
frappe.ui.form.on("Task Assignment", {

    onload: function (frm) {
        if (frm.is_new() && !frm.doc.posting_date) {
            frm.set_value("posting_date", frappe.datetime.nowdate());
        }
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
		// A different stand-in for one task: the same colleagues who could cover the whole handover.
		frm.set_query("task_assignee", "assignment_todos", function () {
			return {
				query: "seal_hrms.seal_hrms.doctype.task_assignment.task_assignment.get_assignable_employees",
				filters: {
					employee: frm.doc.employee,
					leave_application: frm.doc.leave_application,
				},
			};
		});
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
            let message = __('Pick someone who is not on leave themselves over the same dates. Your work moves to them when your leave starts, and comes back when you return.');
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
                    ["status", "in", ["Open", "Approved"]],
                    ["docstatus", "<", 2],
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