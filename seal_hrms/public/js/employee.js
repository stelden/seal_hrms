frappe.ui.form.on("Employee"    , {
    refresh: function(frm) {
        const fullName = frm.doc.employee_name;

        let pending_issues = [];
        frm.dashboard.clear_headline();

        if (!frm.doc.__islocal && !frm.doc.custom_contact) {
            pending_issues.push(__('Contact used for Email communications'));
        }

        if (!frm.doc.__islocal && !frm.doc.custom_salary_bank_account) {
            pending_issues.push(__(`Bank Account used for Bank payments to ${fullName}`));
        }

        if (pending_issues.length > 0) {
            const message = `
                ${__('Please setup the following:')}
                <br>- ${pending_issues.join('<br>- ')}
            `;
            frm.dashboard.set_headline_alert(message, 'orange');
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

        frappe.call({
            method: "seal_hrms.seal_hrms.api.contact_exists",
            args: {
                phone_number: frm.doc.cell_number,
                email_id: frm.doc.prefered_email
            },
            callback: function(r) {
                if (!r.exc) {
                    const contactExists = !!r.message;

                    frm.toggle_display("custom_create_contact", !contactExists && !frm.doc.user_id && !frm.doc.__islocal);
                    frm.toggle_display('custom_update_contact', contactExists);
                }
            }
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

        create_contact(frm, 'employee_name', 'prefered_email', true, function(contact) {
            frm.set_value('custom_contact', contact.name);
        });
    },

    custom_update_contact: function(frm) {
        update_contact(frm, 'employee_name', 'prefered_email', function(contact) {
            frm.set_value('custom_contact', contact.name);
            frm.set_value('cell_number', contact.mobile_no);
            frm.save(); 
        });
    }
});

//TODO Move to seal_common
function update_contact(frm, name_field, email_field, callback) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the {0} before updating a contact.', [frm.doc.doctype]));
        return;
    }

    let contact_email = ''
    
    if (email_field && frm.doc[email_field])
        contact_email = frm.doc[email_field];

    frappe.prompt([
        {
            fieldtype: 'Data',
            label: 'Primary Mobile Number',
            fieldname: 'phone_number',
            reqd: 1
        }
    ],
    function (values) {
        frappe.call({
            method: 'seal_hrms.seal_hrms.api.update_contact',
            args: {
                phone_number: values.phone_number,
                email_id: contact_email
            },
            callback: function (r) {
                if (r.message && typeof callback === 'function') {
                    callback(r.message);
                }
            }
        });
    },
    __('Update Primary Mobile Number'),
    __('Update'));
}