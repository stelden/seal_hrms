// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Time Off in Lieu"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{ fieldname: "employee", label: __("Employee"), fieldtype: "Link", options: "Employee" },
		{
			fieldname: "only_with_time_left",
			label: __("Only people with time left"),
			fieldtype: "Check",
			default: 1,
		},
	],
};
