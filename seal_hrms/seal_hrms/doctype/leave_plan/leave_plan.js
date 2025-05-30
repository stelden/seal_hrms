// Copyright (c) 2025, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Plan', {
	refresh: function(frm) {
		// Set query for Leave Period
		frm.set_query('leave_period', function() {
			return {
				filters: [
					['to_date', '>=', frappe.datetime.get_today()]
					['is_active', '=', 1]
				]
			};
		});

		if (frm.doc.employee) {
			set_leave_type_filter(frm);
		}
	},
	employee: function(frm) {
		if (frm.doc.employee) {
			set_leave_type_filter(frm);
		} else {
            if (frm.fields_dict['leave_plan_slots']) {
                frm.fields_dict['leave_plan_slots'].grid.update_docfield_property(
                    'leave_type', 'only_select', false
                );
                 frm.fields_dict['leave_plan_slots'].grid.update_docfield_property(
                    'leave_type', 'get_query', null
                );
            }
		}
	}
});

frappe.ui.form.on('Leave Plan Slot', {
	// If you need to set the filter specifically when a new row is added:
	leave_plan_slots_add: function(frm, cdt, cdn) {
		set_leave_type_filter_for_row(frm, cdt, cdn);
	},
});

function set_leave_type_filter(frm) {
	if (frm.fields_dict['leave_plan_slots']) {
		frm.set_query('leave_type', 'leave_plan_slots', function(doc, cdt, cdn) {
			return {
				filters: [
					['custom_is_plannable', '=', 1]
				]
			};
		});
	}
}

// // Helper function to set query for a specific row, useful if called from row-specific events
// // This might be redundant if the main grid set_query works effectively for all rows.
// function set_leave_type_filter_for_row(frm, cdt, cdn) {
//     let row = locals[cdt][cdn];
//     frm.fields_dict['leave_plan_slots'].grid.update_docfield_property(
//         'leave_type', 'get_query', function() {
//             return {
//                 filters: [
//                     ['custom_is_plannable', '=', 1]
//                 ]
//             };
//         },
//         cdn // Apply to specific row
//     );
//     // It's often better to set it on the grid level as in set_leave_type_filter
//     // This ensures consistency. The above is an example if row-specific dynamic query is needed.
//     // For this particular filter (is_plannable), the grid-level set_query is usually sufficient.
// }
