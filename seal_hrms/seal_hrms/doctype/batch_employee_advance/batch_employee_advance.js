// Copyright (c) 2024, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Employee Advance", {
    onload: function (frm) {
        frm.fields_dict["expenses"].grid.get_field("expense_type").get_query = function (doc, cdt, cdn) {
            return {
                filters: [
                    ['Expense Claim Account', 'custom_disabled', '=', 0],
                    ['Expense Claim Account', 'company', '=', frm.doc.company]
                ]
            };
        };
    },

    refresh: function (frm, cdt, cdn) {
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

        frm.set_query("cost_center", function () {
            return {
                filters: [
                    ["is_group", "=", 0],
                    ["disabled", "=", 0],
                    ["company", "=", frm.doc.company],
                ],
            };
        });

        frm.set_query("project", function () {
            return {
                filters: [
                    ["status", "=", "Open"],
                    ["is_active", "=", "Yes"],
                    ["company", "=", frm.doc.company],
                ],
            };
        });

        if (frm.doc.__islocal) {
            frappe.db.get_value('Company', frm.doc.company,
            [
            'custom_auto_recover_advances_from_salary',
            'custom_default_expense_claim_mode_of_payment',
            ], function (settings) {
                if (settings) {
                    frm.set_value("repay_unclaimed_amount_from_salary", settings.custom_auto_recover_advances_from_salary || 0);
                    frm.set_value("mode_of_payment", settings.custom_default_expense_claim_mode_of_payment || null);
                }
            });
        }
    },

    cost_center: function (frm, cdt, cdn) {
        frm.doc.expenses.forEach((e) => {
            var d = locals[e.doctype][e.name];
            frappe.model.set_value(
                d.doctype,
                d.name,
                "cost_center",
                frm.doc.cost_center
            );
        });
    },

    project: function (frm, cdt, cdn) {
        frm.doc.expenses.forEach((e) => {
            var d = locals[e.doctype][e.name];
            frappe.model.set_value(
                d.doctype,
                d.name,
                "project",
                frm.doc.project
            );
        });
    },

    validate: function (frm) {
        if (frm.doc.auto_generate_purpose) {
            let purpose = "";
            frm.doc.expenses.forEach((row) => {
                purpose += `Date: ${row.expense_date}, Type: ${row.expense_type}, Description: ${row.description}, Amount: ${row.amount}\n`;
            });
            frm.set_value("purpose", purpose);
        }
    },
});

frappe.ui.form.on("Employee Advance Detail", {
    expenses_add: function (frm, cdt, cdn) {
      var row = frappe.get_doc(cdt, cdn);
      
      //Set Cost Center and Project for each new row
      if (!row.cost_center) {
        
        row.cost_center = frm.doc.cost_center;
        frm.refresh_field("expenses");
      }
  
      if (!row.project) {
        row.project = frm.doc.project;
        frm.refresh_field("expenses");
      }
    },
  
    expense_type: function (frm, cdt, cdn) {
          var d = locals[cdt][cdn];
          if (!frm.doc.company) {
              d.expense_type = "";
              frappe.msgprint(__("Please set the Company"));
              this.frm.refresh_fields();
              return;
          }
  
          if (!d.expense_type) {
              return;
          }
          return frappe.call({
              method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim_account_and_cost_center",
              args: {
                  expense_claim_type: d.expense_type,
                  company: frm.doc.company,
              },
              callback: function (r) {
                  if (r.message) {
                      d.default_account = r.message.account;
                      d.cost_center = r.message.cost_center;
                  }
              },
          });
      },
});

frappe.ui.form.on('Batch Employee Advance Employee', {
    employee: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.employee) return;
        
        // Get employee details and set account fields
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Employee',
                fieldname: ['employee_name', 'bank_ac_no', 'bank_name', 'cell_number', 
                           'custom_cell_number_provider', 'custom_national_id'],
                filters: {name: row.employee}
            },
            callback: function(r) {
                if (r.message) {
                    const emp = r.message;
                    let account_no = '';
                    let provider = '';
                    
                    // Set fields based on payment type
                    if (frm.doc.mode_of_payment_type === 'Bank') {
                        account_no = emp.bank_ac_no;
                        provider = emp.bank_name;
                    } else if (frm.doc.mode_of_payment_type === 'Phone') {
                        account_no = emp.cell_number;
                        provider = emp.custom_cell_number_provider;
                    } else if (frm.doc.mode_of_payment_type === 'Cash') {
                        account_no = emp.custom_national_id;
                        provider = 'Cashier';
                    }
                    
                    frappe.model.set_value(cdt, cdn, {
                        account_name: emp.employee_name,
                        account_no: account_no,
                        account_provider: provider
                    });
                }
            }
        });
    },

    employees_add: function(frm) {
        frm.fields_dict['employees'].grid.get_field('employee').get_query = function() {
            let filters = [
                ["Employee", "status", "=", "Active"]
            ];
            
            // Add filters based on payment type
            if (frm.doc.mode_of_payment_type === 'Bank') {
                filters.push(
                    ["Employee", "bank_ac_no", "!=", ""],
                    ["Employee", "bank_name", "!=", ""]
                );
            } 
            else if (frm.doc.mode_of_payment_type === 'Phone') {
                filters.push(
                    ["Employee", "cell_number", "!=", ""],
                    ["Employee", "custom_cell_number_provider", "!=", ""]
                );
            } 
            else if (frm.doc.mode_of_payment_type === 'Cash') {
                filters.push(
                    ["Employee", "custom_national_id", "!=", ""],
                );
            }
            else {
                // For unsupported payment types, show no employees
                filters.push(["Employee", "name", "=", ""]);
            }
            
            return { filters: filters };
        };
    }
});