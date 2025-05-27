
frappe.ui.form.on('Supplier', {

  refresh: function (frm) {

    if (!frm.doc.__islocal && (!frm.doc.custom_payment_contact || !frm.doc.custom_payment_bank_account)) {
      let message = __('Please setup the Contact and/or Bank Account used for payments to this Supplier.');
      frm.dashboard.add_comment(message, 'orange', true);
    }

    frm.set_query('custom_payment_bank_account', function () {
      return {
        filters: {
          party_type: 'Supplier',
          party: frm.doc.name
        }
      };
    });

    frm.set_query("custom_payment_contact", function(doc) {
      return {
          query: 'seal_hrms.seal_hrms.api.get_contacts_with_mobile',
          filters: {
              link_doctype: "Supplier",
              link_name: doc.name
          }
      };
    });

    //HACK: Temporary hack for ESS users: Some actions are still available even with Read Permisions only
    //No idea why we need a timeout but hey, it works!
    setTimeout(() => {
      if (!frappe.user.has_role(['Purchase Manager', 'Purchase Master Manager'])) {
        frm.remove_custom_button('Get Supplier Group Details', 'Actions');
        frm.remove_custom_button('Link with Customer', 'Actions');
      }

      if (!frappe.user.has_role('Accounts Manager', 'Accounts User')) {
        frm.remove_custom_button('Bank Account', 'Create');
        frm.remove_custom_button('Accounting Ledger', 'View');
        frm.remove_custom_button('Accounts Payable', 'View');
      }

      if (!frappe.user.has_role('Sales Manager', 'Sales Master Manager')) {
        frm.remove_custom_button('Pricing Rule', 'Create');
      }
    }, 500);

  },

  custom_create_payment_contact: function(frm) {
    create_contact(frm, 'supplier_name', '', false, function(contact) {
      frm.set_value('custom_payment_contact', contact.name);
    });
  },

  custom_create_payment_bank_account: function (frm) {
    create_bank_account(frm, 'supplier_name', function(bank_account) {
      frm.set_value('custom_payment_bank_account', bank_account.name);
    });
  },
});
