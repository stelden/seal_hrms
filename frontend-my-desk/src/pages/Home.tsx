// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/** Self Service's first screen: balances, what is in flight, the five quick actions, and every area. */

import type { ReactNode } from "react";
import { useGet } from "@stelden/seal-frontend";
import { Badge, Button, DashboardPage, List, ListItem, Section, StatCard, StatGrid, __ } from "@stelden/seal-frontend/ui";
import {
	CalendarDays,
	ChevronRight,
	Clock,
	FileClock,
	Fingerprint,
	HandCoins,
	Hourglass,
	IdCard,
	MapPin,
	Plane,
	Receipt,
	Repeat,
	Users,
	Wallet,
} from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { listFor, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { localToday, mondayOf } from "../lib/week";

interface HomeAnswer {
	employee: { name: string; employee_name: string; designation?: string; company: string };
	balances: Array<{ key: string; label: string; value: number }>;
	in_flight: Array<{ key: string; label: string; count: number; doctype: string }>;
	checkin: { offered: boolean; location: boolean };
}

export function MyHrHome() {
	const go = useGo();
	const { data, isLoading, error, mutate } = useGet<HomeAnswer>(M.home);
	const thisWeek = P.week(mondayOf(localToday()));

	const areas: Array<{ label: string; hint: string; path: string; icon: ReactNode }> = [
		{ label: __("Leave"), hint: __("Apply, and see what you asked for"), path: P.leave, icon: <CalendarDays /> },
		{ label: __("Cover"), hint: __("Handovers to answer and work you cover"), path: P.cover, icon: <Users /> },
		{ label: __("Time Off in Lieu"), hint: __("Claim extra hours as time off"), path: P.toil, icon: <Hourglass /> },
		{ label: __("Timesheets"), hint: __("Your week, day by day"), path: P.timesheet, icon: <Clock /> },
		{ label: __("Expense Claims"), hint: __("Claims and receipts"), path: P.expenses, icon: <Receipt /> },
		{ label: __("Advances"), hint: __("Money paid ahead and what is left to settle"), path: P.advances, icon: <HandCoins /> },
		{ label: __("Payslips"), hint: __("Your pay, month by month"), path: P.pay, icon: <Wallet /> },
		{ label: __("Attendance Requests"), hint: __("Days worked away from the office"), path: P.attendance, icon: <MapPin /> },
		{ label: __("Shift Requests"), hint: __("Ask to work another shift"), path: P.shifts, icon: <Repeat /> },
		{ label: __("Travel Requests"), hint: __("Trips for work, approved by your line manager"), path: P.travel, icon: <Plane /> },
		{ label: __("My Details"), hint: __("Contact, dependants and where you are paid"), path: P.me, icon: <IdCard /> },
	];
	if (data?.checkin.offered) areas.splice(4, 0, { label: __("Check-in"), hint: __("Check in and out from your phone"), path: P.checkIn, icon: <Fingerprint /> });

	return (
		<DashboardPage title={__("Self Service")} subtitle={data?.employee.employee_name} loading={isLoading} error={error} onRetry={mutate}>
			<div className="flex flex-col gap-6">
				{data && data.balances.length > 0 && (
					<StatGrid columns={2}>
						{data.balances.map((b) => (
							<StatCard key={b.key} label={b.label} value={__("{0} days", [String(b.value)])} onClick={() => go(b.key.startsWith("toil") ? P.toil : P.leave)} />
						))}
					</StatGrid>
				)}

				<Section title={__("Quick Actions")}>
					<div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
						<Button variant="outline" onClick={() => go(P.leaveNew)}>
							<CalendarDays />
							{__("Apply for Leave")}
						</Button>
						<Button variant="outline" onClick={() => go(P.toilNew)}>
							<Hourglass />
							{__("Claim Time Off")}
						</Button>
						<Button variant="outline" onClick={() => go(thisWeek)}>
							<FileClock />
							{__("This Week's Timesheet")}
						</Button>
						<Button variant="outline" onClick={() => go(P.expenseNew)}>
							<Receipt />
							{__("New Expense Claim")}
						</Button>
						{data?.checkin.offered && (
							<Button variant="outline" onClick={() => go(P.checkIn)}>
								<Fingerprint />
								{__("Check In")}
							</Button>
						)}
					</div>
				</Section>

				{data && data.in_flight.length > 0 && (
					<Section title={__("In Progress")}>
						<List divided>
							{data.in_flight.map((f) => {
								const path = listFor(f.doctype);
								return <ListItem key={f.key} primary={f.label} action={<Badge>{f.count}</Badge>} onClick={path ? () => go(path) : undefined} />;
							})}
						</List>
					</Section>
				)}

				<Section title={__("Everything in Self Service")}>
					<List divided>
						{areas.map((a) => (
							<ListItem key={a.path} primary={a.label} secondary={a.hint} icon={a.icon} action={<ChevronRight aria-hidden />} onClick={() => go(a.path)} />
						))}
					</List>
				</Section>
			</div>
		</DashboardPage>
	);
}
