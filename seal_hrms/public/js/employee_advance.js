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

      const required_by_moptype = {
        "Bank": ["Account Number", "Bank Name"],
        "Phone": ["Mobile Number", "Mobile Provider"],
        "Cash": ["National ID or KRA PIN"],
      };

      const message = __("Disbursement Requirements: ") + Object.entries(required_by_moptype)
        .map(([type, fields]) => `<b>${type}</b>: ${fields}`)
        .join(" | ");

      frm.dashboard.clear_headline();
      frm.dashboard.set_headline_alert(message, 'orange');
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

    // frm.set_query("custom_payee_type", function () {
    //   return {
    //     filters: [
    //       ['DocType', 'name', 'in', ['Employee', 'Supplier']],
    //     ],
    //   };
    // });

    //TODO: Enforce same department rule
    // frm.set_query("custom_payee", function () {
    //   if (frm.doc.custom_payee_type == "Employee") {
    //     return {
    //       filters: [
    //         ["name", "!=", frm.doc.employee],
    //         ["status", "=", "active"],
    //         //["department", "=", frm.doc.department],
    //       ],
    //     };
    //   } else if (frm.doc.custom_payee_type == "Supplier") {
    //     return {
    //       filters: [
    //         ["disabled", "=", 0],
    //         ["is_frozen", "=", 0],
    //         ["on_hold", "=", 0],
    //         ["is_internal_supplier", "=", 0],
    //       ],
    //     };
    //   }
    // });

    //Override Create Payment Entry to pass payee details
    if (frm.custom_buttons && frm.custom_buttons["Payment"]) {
      frm.custom_buttons["Payment"].unbind("click");
      frm.custom_buttons["Payment"].on("click", function () {

        let method = "seal_hrms.seal_hrms.overrides.employee_advance.get_payment_entry_for_employee";

        //TODO: Override this method to allow bank entry creation
        if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
          method = "hrms.hr.doctype.employee_advance.employee_advance.make_bank_entry";
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
          method: "seal_hrms.seal_hrms.overrides.employee_advance.get_expense_claim",
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

    if (frm.doc.custom_auto_generate_purpose) {
      let purpose = "";
      frm.doc.custom_expenses.forEach((row) => {
        purpose += `Date: ${row.expense_date}, Type: ${row.expense_type}, Description: ${row.description}, Amount: ${row.amount}\n`;
      });
      frm.set_value("purpose", purpose);
    }
  },

  employee: function (frm, cdt, cdn) {
    if (!frm.doc.employee || frm.doc.custom_direct_disbursement) {
      //reset_payee_details(frm);
      reset_expenses(frm);
      reset_account_details(frm);
      return;
    };

    const mop = frm.doc.mode_of_payment;
    const moptype = frm.doc.custom_mode_of_payment_type;

    if (!mop || !moptype) {
      frappe.msgprint(__("Mode of Payment is required. Please select or set <b>'Default Expense Claim Mode of Payment'</b> for <b>{0}</b> in Company.", [frm.doc.company]));
      return;
    }

    frappe.call({
      method: "seal_hrms.seal_hrms.api.get_payee_account_details",
      args: {
        moptype: moptype,
        doctype: "Employee",
        docname: frm.doc.employee
      },
      callback: function (r) {
        if (!r.message) return;

        const {
          custom_account_name,
          custom_account_no,
          custom_account_provider
        } = r.message;

        frm.set_value("custom_account_name", custom_account_name);
        frm.set_value("custom_account_no", custom_account_no);
        frm.set_value("custom_account_provider", custom_account_provider);
      },
      error: function (err) {
        // Handle specific error cases if needed
        if (err.exc_type === 'ValidationError') {
          reset_payee_details(frm);
          reset_account_details(frm);

          frappe.msgprint({
            title: __('Missing Employee Details'),
            message: err.message,
            indicator: 'orange'
          });
        } else {
          frappe.msgprint(__("Error fetching employee account details"));
        }
      }
    });
  },

  custom_advance_type: function (frm) {
    //reset_payee_details(frm);
    reset_expenses(frm);
    reset_account_details(frm);
    
    if (frm.doc.custom_advance_type == "Salary Advance")
      frm.set_value("custom_auto_generate_purpose", 0);
    else if (frm.doc.custom_advance_type == "Imprest")
      frm.set_value("custom_auto_generate_purpose", 1);

    frm.trigger("employee");
  },

  // custom_direct_disbursement: function (frm, cdt, cdn) {
  //   frm.set_value("custom_payee_type", null);
  //   frm.set_value("custom_payee", null);

  //   reset_account_details(frm);

  //   if (!frm.doc.custom_direct_disbursement && frm.doc.employee)
  //     frm.set_value("employee", null);
  // },

  // custom_payee_type: function (frm) {
  //   frm.set_value("custom_payee", null);

  //   reset_account_details(frm);
  // },

  // custom_payee: function (frm) {
  //   if (!frm.doc.custom_direct_disbursement)
  //     return;

  //   if (!frm.doc.custom_payee_type || !frm.doc.custom_payee) {
  //     reset_account_details(frm);
  //     return;
  //   }

  //   reset_account_details(frm);

  //   const moptype = frm.doc.custom_mode_of_payment_type;
  //   const doctype = frm.doc.custom_payee_type;
  //   const docname = frm.doc.custom_payee;

  //   if (!moptype || !doctype || !docname) {
  //     frappe.msgprint(__("Please select Payee Type, Payee, and Mode of Payment Type."));
  //     return;
  //   }

  //   frappe.call({
  //     method: "seal_hrms.seal_hrms.api.get_payee_account_details",
  //     args: {
  //       moptype: moptype,
  //       doctype: doctype,
  //       docname: docname
  //     },
  //     callback: function (r) {
  //       if (r.message) {
  //         frm.set_value("custom_account_name", r.message.custom_account_name);
  //         frm.set_value("custom_account_no", r.message.custom_account_no);
  //         frm.set_value("custom_account_provider", r.message.custom_account_provider);

  //         frm.refresh_fields(["custom_account_name", "custom_account_no", "custom_account_provider"]);
  //       } else {
  //         frappe.msgprint(__("<b>{0}</b> has no payment information. Please update the <b>{1}</b> record.", [docname, doctype]));
  //       }
  //     },
  //     error: function (error) {
  //       frappe.msgprint({
  //         title: __('Error'),
  //         indicator: 'red',
  //         message: __(error.message)
  //       });
  //     }
  //   });
  // },

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

// function reset_payee_details(frm) {
//   frm.set_value("custom_direct_disbursement", 0);
//   frm.set_value("custom_payee_type", null);
//   frm.set_value("custom_payee", null);
// }

function reset_expenses(frm) {
  frm.set_value("custom_expenses", []);
  frm.set_value("advance_amount", 0);
  frm.set_value("custom_sanctioned_amount", 0);
  frm.set_value("claimed_amount", 0);
  frm.set_value("paid_amount", 0);
  frm.set_value("pending_amount", 0);
  frm.set_value("return_amount", 0);
  frm.set_value("custom_account_balance", 0);
  frm.set_value("purpose", null);
}

function reset_account_details(frm) {
  frm.set_value("custom_account_name", null);
  frm.set_value("custom_account_no", null);
  frm.set_value("custom_account_provider", null);
}

