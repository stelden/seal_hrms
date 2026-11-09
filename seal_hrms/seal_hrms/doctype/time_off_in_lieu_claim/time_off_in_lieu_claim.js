// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// The buttons follow the claim's status and who is looking (set by the server
// in onload); every action goes through an endpoint that checks again.

const TOIL_API = "seal_hrms.seal_hrms.toil.approval";

frappe.ui.form.on("Time Off in Lieu Claim", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			frappe.call("seal_hrms.seal_hrms.task_assignment_access.my_employee").then((r) => {
				if (r.message) frm.set_value("employee", r.message);
			});
		}
	},

	refresh(frm) {
		show_where_it_is(frm);
		if (frm.is_new()) return;
		const onload = frm.doc.__onload || {};

		if (
			frm.doc.docstatus === 0 &&
			["Draft", "Returned"].includes(frm.doc.status) &&
			onload.can_send
		) {
			frm.add_custom_button(__("Send for Approval"), () =>
				act(frm, "send_for_approval")
			).addClass("btn-primary");
		}
		if (
			frm.doc.docstatus === 0 &&
			frm.doc.status === "Waiting for Approval" &&
			onload.can_decide
		) {
			frm.add_custom_button(__("Approve"), () => act(frm, "approve")).addClass(
				"btn-primary"
			);
			frm.add_custom_button(
				__("Return"),
				() => with_reason(frm, "return_claim", __("Return the claim")),
				__("Other")
			);
			frm.add_custom_button(
				__("Reject"),
				() => with_reason(frm, "reject", __("Reject the claim")),
				__("Other")
			);
		}
		if (frm.doc.status === "Waiting for Approval") {
			frm.disable_save();
		}
	},
});

function show_where_it_is(frm) {
	frm.dashboard.clear_headline();
	const status = frm.doc.status;
	if (status === "Returned" && frm.doc.decision_note) {
		frm.dashboard.set_headline(
			__("Returned by {0}: {1}", [
				frm.doc.approved_by || frm.doc.approver_name || "",
				frm.doc.decision_note,
			]),
			"orange"
		);
	} else if (status === "Waiting for Approval") {
		frm.dashboard.set_headline(
			__("With {0} for approval.", [frm.doc.approver_name || frm.doc.approver]),
			"blue"
		);
	} else if (status === "Approved") {
		let text = __("{0} days added, usable until {1}.", [
			frm.doc.days_credited,
			frappe.datetime.str_to_user(frm.doc.lapses_on) || "-",
		]);
		if (frm.doc.days_not_credited) {
			text +=
				" " +
				__("{0} days were over the limit and not added.", [frm.doc.days_not_credited]);
		}
		frm.dashboard.set_headline(text, "green");
	} else if (status === "Rejected" && frm.doc.decision_note) {
		frm.dashboard.set_headline(__("Rejected: {0}", [frm.doc.decision_note]), "red");
	}
}

function act(frm, method, args = {}) {
	const go = () =>
		frappe
			.call({
				method: `${TOIL_API}.${method}`,
				args: { name: frm.doc.name, ...args },
				freeze: true,
			})
			.then(() => frm.reload_doc());
	return frm.is_dirty() ? frm.save().then(go) : go();
}

function with_reason(frm, method, title) {
	frappe.prompt(
		[
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("What the person needs to change or know"),
				reqd: 1,
			},
		],
		(values) => act(frm, method, { reason: values.reason }),
		title,
		__("Send")
	);
}
