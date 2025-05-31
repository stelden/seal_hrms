// Copyright (c) 2025, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Plan', {
	refresh: function(frm) {
		frm.set_query("employee", () => {
            return {
                filters: {
                    status: "Active",
                    company: frm.doc.company
                }
            };
        });

        // Filter leave period: active, matching company, and in future
        frm.set_query("leave_period", () => {
            return {
                filters: {
                    is_active: 1,
                    company: frm.doc.company,
                    to_date: [">", frappe.datetime.now_date()]
                }
            };
        });

		if (frm.doc.employee) {
			set_leave_type_filter(frm);
		}
	},
	company(frm) {
        frm.set_value("employee", null);
        frm.set_value("leave_period", null);
    },

    leave_plan_slots_add: function(frm, cdt, cdn) {
		frm.set_query('leave_type', 'leave_plan_slots', function(doc, cdt, cdn) {
			return {
				filters: [
					['custom_is_plannable', '=', 1]
				]
			};
		});

		const row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "slot_status", "Open");

	},
});

frappe.ui.form.on('Leave Plan Slot', {
	from_date: update_slot_days,
    to_date: update_slot_days
});

function update_slot_days(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.from_date && row.to_date) {
        frappe.call({
            method: "seal_hrms.seal_hrms.doctype.leave_plan.leave_plan.calculate_slot_days",
            args: {
                employee: frm.doc.employee,
                from_date: row.from_date,
                to_date: row.to_date
            },
            callback: function(r) {
                if (r.message !== undefined) {
                    frappe.model.set_value(cdt, cdn, "days", r.message);
                }
            }
        });
    }
}