// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

frappe.pages["departmental-coverage-calendar"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Departmental Coverage Calendar"),
		single_column: true,
	});

	const state = { company: null, department: null, leave_period: null };

	const company_field = page.add_field({
		fieldtype: "Link",
		fieldname: "company",
		label: __("Company"),
		options: "Company",
		default: frappe.defaults.get_default("company"),
		change: () => { state.company = company_field.get_value(); refresh(); },
	});
	state.company = frappe.defaults.get_default("company");

	const dept_field = page.add_field({
		fieldtype: "Link",
		fieldname: "department",
		label: __("Department"),
		options: "Department",
		change: () => { state.department = dept_field.get_value(); refresh(); },
	});

	const period_field = page.add_field({
		fieldtype: "Link",
		fieldname: "leave_period",
		label: __("Leave Period"),
		options: "Leave Period",
		change: () => { state.leave_period = period_field.get_value(); refresh(); },
	});

	const $content = $('<div class="layout-main-section" style="padding: 1rem;"></div>').appendTo(page.body);

	function refresh() {
		if (!state.company) {
			$content.html(`<p class="text-muted">${__("Pick a company to see coverage.")}</p>`);
			return;
		}
		$content.html(`<p class="text-muted">${__("Loading...")}</p>`);
		frappe.call({
			method: "seal_hrms.seal_hrms.leave_planning.reports.departmental_coverage",
			args: {
				company: state.company,
				department: state.department || null,
				leave_period: state.leave_period || null,
			},
			callback: (r) => render(r.message || {}),
		});
	}

	function render(data) {
		const weeks = data.weeks || [];
		const cells = data.cells || [];
		const headcount = data.headcount || {};

		if (!weeks.length) {
			$content.html(`<p class="text-muted">${__("No data for the selected scope.")}</p>`);
			return;
		}

		const by_dept_week = {};
		cells.forEach((c) => {
			by_dept_week[`${c.department}|${c.week}`] = c;
		});
		const departments = Object.keys(headcount).sort();

		const colorClass = (pct) => {
			if (pct === 0) return "";
			if (pct < 10) return "indicator-pill green";
			if (pct < 25) return "indicator-pill yellow";
			if (pct < 50) return "indicator-pill orange";
			return "indicator-pill red";
		};

		let html = `
			<p class="text-muted">${__("Each cell shows planned-absent employees / headcount and % out for that ISO week. Click a cell for detail.")}</p>
			<div style="overflow-x: auto;">
			<table class="table table-bordered" style="font-size: 0.85rem; min-width: 100%;">
				<thead><tr><th>${__("Department")}</th><th class="text-right">${__("HC")}</th>`;
		weeks.forEach((w) => { html += `<th class="text-center">${w}</th>`; });
		html += `</tr></thead><tbody>`;
		departments.forEach((dept) => {
			html += `<tr><td><b>${frappe.utils.escape_html(dept)}</b></td>`;
			html += `<td class="text-right">${headcount[dept]}</td>`;
			weeks.forEach((w) => {
				const c = by_dept_week[`${dept}|${w}`];
				if (!c) {
					html += `<td class="text-center text-muted">—</td>`;
				} else {
					const pct = c.percent_absent;
					html += `<td class="text-center"><span class="${colorClass(pct)}">${c.absent_employees}/${c.headcount}<br/><small>${pct}%</small></span></td>`;
				}
			});
			html += `</tr>`;
		});
		html += `</tbody></table></div>`;
		$content.html(html);
	}

	refresh();
};
