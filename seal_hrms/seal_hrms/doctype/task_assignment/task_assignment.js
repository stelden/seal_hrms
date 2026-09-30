// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

const TA_ACTIONS = "seal_hrms.seal_hrms.task_assignment_actions";
const TA_CONTROLLER = "seal_hrms.seal_hrms.doctype.task_assignment.task_assignment";

frappe.ui.form.on("Task Assignment", {
	setup(frm) {
		const colleagues = () => ({
			query: `${TA_CONTROLLER}.get_assignable_employees`,
			filters: { employee: frm.doc.employee, leave_application: frm.doc.leave_application },
		});
		frm.set_query("task_assignee", colleagues);
		// A different stand-in for one task: the same colleagues who could cover the whole handover.
		frm.set_query("task_assignee", "assignment_todos", colleagues);
		frm.set_query("reference_type", "assignment_todos", () => ({ filters: [["DocType", "issingle", "=", 0]] }));
		frm.set_query("leave_application", () => ({
			filters: [
				["employee", "=", frm.doc.employee],
				["status", "in", ["Open", "Approved"]],
				["docstatus", "<", 2],
				["to_date", ">=", frappe.datetime.nowdate()],
			],
		}));
		frm.set_query("employee", () => {
			if (frappe.user.has_role(["HR User", "HR Manager", "System Manager"])) return {};
			return { filters: [["user_id", "=", frappe.session.user], ["status", "=", "Active"]] };
		});
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.nowdate());
		}
	},

	async refresh(frm) {
		frm.__me = frm.__me || (await ta_my_employee());
		ta_banner(frm);
		ta_buttons(frm);
	},

	// Load the member of staff's open work when they are chosen.
	employee(frm) {
		if (!frm.doc.employee || frm.doc.docstatus !== 0) return;
		frappe.call({
			method: `${TA_CONTROLLER}.get_employee_tasks`,
			args: { employee: frm.doc.employee },
			callback(r) {
				frm.clear_table("assignment_todos");
				(r.message || []).forEach((todo) => {
					const row = frm.add_child("assignment_todos");
					Object.assign(row, {
						todo: todo.name,
						reference_type: todo.reference_type,
						reference_name: todo.reference_name,
						description: todo.description,
						priority: todo.priority,
						due_date: todo.date,
					});
				});
				frm.refresh_field("assignment_todos");
			},
		});
	},
});

async function ta_my_employee() {
	const { message } = await frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name");
	return (message && message.name) || null;
}

function ta_covered_by(frm, row) {
	return row.task_assignee || frm.doc.task_assignee;
}

// What this person has been asked to cover on this handover.
function ta_role(frm) {
	const me = frm.__me;
	const doc = frm.doc;
	const own_rows = (doc.assignment_todos || []).filter((r) => r.task_assignee && r.task_assignee !== doc.task_assignee && r.task_assignee === me);
	const is_main = !!me && doc.task_assignee === me;
	const my_approvals = (doc.authorities || []).filter((r) => ta_covered_by(frm, r) === me);
	const pending = (is_main && doc.acceptance === "Pending") || own_rows.some((r) => r.acceptance === "Pending")
		|| my_approvals.some((r) => r.acceptance === "Pending");
	return {
		my_approvals,
		covers_work: is_main || own_rows.length > 0,
		is_owner: !!me && doc.employee === me,
		is_hr: frappe.user.has_role(["HR User", "HR Manager", "System Manager"]),
		is_stand_in: is_main || own_rows.length > 0 || my_approvals.length > 0
			|| (doc.assignment_todos || []).some((r) => ta_covered_by(frm, r) === me),
		pending,
	};
}

function ta_banner(frm) {
	const doc = frm.doc;
	const role = ta_role(frm);
	const from = doc.leave_from ? frappe.datetime.str_to_user(doc.leave_from) : __("the first day of leave");
	const back = doc.return_date ? frappe.datetime.str_to_user(doc.return_date) : __("the first day back");
	const who = doc.task_assignee_name || __("the stand-in");
	let now, next, todo, colour = "blue";

	if (frm.is_new() || doc.docstatus === 0) {
		now = __("Not sent to the stand-in yet.");
		next = __("{0} is asked to agree to cover the work listed on the Work tab.", [who]);
		todo = role.is_owner || role.is_hr
			? __("Name the stand-in, check the work, then click <b>Submit</b>.")
			: __("Nothing for you to do here yet.");
	} else if (doc.status === "Awaiting Acceptance") {
		now = __("Waiting for the stand-in to agree.");
		next = __("Once everyone agrees and the leave is approved, the work moves to them on {0}.", [from]);
		if (role.pending && role.my_approvals.length && !role.covers_work) {
			todo = __("Under <b>Approvals</b>, click <b>Accept</b> or <b>Decline</b> for each approval you are asked to give.");
		} else if (role.pending) {
			todo = role.my_approvals.length
				? __("Click <b>Accept</b> if you can cover the work, or <b>Decline</b> and say why; then answer each item under <b>Approvals</b>.")
				: __("Click <b>Accept</b> if you can cover it, or <b>Decline</b> and say why.");
		} else {
			todo = __("Nothing yet. You will be emailed when they answer.");
		}
		colour = "orange";
	} else if (doc.status === "Declined") {
		now = __("A stand-in cannot cover this.");
		next = __("Someone else needs to be asked. Nothing has moved.");
		todo = role.is_owner || role.is_hr
			? __("Click <b>Cancel</b>, then <b>Amend</b>, and name another stand-in.")
			: __("Nothing for you to do.");
		colour = "red";
	} else if (doc.status === "Accepted") {
		now = __("Agreed. Nothing has moved yet.");
		next = __("The work moves to the stand-in on {0}, once the leave is approved.", [from]);
		todo = role.is_stand_in
			? __("Nothing until then. If you can no longer cover it, click <b>Decline</b>.")
			: __("Nothing until then.");
		colour = "green";
	} else if (doc.status === "Active") {
		now = __("{0} is covering the work.", [who]);
		next = __("Whatever is still open comes back to {0} on {1}.", [doc.employee_name, back]);
		if (role.is_stand_in) {
			todo = __("Click <b>Leave a Note</b> on work as you go, and <b>Note for Return</b> before {0}.", [back]);
		} else if (role.is_owner) {
			todo = __("Nothing while away. If the leave ends early, click <b>I'm Back</b>.");
		} else if (role.is_hr) {
			todo = __("Nothing, unless the leave ends early: then click <b>Return the Work Now</b>.");
		} else {
			todo = __("Nothing for you to do.");
		}
	} else if (doc.status === "Handed Back") {
		now = __("The work was returned on {0}.", [frappe.datetime.str_to_user(doc.handed_back_at)]);
		next = __("Nothing: this handover is finished.");
		todo = __("Read the stand-in's note on the Return tab.");
		colour = "grey";
	} else if (doc.status === "Legacy") {
		now = __("Recorded before handovers could return work.");
		next = __("Nothing: any work left with the stand-in was returned when the system was updated.");
		todo = __("Nothing to do on this form.");
		colour = "grey";
	} else {
		now = __("Called off.");
		next = __("Nothing: any work already handed over has gone back.");
		todo = __("Nothing to do on this form.");
		colour = "grey";
	}

	if (doc.status === "Declined" && (doc.decline_reason || "").trim()) {
		now += " " + __("Reason: {0}", [frappe.utils.escape_html(doc.decline_reason)]);
	}
	const rows = [[__("Now"), now], [__("Next"), next], [__("Do"), todo]]
		.map(([label, text]) => `<div><b>${label}:</b> ${text}</div>`)
		.join("");
	frm.layout.show_message(`<div class="ta-banner">${rows}</div>`, colour, true);
}

function ta_call(frm, method, args, done) {
	frappe.call({
		method: `${TA_ACTIONS}.${method}`,
		args: Object.assign({ name: frm.doc.name }, args),
		freeze: true,
		callback() {
			if (done) done();
			frm.reload_doc();
		},
	});
}

function ta_buttons(frm) {
	const doc = frm.doc;
	const role = ta_role(frm);

	if (doc.docstatus === 0 && !frm.is_new() && (role.is_owner || role.is_hr)) {
		frm.add_custom_button(__("Find What I Approve"), () => {
			frappe.call({
				method: "seal_hrms.seal_hrms.acting.suggest_authorities",
				args: { employee: doc.employee },
				callback(r) {
					const have = new Set((doc.authorities || []).map((a) => a.authority));
					const found = (r.message || []).filter((a) => !have.has(a.authority));
					found.forEach((a) => Object.assign(frm.add_child("authorities"), a));
					frm.refresh_field("authorities");
					frappe.show_alert(found.length
						? __("Added {0}. Name who approves each in your place, or leave it to your stand-in.", [found.map((a) => a.authority_label).join(", ")])
						: __("Nothing new: you do not approve anything else for anyone."));
				},
			});
		});
	}
	if (doc.docstatus !== 1) return;

	if (["Awaiting Acceptance", "Accepted", "Declined"].includes(doc.status)) {
		role.my_approvals.forEach((row) => {
			const label = row.authority_label || row.authority;
			if (row.acceptance !== "Accepted") {
				frm.add_custom_button(__("Accept: {0}", [label]), () =>
					ta_call(frm, "respond_authority", { row: row.name, answer: "Accepted" }), __("Approvals"));
			}
			frm.add_custom_button(__("Decline: {0}", [label]), () => {
				frappe.prompt(
					{ fieldname: "reason", fieldtype: "Small Text", reqd: 1, label: __("Why can you not approve this?"),
					  description: __("{0} reads this to decide who to ask instead.", [doc.employee_name]) },
					(v) => ta_call(frm, "respond_authority", { row: row.name, answer: "Declined", reason: v.reason }),
					__("Decline"),
					__("Decline")
				);
			}, __("Approvals"));
		});
	}

	if (role.covers_work && ["Awaiting Acceptance", "Accepted", "Declined"].includes(doc.status)) {
		if (role.pending || doc.status !== "Accepted") {
			frm.add_custom_button(__("Accept"), () => ta_call(frm, "respond", { answer: "Accepted" }));
		}
		frm.add_custom_button(__("Decline"), () => {
			frappe.prompt(
				{ fieldname: "reason", fieldtype: "Small Text", reqd: 1, label: __("Why can you not cover it?"),
				  description: __("{0} reads this to decide who to ask instead.", [doc.employee_name]) },
				(v) => ta_call(frm, "respond", { answer: "Declined", reason: v.reason }),
				__("Decline to Cover"),
				__("Decline")
			);
		});
	}

	if (doc.status === "Active" && role.is_stand_in) {
		const mine = (doc.assignment_todos || []).filter((r) => ta_covered_by(frm, r) === frm.__me);
		if (mine.length) {
			frm.add_custom_button(__("Leave a Note"), () => {
				frappe.prompt(
					[
						{ fieldname: "row", fieldtype: "Select", reqd: 1, label: __("Which Task"),
						  options: mine.map((r) => ({ value: r.name, label: frappe.utils.html2text(r.description || "").slice(0, 80) })) },
						{ fieldname: "note", fieldtype: "Small Text", reqd: 1, label: __("What You Did"),
						  description: __("So {0} can pick up where you left off.", [doc.employee_name]) },
					],
					(v) => ta_call(frm, "add_note", v),
					__("Leave a Note"),
					__("Save Note")
				);
			});
		}
		frm.add_custom_button(__("Note for Return"), () => {
			frappe.prompt(
				{ fieldname: "note", fieldtype: "Text Editor", reqd: 1, label: __("Note for When They Are Back"),
				  default: doc.return_summary || "",
				  description: __("What you finished, what is waiting, and who called.") },
				(v) => ta_call(frm, "leave_return_note", v),
				__("Note for Return"),
				__("Save Note")
			);
		});
	}

	if (doc.status === "Active" && (role.is_owner || role.is_hr)) {
		frm.add_custom_button(role.is_owner ? __("I'm Back") : __("Return the Work Now"), () => {
			frappe.confirm(
				__("Take back everything that is still open now, before {0}?", [frappe.datetime.str_to_user(doc.return_date)]),
				() => ta_call(frm, "return_work", {})
			);
		});
	}
}
