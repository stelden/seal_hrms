frappe.provide("hrms.hr");
frappe.provide("erpnext.accounts.dimensions");
frappe.provide("seal_hrms.seal_hrms");

frappe.ui.form.on("Employee Advance", {
  onload: function(frm) {
    frm.fields_dict["custom_expenses"].grid.get_field("expense_type").get_query = function(doc, cdt, cdn) {
        return {
            filters: [
                ['Expense Claim Account', 'custom_disabled', '=', 0],
                ['Expense Claim Account', 'company', '=', frm.doc.company]
            ]
        };
    };
  },

  refresh: function (frm, cdt, cdn) {
    
    if (frm.doc.__islocal) {
      
      frm.dashboard.clear_headline();
      frm.dashboard.set_headline_alert(
          'Non-Cash disbursements to <b>Employee</b> or <b>Supplier</b> require a valid <b>mobile phone</b> registered for mobile money or a <b>Bank Account</b>.', 'orange' );
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

    frm.set_query("custom_cost_center", function () {
      return {
        filters: [
          ["is_group", "=", 0],
          ["disabled", "=", 0],
          ["company", "=", frm.doc.company],
        ],
      };
    });

    frm.set_query("custom_project", function () {
      return {
        filters: [
          ["status", "=", "Open"],
          ["is_active", "=", "Yes"],
          ["company", "=", frm.doc.company],
        ],
      };
    });

    frm.set_query("custom_payee_type", function () {
      return {
        filters: [
          ['DocType', 'name', 'in', ['Employee', 'Supplier']],
        ],
      };
    });

    frm.set_query("custom_payee", function () {
      if (frm.doc.custom_payee_type == "Employee") {
        return {
          filters: [
            ["name", "!=", frm.doc.employee],
            ["status", "=", "active"],
            //["department", "=", frm.doc.department], //Enforce same department rule
          ],
        };
      } else if (frm.doc.custom_payee_type == "Supplier") {
        return {
          filters: [
            ["disabled", "=", 0],
            ["is_frozen", "=", 0],
            ["on_hold", "=", 0],
            ["is_internal_supplier", "=", 0],
          ],
        };
      }
    });

    frm.set_query("custom_account_type", function () {
      return {
        filters: [
          ['DocType', 'name', 'in', ['Bank Account', 'Contact']],
        ],
      };
    });

    //Setup defaults if we are creating a new document
    if (frm.doc.__islocal) {
      frappe.db.get_value('Company', frm.doc.company,
        [
          'custom_auto_recover_advances_from_salary', 'custom_default_expense_claim_mode_of_payment',
        ], function (value) {

          //Apply Global Settings
          if (value) {
            frm.set_value("repay_unclaimed_amount_from_salary",
              value.custom_auto_recover_advances_from_salary);

            //Set default mode of payment (to be carried over to expense claim - mandatory)
            if (value.custom_default_expense_claim_mode_of_payment) {
              frm.set_value("mode_of_payment", value.custom_default_expense_claim_mode_of_payment); 
            }       
          }
      });
    }
    
    //Override Create Payment Entry to pass payee details
    if (frm.custom_buttons && frm.custom_buttons["Payment"]) {
      frm.custom_buttons["Payment"].unbind("click");
      frm.custom_buttons["Payment"].on("click", function () {

        let method =
          "seal_hrms.seal_hrms.overrides.employee_advance.get_payment_entry_for_employee";
        if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
          method =
            "hrms.hr.doctype.employee_advance.employee_advance.make_bank_entry";
        }
        return frappe.call({
          method: method,
          args: {
            dt: frm.doc.doctype,
            dn: frm.doc.name,
          },
          callback: function (r) {
            //TODO: Update (here?) Mode of Payment if it was not selected
            var doclist = frappe.model.sync(r.message);
            frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
          },
        });

      });
    }

    //Override Create Expense Claim to add expenses
    if (frm.custom_buttons && frm.custom_buttons["Expense Claim"]) {
      frm.custom_buttons["Expense Claim"].unbind("click");
      frm.custom_buttons["Expense Claim"].on("click", function () {
        
        return frappe.call({
          method: "seal_customizations.seal_hr.overrides.employee_advance.get_expense_claim",
          args: {
            dt: frm.doc.doctype,
            dn: frm.doc.name,
            employee_name: frm.doc.employee,
            company: frm.doc.company,
            employee_advance_name: frm.doc.name,
            posting_date: frm.doc.posting_date,
            claim_type: 'Surrender',
            paid_amount: frm.doc.paid_amount,
            claimed_amount: frm.doc.claimed_amount,
            expense_items: frm.doc.custom_expenses,
            mode_of_payment: frm.doc.mode_of_payment,
            
          },
          callback: function (r) {
            const doclist = frappe.model.sync(r.message);
            frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
          },

        });   
      });
    }
  },

  validate: function (frm) {
    if (frm.doc.custom_advance_type == "Imprest") {
      //Prefill sanctioned amount to save approvers time
      frm.doc.custom_expenses.forEach((row) => {
        row.sanctioned_amount = row.amount;
      });
		  frm.trigger("calculate_total");
    }
	},

  after_save: function (frm) {
    let today = frappe.datetime.get_today();
    let posting_date = frm.doc.posting_date;

    if (frappe.datetime.get_diff(posting_date, today) > 0) {
      let r_msg = `Reminder for ${frm.doc.doctype} ${frm.doc.name} for date ${posting_date} for purpose ${frm.doc.purpose} for amount ${frm.doc.advance_amount}`;
   
      frappe.confirm(
          __(`The posting date for this ${frm.doc.doctype} is in the future. Would you like to create a reminder to submit the document?`),
          function() {
              frappe.call({
                  method: 'frappe.client.insert',
                  args: {
                      doc: {
                          doctype: 'ToDo',
                          description: r_msg,
                          assigned_by: frappe.session.user,
                          allocated_to: frappe.session.user,
                          reference_type: frm.doc.doctype,
                          reference_name: frm.doc.name,
                          owner: frappe.session.user,
                          date: posting_date
                      }
                  },
                  callback: function(r) {
                    a_msg = !r.exc ? "Reminder created." : "Failed to create reminder.";
                    a_color = !r.exc ? "green" : "red";

                    frappe.show_alert({
                      message: __(a_msg),
                      indicator: a_color
                    }, 5);
                  }
              });
          },
          function() {
            //Do nothing
          }
      );
    }
	},

  employee: function (frm, cdt, cdn) {
    //Set custom_preferred_payment_method, custom_account_name, custom_account_no only for self
    //No permisions required for other Employee or Supplier
    if (frm.doc.employee && !frm.doc.custom_direct_disbursement) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: 'Employee',
          name: frm.doc.employee,
          fields: ['custom_preferred_payment_method', 'custom_account_name', 'custom_account_no'],
        },
        callback: function (r) {
          if (r.message) {
            let d = r.message;
            //console.log(d.custom_preferred_payment_method + ' ' + d.custom_account_name + ' ' + d.custom_account_no);
            if (d.custom_preferred_payment_method == null || d.custom_account_name == null || d.custom_account_no == null) {
              frappe.msgprint(__("<b>{0}</b> does not have a preferred payment method set up for advances. Please update the employee record.", [frm.doc.employee]));
            }
            else {
              frm.set_value("custom_payment_method", d.custom_preferred_payment_method);
              frm.set_value("custom_account_name", d.custom_account_name);
              frm.set_value("custom_account_no", d.custom_account_no);
            }
          }
        },
      });
    }
  },

  custom_direct_disbursement: function (frm, cdt, cdn) {
    frm.set_value("custom_payee_type", null);
    frm.set_value("custom_payee", null);
    frm.set_value("custom_account_type", null);
    frm.set_value("custom_account", null);
    frm.set_value("custom_payment_method", null);
    frm.set_value("custom_account_name", null);
    frm.set_value("custom_account_no", null);
    
    if (!frm.doc.custom_direct_disbursement && frm.doc.employee)
      frm.set_value("employee", null);
  },

  custom_payee_type: function(frm) {
      frm.set_value("custom_payee", null);
      frm.set_value("custom_account_type", null);
      frm.set_value("custom_account", null);
      frm.set_value("custom_payment_method", null);
      frm.set_value("custom_account_name", null);
      frm.set_value("custom_account_no", null);
  },
  
  //Set custom_preferred_payment_method, custom_account_name, custom_account_no only from Contact or Bank Account
  //No permisions required for other Employee or Supplier. Permissions required for Contact and Bank Account.
  custom_payee: function(frm) {
    if (!frm.doc.custom_direct_disbursement)
      return;

    frm.set_value("custom_account_type", null);
    frm.set_value("custom_account", null);
    //frm.set_value("custom_payment_method", null);
    frm.set_value("custom_account_name", null);
    frm.set_value("custom_account_no", null);

    if (frm.doc.custom_payee_type && frm.doc.custom_payee) {
      frappe.call({
          method: 'seal_customizations.seal_hr.seal_hr_api.get_preferred_payment_method',
          args: {
              custom_payee_type: frm.doc.custom_payee_type,
              custom_payee: frm.doc.custom_payee
          },
          callback: function(r) {
              if (r.message) {
                  let returned_doc = r.message;

                  if (returned_doc.doctype === 'Contact') {
                      frm.set_value('custom_account_type', 'Contact');
                      frm.set_value('custom_account', returned_doc.name);
                      frm.set_value("custom_payment_method", "Mpesa");
                      frm.set_value("custom_account_name", returned_doc.full_name);
                      frm.set_value("custom_account_no", returned_doc.mobile_no || returned_doc.phone);
                  } else if (returned_doc.doctype === 'Bank Account') {
                      frm.set_value('custom_account_type', 'Bank Account');
                      frm.set_value('custom_account', returned_doc.name);
                      frm.set_value("custom_payment_method", "Cheque");
                      frm.set_value('custom_account_name', returned_doc.account_name);
                      frm.set_value('custom_account_no', returned_doc.bank_account_no);
                  }
              } else {
                frappe.msgprint(__("<b>{0}</b> does not have a preferred payment method set up for advances. Please update the <b>{1}</b> record.", [frm.doc.custom_payee, frm.doc.custom_payee_type]));
              }
          },
          error: function(error) {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __(error.message)
            });
          }
      });
    }
  },

  custom_cost_center: function (frm, cdt, cdn) {
    frm.doc.custom_expenses.forEach((e) => {
      var d = locals[e.doctype][e.name];
      frappe.model.set_value(
        d.doctype,
        d.name,
        "cost_center",
        frm.doc.custom_cost_center
      );
    });
  },

  custom_project: function (frm, cdt, cdn) {
    frm.doc.custom_expenses.forEach((e) => {
      var d = locals[e.doctype][e.name];
      frappe.model.set_value(
        d.doctype,
        d.name,
        "project",
        frm.doc.custom_project
      );
    });
  },

  calculate_total: function (frm) {
		let total_amount = 0;
		let total_sanctioned_amount = 0;

		frm.doc.custom_expenses.forEach((row) => {
			total_amount += row.amount;
			total_sanctioned_amount += row.sanctioned_amount;
		});

		frm.set_value("advance_amount", total_amount);
		frm.set_value("custom_sanctioned_amount", total_sanctioned_amount);
	},
});

frappe.ui.form.on("Employee Advance Detail", {
  custom_expenses_add: function (frm, cdt, cdn) {
    var row = frappe.get_doc(cdt, cdn);
    
    //Set Cost Center and Project for each new row
    if (!row.custom_cost_center) {
      row.cost_center = frm.doc.custom_cost_center;
      //frm.refresh_field("custom_expenses");
    }

    if (!row.custom_project) {
      row.project = frm.doc.custom_project;
      //frm.refresh_field("custom_expenses");
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
					//d.cost_center = r.message.cost_center;
				}
			},
		});
	},
});



