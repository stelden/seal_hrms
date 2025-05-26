function create_contact(frm, name_field, disable_name, callback) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the {0} before creating a contact.', [frm.doc.doctype]));
        return;
    }

    let contact_name = frm.doc[name_field] || frm.doc.name;

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
        // Allow +254, 254, 0 or no prefix (like 712345678)
        const phone_regex = /^(?:\+?254|0)?(7\d{8}|1\d{8})$/;
        if (!phone_regex.test(values.phone_number)) {
            frappe.msgprint(__('Please enter a valid Kenyan phone number like 0700123456 or 25400123456.'));
            return;
        }

        // Normalize before checking
        const normalized_phone_no = normalize_contact_phone(values.phone_number);

        // Server check for duplicates
        frappe.call({
            method: 'seal_hrms.seal_hrms.api.contact_exists',
            args: {
                phone_number: normalized_phone_no
            },
            callback: function (r) {
                if (r.message === true) {
                    frappe.msgprint(__('A contact with this phone number already exists.'));
                    return;
                }

                // Proceed to create contact
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Contact',
                            first_name: values.contact_name,
                            is_billing_contact: 1,
                            is_primary_contact: 1,
                            links: [{
                                link_doctype: frm.doc.doctype,
                                link_name: frm.doc.name
                            }],
                            phone_nos: [{
                                phone: normalized_phone_no,
                                is_primary_mobile_no: 1
                            }],
                        }
                    },
                    callback: function (r) {
                        if (r.message) {
                            if (typeof callback === 'function') {
                                callback(r.message);
                            }
                        } else {
                            frappe.msgprint(__('Failed to create Contact for {0}.', [frm.doc.doctype]));
                        }
                    }
                });
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
                method: 'seal_hrms.seal_hrms.api.bank_account_exists',
                args: {
                    account_number: values.account_number,
                },
                callback: function (r) {
                    if (r.message === true) {
                        frappe.msgprint(__('A bank account with this account number already exists.'));
                        return;
                    }
                    
                    frappe.call({
                        method: 'frappe.client.insert',
                        args: {
                            doc: {
                                doctype: 'Bank Account',
                                account_name: values.account_name,
                                party_type: frm.doc.doctype,
                                party: frm.doc.name,
                                bank_account_no: values.account_number,
                                bank: values.bank,
                                iban: values.iban
                            }
                        },
                        callback: function (r) {
                            if (r.message) {
                                if (typeof callback === 'function') {
                                    callback(r.message);
                                }
                            } else {
                                frappe.log_error(error, __('Failed to create Bank Account for {0}.', [frm.doc.doctype]));
                                frappe.msgprint(__('Failed to create Bank Account for {0}.', [frm.doc.doctype]));
                            }
                        }
                    });
                }
            });
        },
        __('Enter Bank Account Information'),
        __('Create'));
}

function get_bank_account(frm, field_name, callback) {
    if (frm.doc[field_name] == null)
      return;

    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: 'Bank Account',
        name: frm.doc[field_name],
        fields: ['account_name', 'bank_account_no'],
        //ignore_permissions: true,
      },
      callback: function (r) {
        console.assert(r.message, "Bank Account not found");
        if (r.message) {
          let d = r.message;

          if (d.account_name == null || d.bank_account_no == null) {
            frappe.msgprint(__("<b>{0}</b> does not have an Bank Account Name or Bank Account Number set up for payments. Please update the Bank Account for the {1}. Enter the {1}'s name as Bank Account Name and specify a Bank Account Number.", [frm.doc.name], [frm.doc.doctype]));
          }
          else {
            if (typeof callback === 'function') {
                callback(r.message);
            }
          }
        }
      },
    });
}

function get_contact(frm, field_name, callback) {
    if (frm.doc[field_name] == null)
      return;

    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: 'Contact',
        name: frm.doc[field_name],
        fields: ['first_name', 'mobile_no'],
        //ignore_permissions: true,
      },
      callback: function (r) {
        console.assert(r.message, "Contact not found");
        if (r.message) {
          let d = r.message;

          if (d.first_name == null || d.mobile_no == null) {
            frappe.msgprint(__("<b>{0}</b> does not have a name or mobile number set up for payments. Please update the Contact for the {1}. Enter the {1}'s name as First Name and specify a Primary Mobile Number.", [frm.doc.name], [frm.doc.doctype]));
          }
          else {
            if (typeof callback === 'function') {
                callback(r.message);
            }
          }
        }
      },
    });
  }

function normalize_contact_phone(input) {
    let number = input.replace(/\D/g, ''); // remove all non-digits

    if (number.startsWith('0')) {
        number = '+254' + number.slice(1);
    } else if (number.startsWith('254')) {
        number = '+254' + number.slice(3);
    } else if (!number.startsWith('254') && number.length === 9) {
        number = '+254' + number;
    } else if (number.startsWith('+254')) {
        number = '+' + number;
    }

    return number;
}