// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.pages["leave-planning-compliance"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Leave Planning Compliance"),
		single_column: true,
	});

	const state = { cycle: null, department: null, status_filter: null, search: "" };
	let last_data = null;
	let selected_member_names = new Set();

	const cycle_field = page.add_field({
		fieldtype: "Link",
		fieldname: "cycle",
		label: __("Planning Cycle"),
		options: "Leave Planning Cycle",
		change: () => { state.cycle = cycle_field.get_value(); selected_member_names.clear(); refresh(); },
	});

	const dept_field = page.add_field({
		fieldtype: "Link",
		fieldname: "department",
		label: __("Department"),
		options: "Department",
		change: () => { state.department = dept_field.get_value(); refresh(); },
	});

	const status_field = page.add_field({
		fieldtype: "Select",
		fieldname: "status_filter",
		label: __("Plan Status"),
		options: "\nNot Started\nDraft\nPending Manager\nPending HR\nReturned\nApproved\nCancelled",
		change: () => {
			state.status_filter = status_field.get_value() || null;
			refresh();
		},
	});

	const search_field = page.add_field({
		fieldtype: "Data",
		fieldname: "search",
		label: __("Search"),
		change: () => { state.search = search_field.get_value() || ""; refresh(); },
	});

	page.set_primary_action(__("Bulk Nudge Selected"), bulk_nudge);

	const $summary = $('<div style="padding: 1rem;"></div>').appendTo(page.body);
	const $content = $('<div class="layout-main-section" style="padding: 0 1rem 1rem;"></div>').appendTo(page.body);

	function refresh() {
		if (!state.cycle) {
			$summary.html("");
			$content.html(`<p class="text-muted">${__("Pick a cycle to see compliance.")}</p>`);
			return;
		}
		$content.html(`<p class="text-muted">${__("Loading...")}</p>`);
		frappe.call({
			method: "seal_hrms.seal_hrms.leave_planning.reports.compliance_roster",
			args: {
				cycle: state.cycle,
				department: state.department || null,
				status_filter: state.status_filter ? [state.status_filter] : null,
				search: state.search || null,
			},
			callback: (r) => {
				last_data = r.message || null;
				render();
			},
		});
	}

	function render() {
		if (!last_data) return;
		const cycle = last_data.cycle || {};
		const summary = last_data.summary || {};
		const members = last_data.members || [];

		const days_str = cycle.days_remaining == null ? "—"
			: cycle.days_remaining < 0 ? __("{0} day(s) past deadline", [Math.abs(cycle.days_remaining)])
			: __("{0} day(s) remaining", [cycle.days_remaining]);

		$summary.html(`
			<div class="row">
				<div class="col-md-6">
					<h4>${frappe.utils.escape_html(cycle.name || "")}</h4>
					<p class="text-muted">${__("Status")}: <b>${cycle.status || ""}</b> &middot; ${__("Deadline")}: <b>${cycle.deadline || "—"}</b> &middot; ${days_str}</p>
				</div>
				<div class="col-md-6 text-right">
					<p>
						<span class="indicator-pill green">${__("Approved")}: ${summary.approved || 0} (${summary.percent_approved || 0}%)</span>
						<span class="indicator-pill orange">${__("Pending")}: ${summary.pending || 0} (${summary.percent_pending || 0}%)</span>
						<span class="indicator-pill yellow">${__("Draft")}: ${summary.draft || 0} (${summary.percent_draft || 0}%)</span>
						<span class="indicator-pill red">${__("Not Started")}: ${summary.not_started || 0} (${summary.percent_not_started || 0}%)</span>
						<span class="indicator-pill grey">${__("Exempt")}: ${summary.exempt || 0}</span>
					</p>
				</div>
			</div>
		`);

		if (!members.length) {
			$content.html(`<p class="text-muted">${__("No members match the current filters.")}</p>`);
			return;
		}

		let html = `
			<table class="table table-bordered" style="font-size: 0.9rem;">
				<thead>
					<tr>
						<th><input type="checkbox" id="lpc-select-all"/></th>
						<th>${__("Employee")}</th>
						<th>${__("Department")}</th>
						<th>${__("Plan Status")}</th>
						<th>${__("Plan")}</th>
						<th>${__("Last Nudge")}</th>
						<th>${__("Nudges")}</th>
					</tr>
				</thead>
				<tbody>`;
		members.forEach((m) => {
			const checked = selected_member_names.has(m.name) ? "checked" : "";
			const exempt_marker = m.exempt ? `<span class="indicator-pill grey">${__("EXEMPT")}</span>` : "";
			const plan_link = m.plan ? `<a href="/app/leave-plan/${m.plan}">${m.plan}</a>` : "—";
			html += `
				<tr>
					<td><input type="checkbox" class="lpc-row" data-name="${frappe.utils.escape_html(m.name)}" ${checked} ${m.exempt ? 'disabled' : ''}/></td>
					<td>${frappe.utils.escape_html(m.employee_name || m.employee)} ${exempt_marker}</td>
					<td>${frappe.utils.escape_html(m.department || "—")}</td>
					<td>${frappe.utils.escape_html(m.plan_status || "—")}</td>
					<td>${plan_link}</td>
					<td>${m.last_nudge_at || "—"}</td>
					<td class="text-right">${m.nudges_sent || 0}</td>
				</tr>`;
		});
		html += "</tbody></table>";
		$content.html(html);

		$content.find("#lpc-select-all").on("change", function () {
			const checked = $(this).is(":checked");
			$content.find(".lpc-row:not([disabled])").prop("checked", checked).each(function () {
				const name = $(this).data("name");
				if (checked) selected_member_names.add(name);
				else selected_member_names.delete(name);
			});
		});

		$content.find(".lpc-row").on("change", function () {
			const name = $(this).data("name");
			if ($(this).is(":checked")) selected_member_names.add(name);
			else selected_member_names.delete(name);
		});
	}

	function bulk_nudge() {
		if (!selected_member_names.size) {
			frappe.msgprint(__("No members selected."));
			return;
		}
		if (!state.cycle) return;
		frappe.confirm(
			__("Send a reminder to {0} selected member(s)?", [selected_member_names.size]),
			() => {
				frappe.call({
					method: "seal_hrms.seal_hrms.leave_planning.endpoints.admin.bulk_nudge_members",
					args: { cycle: state.cycle, member_names: Array.from(selected_member_names) },
					callback: (r) => {
						const result = r.message || {};
						frappe.show_alert({
							message: __("Nudged {0}, throttled {1}, skipped {2}", [
								result.nudged || 0, result.throttled || 0, result.skipped || 0,
							]),
							indicator: "green",
						});
						selected_member_names.clear();
						refresh();
					},
				});
			}
		);
	}

	refresh();
};
