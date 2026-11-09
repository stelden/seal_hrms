// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/* global seal_hrms */

// Draws a process form's Now / Next / Do banner (house rule), from rows the
// server worked out for the person viewing. The text is trusted server HTML:
// names are escaped there and only <b> is added.

frappe.provide("seal_hrms");

seal_hrms.WHERE_IT_IS_COLOURS = {
	info: ["var(--blue-600)", "var(--blue-50)"],
	success: ["var(--green-600)", "var(--green-50)"],
	warning: ["var(--orange-600)", "var(--orange-50)"],
	error: ["var(--red-600)", "var(--red-50)"],
};

seal_hrms.show_where_it_is = function (frm, banner) {
	frm.dashboard.clear_headline();
	if (!banner || !banner.items || !banner.items.length) return;
	const [colour, background] =
		seal_hrms.WHERE_IT_IS_COLOURS[banner.type] || seal_hrms.WHERE_IT_IS_COLOURS.info;
	const rows = banner.items
		.map(
			(item) => `<tr>
				<th style="padding: 2px 12px 2px 0; vertical-align: top; white-space: nowrap; color: ${colour};">${item.label}</th>
				<td style="padding: 2px 0;">${item.text}</td>
			</tr>`
		)
		.join("");
	frm.dashboard.set_headline_alert(
		`<div class="seal-where-it-is" style="padding: 12px 15px; border-left: 4px solid ${colour}; background: ${background};">
			<table style="margin: 0; border-collapse: collapse;">${rows}</table>
		</div>`
	);
};
