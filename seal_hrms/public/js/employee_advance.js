frappe.provide("hrms.hr");
frappe.provide("erpnext.accounts.dimensions");
frappe.provide("seal_hrms.seal_hrms");

frappe.ui.form.on("Employee Advance", {
  onload: function (frm) {
    frm.fields_dict["custom_expenses"].grid.get_field("expense_type").get_query = function (doc, cdt, cdn) {
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
        'Non-Cash disbursements to <b>Employee</b> or <b>Supplier</b> require a valid <b>mobile phone</b> registered for mobile money or a <b>Bank Account</b>.', 'orange');
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

    //TODO: Enforce same department rule
    frm.set_query("custom_payee", function () {
      if (frm.doc.custom_payee_type == "Employee") {
        return {
          filters: [
            ["name", "!=", frm.doc.employee],
            ["status", "=", "active"],
            //["department", "=", frm.doc.department],
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

    //Apply default values for new Employee Advance
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
        function () {
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
            callback: function (r) {
              a_msg = !r.exc ? "Reminder created." : "Failed to create reminder.";
              a_color = !r.exc ? "green" : "red";

              frappe.show_alert({
                message: __(a_msg),
                indicator: a_color
              }, 5);
            }
          });
        },
        function () {
          //Do nothing
        }
      );
    }
  },

  employee: function (frm, cdt, cdn) {
    if (!frm.doc.employee || frm.doc.custom_direct_disbursement) return;

    const mop = frm.doc.mode_of_payment;
    const mop_type = frm.doc.custom_mode_of_payment_type;

    if (!mop || !mop_type) {
      frappe.msgprint(__("Mode of Payment is required. Please select or set a default mode of payment for <b>{0}</b>.", [frm.doc.company]));
      return;
    }

    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: 'Employee',
        name: frm.doc.employee,
        fields: [
          'employee_name',
          'full_name',
          'cell_number',
          'custom_cell_number_provider',
          'bank_name',
          'bank_ac_no',
          'custom_national_id',
          'custom_passport_no'
        ]
      },
      callback: function (r) {
        if (!r.message) return;

        const emp = r.message;
        let account_name = emp.employee_name;
        let account_no = '';
        let provider_name = '';

        const field_labels = {
          bank_name: "Bank Name",
          bank_ac_no: "Bank Account Number",
          cell_number: "Mobile Number",
          custom_cell_number_provider: "Mobile Provider",
          custom_national_id: "National ID",
          custom_passport_no: "Passport Number"
        };

        const config = {
          Bank: {
            required_fields: ['bank_name', 'bank_ac_no'],
            assign: () => {
              account_no = emp.bank_ac_no;
              provider_name = emp.bank_name;
            }
          },
          Phone: {
            required_fields: ['cell_number', 'custom_cell_number_provider'],
            assign: () => {
              account_no = emp.cell_number;
              provider_name = emp.custom_cell_number_provider;
            }
          },
          Cash: {
            required_fields: ['custom_national_id', 'custom_passport_no'], // we need at least one
            assign: () => {
              account_no = emp.custom_national_id || emp.custom_passport_no;
              provider_name = "Cashier";
            },
            require_any: true
          }
        };

        const mop_config = config[mop_type];
        if (!mop_config) {
          frappe.throw(__("<b>{0}</b> Mode of Payment Type is not supported for <b>{1}</b>", [mop_type, frm.doc.doctype]));
          return;
        }

        const missing = mop_config.required_fields.filter(f => !emp[f]);

        // For modes like "Cash" where only one is required, allow if at least one is present
        if (mop_config.require_any && missing.length === mop_config.required_fields.length) {
          const label_list = mop_config.required_fields.map(f => `<li>${field_labels[f]}</li>`).join('');
          frappe.msgprint({
            title: __("Missing Employee Details"),
            message: __("<b>{0}</b> is missing one of the following details required for <b>{1}</b> {2} disbursement:<ul>{3}</ul>", [
              emp.employee_name,
              mop_type,
              frm.doc.doctype,
              label_list
            ]),
            indicator: 'orange'
          });
          return;
        }

        // For modes where all fields must be present
        if (!mop_config.require_any && missing.length) {
          const label_list = missing.map(f => `<li>${field_labels[f]}</li>`).join('');
          frappe.msgprint({
            title: __("Missing Employee Details"),
            message: __("<b>{0}</b> is missing the following details required for <b>{1}</b> {2} disbursement:<ul>{3}</ul>", [
              emp.employee_name,
              mop_type,
              frm.doc.doctype,
              label_list
            ]),
            indicator: 'orange'
          });
          return;
        }

        // Assign and set
        mop_config.assign();
        
        frm.set_value("custom_account_name", account_name);
        frm.set_value("custom_account_no", account_no);
        frm.set_value("custom_account_provider", provider_name);
      }
    });
  },

  custom_direct_disbursement: function (frm, cdt, cdn) {
    frm.set_value("custom_payee_type", null);
    frm.set_value("custom_payee", null);

    reset_account_details(frm);

    if (!frm.doc.custom_direct_disbursement && frm.doc.employee)
      frm.set_value("employee", null);
  },

  custom_payee_type: function (frm) {
    frm.set_value("custom_payee", null);

    reset_account_details(frm);
  },

  //Set custom_preferred_payment_method, custom_account_name, custom_account_no only from Contact or Bank Account
  //No permisions required for other Employee or Supplier. Permissions required for Contact and Bank Account.
  custom_payee: function (frm) {
    if (!frm.doc.custom_direct_disbursement)
      return;

    reset_account_details(frm);

    const moptype = frm.doc.custom_mode_of_payment_type;
    const doctype = frm.doc.custom_payee_type;
    const docname = frm.doc.custom_payee;

    if (!moptype || !doctype || !docname) {
      frappe.msgprint(__("Please select Payee Type, Payee, and Mode of Payment Type."));
      return;
    }

    frappe.call({
      method: "seal_hrms.seal_hrms.api.get_payee_account_details",
      args: {
        mop_type: moptype,
        doctype: doctype,
        docname: docname
      },
      callback: function (r) {
        if (r.message) {
          frm.set_value("custom_account_name", r.message.custom_account_name);
          frm.set_value("custom_account_no", r.message.custom_account_no);
          frm.set_value("custom_account_provider", r.message.custom_account_provider);
          
          frm.refresh_fields(["custom_account_name", "custom_account_no", "custom_account_provider"]);
        }else {
          frappe.msgprint(__("<b>{0}</b> has no payment information. Please update the <b>{1}</b> record.", [docname, doctype]));
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

  // reset_account_details: function (frm) {
  //   frm.set_value("custom_account_type", null);
  //   frm.set_value("custom_account", null);

  //   frm.set_value("custom_account_name", null);
  //   frm.set_value("custom_account_no", null);
  //   frm.set_value("custom_account_provider", null);
  // }
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

function reset_account_details(frm) {
  frm.set_value("custom_account_type", null);
  frm.set_value("custom_account", null);
  frm.set_value("custom_account_name", null);
  frm.set_value("custom_account_no", null);
  frm.set_value("custom_account_provider", null);
}

