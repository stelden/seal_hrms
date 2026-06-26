// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Expense Requisition Status"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Approved", "Disbursed", "Surrendered", "Returned", "Closed"].join("\n"),
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "only_outstanding",
			label: __("Only With Outstanding Balance"),
			fieldtype: "Check",
		},
	],
};
