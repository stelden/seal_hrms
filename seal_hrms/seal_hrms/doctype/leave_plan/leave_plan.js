// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Plan", {
	refresh(frm) {
		frm.set_query("planning_cycle", () => ({
			filters: { status: "Open" },
		}));

		frm.set_query("employee", () => ({
			filters: {
				status: "Active",
				company: frm.doc.company || "",
			},
		}));

		frm.set_query("leave_type", "leave_plan_slots", () => ({
			filters: { custom_is_plannable: 1 },
		}));

		frm.set_query("coverage_assignee", "leave_plan_slots", () => ({
			filters: {
				status: "Active",
				company: frm.doc.company || "",
				name: ["!=", frm.doc.employee || ""],
			},
		}));

		if (frm.doc.docstatus === 1 && frm.doc.status !== "Fully Applied") {
			frm.add_custom_button(__("Cancel Plan"), () => prompt_cancel_plan(frm), __("Actions"));
		}
	},

	planning_cycle(frm) {
		if (!frm.doc.planning_cycle) return;
		frm.set_value("employee", null);
	},
});

frappe.ui.form.on("Leave Plan Slot", {
	from_date: update_slot_days,
	to_date: update_slot_days,
});

function update_slot_days(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.from_date || !row.to_date || !frm.doc.employee) return;
	frappe.call({
		method: "seal_hrms.seal_hrms.leave_planning.slots.calculate_slot_days",
		args: {
			employee: frm.doc.employee,
			from_date: row.from_date,
			to_date: row.to_date,
		},
		callback(r) {
			if (r.message !== undefined) {
				frappe.model.set_value(cdt, cdn, "days", r.message);
			}
		},
	});
}

function prompt_cancel_plan(frm) {
	frappe.call({
		method: "seal_hrms.seal_hrms.leave_planning.endpoints.plan.can_cancel_plan",
		args: { plan: frm.doc.name },
		callback(r) {
			if (!r.message) return;
			if (!r.message.can_cancel) {
				frappe.msgprint({
					title: __("Cannot Cancel Leave Plan"),
					message: r.message.reason,
					indicator: "red",
				});
				return;
			}
			frappe.confirm(__("Cancel this Leave Plan?"), () => {
				frappe.call({
					method: "seal_hrms.seal_hrms.leave_planning.endpoints.plan.cancel_plan",
					args: { plan: frm.doc.name },
					callback() { frm.reload_doc(); },
				});
			});
		},
	});
}
