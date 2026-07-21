frappe.views.calendar["Leave Allocation"] = {
    field_map: {
        id: "name",
        start: "from_date",
        end: "to_date",
        title: "employee_name",
        allDay: "allDay",
        progress: "progress",
        name: "name",
        status: 'leave_type',
        color: "color"
    },
    gantt: true,
    order_by: "from_date",
    filters: [
        {
			fieldtype: "Link",
			fieldname: "Leave Type",
            options: "Leave Type",
			label: __("Leave Type"),
		},
        {
            fieldtype: "Link",
            fieldname: "Employee",
            options: "Employee",
            label: __("Employee"),
        },
        {
            fieldtype: "Link",
            fieldname: "Company",
            options: "Company",
            label: __("Campus"),
        },
        {
            fieldtype: "Link",
            fieldname: "Department",
            options: "Department",
            label: __("Department"),
        },
    ],
    get_events_method: "seal_hrms.seal_hrms.overrides.leave_allocation.get_events",
    // color_map: {
    //     "Approved": "green",
    //     "Pending": "orange",
    //     "Rejected": "red"
    // }
};