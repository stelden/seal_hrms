function create_contact(frm, name_field, email_field, disable_name, callback) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the {0} before creating a contact.', [frm.doc.doctype]));
        return;
    }

    let contact_name = frm.doc[name_field] || frm.doc.name;
    let contact_email = ''
    
    if (email_field && frm.doc[email_field])
        contact_email = frm.doc[email_field];

    frappe.prompt([
        {
            fieldtype: 'Data',
            label: 'Contact Name',
            fieldname: 'contact_name',
            reqd: 1,
            read_only: disable_name,
            default: contact_name
        },
        {
            fieldtype: 'Data',
            label: 'Primary Mobile Number',
            fieldname: 'phone_number',
            reqd: 1
        }
    ],
    function (values) {
        frappe.call({
            method: 'seal_hrms.seal_hrms.api.create_contact',
            args: {
                ref_doctype: frm.doc.doctype,
                ref_name: frm.doc.name,
                contact_name: values.contact_name,
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
    __('Enter Primary Mobile Number'),
    __('Create'));
}

function create_bank_account(frm, name_field, callback) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the {0} before creating a bank account.', [frm.doc.doctype]));
        return;
    }

    let account_name = frm.doc[name_field] || frm.doc.name;

    frappe.prompt([
        {
            fieldtype: 'Data', label: 'Account Name', fieldname: 'account_name', reqd: 1, read_only: 1, default: account_name
        },
        {
            fieldtype: 'Data', label: 'Account Number', fieldname: 'account_number', reqd: 1
        },
        {
            fieldtype: 'Link', label: 'Bank', fieldname: 'bank', options: 'Bank', reqd: 1
        },
        {
            fieldtype: 'Data', label: 'IBAN', fieldname: 'iban', reqd: 0
        }
    ],
    function (values) {
        frappe.call({
            method: 'seal_hrms.seal_hrms.api.create_bank_account',
            args: {
                ref_doctype: frm.doc.doctype,
                ref_name: frm.doc.name,
                account_name: values.account_name,
                account_number: values.account_number,
                bank: values.bank,
                iban: values.iban
            },
            callback: function (r) {
                if (r.message && typeof callback === 'function') {
                    callback(r.message);
                }
            }
        });
    },
    __('Enter Bank Account Information'),
    __('Create'));
}