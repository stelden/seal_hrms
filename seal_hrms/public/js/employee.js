frappe.ui.form.on("Employee"    , {
    refresh: function(frm) {
        if (!frm.doc.__islocal && (!frm.doc.custom_contact || !frm.doc.custom_salary_bank_account)) {
          let message = __('Please setup the Contact and/or Bank Account used for payments to this Employee.');
          frm.dashboard.add_comment(message, 'orange', true);
        }
    
        frm.set_query('custom_salary_bank_account', function() {
            return {
                filters: {
                party_type: 'Employee',
                party: frm.doc.name
                }
            };
        });
       
        frm.set_query("custom_contact", function(doc) {
          return {
            query: 'seal_hrms.seal_hrms.api.get_employee_contacts',
            filters: {
                email: frm.doc.prefered_email
            }
          };
        });
    },

    custom_create_salary_bank_account: function(frm) {
        create_bank_account(frm, 'employee_name', function(bank_account) {
            frm.set_value('custom_salary_bank_account', bank_account.name);
        });
    },
    
    custom_create_contact: function(frm) {
        if (!frm.doc.prefered_email) {
            frappe.msgprint(__('Please set the Preferred Email before creating a Contact.'));
            return;
        }

        create_contact(frm, 'employee_name', true, function(contact) {
            frm.set_value('custom_contact', contact.name);
        });
    },
});