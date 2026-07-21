frappe.provide("frappe.desk");

frappe.ui.form.on("ToDo", {

    refresh: function(frm) {
        if (frm.doc.__islocal) {
            frm.set_value('assigned_by', frappe.session.user);
        }

        frm.set_query('assigned_by', function() {
            return {
                filters: {
                    name: frappe.session.user
                }
            };
        });

    }
});