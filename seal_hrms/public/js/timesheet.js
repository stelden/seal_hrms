// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/* global seal_hrms */

// Timesheet approval (seal_hrms timesheets/approval.py). Only where the
// company's Working Time Policy asks for it: the server says so in onload.
// Elsewhere the Timesheet form is left exactly as ERPNext ships it.

const TIMESHEET_API = "seal_hrms.seal_hrms.timesheets.approval";

// ERPNext's new Timesheet looks the person up by login (`{user_id: me}`) on load.
// On sites where Employee.user_id is at a level staff cannot read, Frappe refuses
// that filter and staff meet a Permission Error before they type anything. This
// answers exactly that lookup, for the person's own record and harmless fields,
// through seal_hrms; every other call goes to Frappe untouched.
// [unsupervised — review]: the lasting fix is deciding who may read user_id.
(function answer_own_employee_lookup() {
	const original = frappe.db.get_value;
	if (original.__seal_hrms_own_employee) return;
	const SAFE = ["name", "company", "employee_name", "department"];
	const patched = function (doctype, filters, fieldname, callback, ...rest) {
		const fields = Array.isArray(fieldname) ? fieldname : [fieldname || "name"];
		const own =
			doctype === "Employee" &&
			filters &&
			typeof filters === "object" &&
			!Array.isArray(filters) &&
			Object.keys(filters).length === 1 &&
			filters.user_id === frappe.session.user &&
			fields.every((f) => SAFE.includes(f));
		if (!own) return original.call(this, doctype, filters, fieldname, callback, ...rest);
		return frappe
			.xcall("seal_hrms.seal_hrms.task_assignment_access.my_employee_fields", { fields })
			.then((message) => {
				message = message || {};
				if (callback) callback(message);
				return { message };
			});
	};
	patched.__seal_hrms_own_employee = true;
	frappe.db.get_value = patched;
})();

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
		const onload = frm.doc.__onload || {};
		if (!onload.approval_on) return;
		seal_hrms.show_where_it_is(frm, onload.where_it_is);
		const state = frm.doc.custom_approval_state || "Not Sent";

		if (frm.doc.docstatus === 0) {
			// Submitting is approving: the server refuses a plain Submit, so do not offer one.
			if (!frm.is_dirty()) frm.page.clear_primary_action();
			if (["Not Sent", "Returned"].includes(state) && onload.can_send) {
				frm.add_custom_button(__("Send for Approval"), () =>
					act(frm, "send_for_approval")
				).addClass("btn-primary");
			}
			if (state === "Waiting for Approval") {
				frm.disable_save();
				if (onload.can_decide) {
					frm.add_custom_button(__("Approve"), () => act(frm, "approve")).addClass(
						"btn-primary"
					);
					frm.add_custom_button(__("Return"), () => return_with_reason(frm));
				}
			}
		}
	},
});

function act(frm, method, args = {}) {
	const go = () =>
		frappe
			.call({
				method: `${TIMESHEET_API}.${method}`,
				args: { name: frm.doc.name, ...args },
				freeze: true,
			})
			.then(() => frm.reload_doc());
	return frm.is_dirty() ? frm.save().then(go) : go();
}

function return_with_reason(frm) {
	frappe.prompt(
		[
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("What needs changing"),
				reqd: 1,
			},
		],
		(values) => act(frm, "return_timesheet", { reason: values.reason }),
		__("Return the timesheet"),
		__("Send")
	);
}
