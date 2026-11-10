// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// The test host: what seal_desk's shell gives a section (a router, ShellProvider, SectionOutlet, the
// frame), nothing else. Every call the section makes goes to the stub server in phone.mjs.

import { useMemo } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, useNavigate, useRoutes } from "react-router";

import "./index.css";

import { PortalProvider } from "@stelden/seal-frontend";
import { SectionOutlet, ShellProvider, type SectionDefinition, type ShellApi } from "@stelden/seal-frontend/section";
import { AppShell, SealProvider, __ } from "@stelden/seal-frontend/ui";
import { House, LayoutGrid } from "@stelden/seal-frontend/icons";

const BASE = "/my-desk/apps/my-hr";
const ENTRY = {
	key: "seal_hrms.my_hr",
	label: "My HR",
	module: "/assets/seal_hrms/my-desk/section.js",
	css: "/assets/seal_hrms/my-desk/section.css",
	stamp: "/assets/seal_hrms/my-desk/section.json",
};

declare global {
	interface Window {
		__verifications: number;
		__errors: string[];
	}
}
window.__verifications = 0;
window.__errors = [];

function Routes({ definition }: { definition: SectionDefinition }) {
	const Home = definition.home;
	return useRoutes([{ index: true, element: <Home /> }, ...definition.routes.map((r) => ({ path: r.path, element: r.element }))]);
}

function Host() {
	const navigate = useNavigate();
	const api = useMemo<ShellApi>(
		() => ({
			user: "otieno.ochieng@kilimani-office.co.ke",
			company: "Kilimani Community Trust",
			navigate: (path) => navigate(path.startsWith("/") ? path : path ? `${BASE}/${path}` : BASE),
			openRecord: (doctype, name) => navigate(`/my-desk/r/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`),
			openList: (doctype) => navigate(`/my-desk/l/${encodeURIComponent(doctype)}`),
			verify: async () => {
				window.__verifications += 1;
				return true;
			},
			extra: {},
		}),
		[navigate],
	);
	return (
		<AppShell
			variant="app"
			title={__("My Desk")}
			tabs={[
				{ id: "home", label: __("Home"), icon: <House /> },
				{ id: "apps", label: __("Apps"), icon: <LayoutGrid /> },
			]}
			activeTab="apps"
			onTab={() => undefined}
		>
			<ShellProvider value={api}>
				{useRoutes([{ path: `${BASE}/*`, element: <SectionOutlet entry={ENTRY} render={(definition) => <Routes definition={definition} />} onError={(e) => window.__errors.push(String(e))} /> }])}
			</ShellProvider>
		</AppShell>
	);
}

createRoot(document.getElementById("root")!).render(
	<PortalProvider>
		<SealProvider>
			<BrowserRouter>
				<Host />
			</BrowserRouter>
		</SealProvider>
	</PortalProvider>,
);
