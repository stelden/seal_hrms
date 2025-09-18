frappe.ui.form.on("Company", {
    refresh: function(frm) {
        
        frm.set_query('default_expense_claim_payable_account', function() {
            return {
                filters: {
                    account_type: 'Payable',
                    company: frm.doc.name,
					is_group: 0,
                    disabled: 0,
                }
            };
        });

        frm.set_query('default_employee_advance_account', function() {
            return {
                filters: {
                    account_type: 'Current Asset',
                    company: frm.doc.name,
					is_group: 0,
                    disabled: 0,
                }
            };
        });

        frm.set_query('default_payroll_payable_account', function() {
            return {
                filters: {
                    account_type: 'Payable',
                    company: frm.doc.name,
					is_group: 0,
                    disabled: 0,
                }
            };
        });

        frm.set_query('custom_default_expense_claim_mode_of_payment', function() {
            return {
                filters: {
                    custom_use: 'Payments',
                    enabled: 1,
                }
            };
        });

        frm.set_query('custom_salary_component_for_recovery', function() {
            return {
                filters: {
                    disabled: 0,
                    type: "Deduction",
                }
            };
        });
    },

    validate: function(frm) {
        if ((frm.doc.custom_auto_recover_advances_from_salary || frm.doc.custom_block_new_advances) && (frm.doc.custom_max_advance_days > 360)) {
            frappe.msgprint(__('Maximum Advance Days must less than 360 days.'));
            frappe.validated = false;
        }
    }
});