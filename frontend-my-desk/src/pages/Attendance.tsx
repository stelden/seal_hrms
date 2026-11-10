// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Check-in from the phone (PWA-5) and attendance and shift requests (HR_ON_MY_DESK §3). Where the phone
 * is goes with a check-in only when HR asks for it and the phone shares it; HR decides the rest.
 */

import { useMemo, useState } from "react";
import { useParams } from "react-router";
import { formatDate, formatDateTime, useGet, usePost } from "@stelden/seal-frontend";
import { CheckboxInput, DateInput, FormActions, RadioInput, SealForm, SelectInput, TextInput, frappeDate, required, useSealForm, z } from "@stelden/seal-frontend/forms";
import { Alert, Button, DescriptionList, DetailPage, EmptyState, FormPage, List, ListItem, ListPage, Section, Text, __, useNotify } from "@stelden/seal-frontend/ui";
import { LogIn, LogOut, MapPin, Plus, Repeat } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";
import { localToday } from "../lib/week";

interface CheckinAnswer {
	offered: boolean;
	location: boolean;
	today: Array<{ name: string; log_type: "IN" | "OUT"; time: string; device_id: string | null }>;
	next: "IN" | "OUT";
}

/** Where the phone is, if it will say within ten seconds; null if it will not (the check-in goes ahead). */
function whereAmI(): Promise<{ latitude: number; longitude: number } | null> {
	if (!("geolocation" in navigator)) return Promise.resolve(null);
	return new Promise((resolve) =>
		navigator.geolocation.getCurrentPosition(
			(position) => resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
			() => resolve(null),
			{ enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
		),
	);
}

export function CheckIn() {
	const go = useGo();
	const notify = useNotify();
	const { data, isLoading, error, mutate } = useGet<CheckinAnswer>(M.checkinStatus);
	const record = usePost<{ name: string; log_type: string; time: string }>(M.checkIn);
	const [locating, setLocating] = useState(false);
	const [noLocation, setNoLocation] = useState(false);

	const check = async () => {
		if (!data) return;
		setNoLocation(false);
		let place: { latitude: number; longitude: number } | null = null;
		if (data.location) {
			setLocating(true);
			place = await whereAmI();
			setLocating(false);
			setNoLocation(!place);
		}
		try {
			await record.run({ log_type: data.next, ...(place ?? {}) });
			notify.success(data.next === "IN" ? __("Checked in.") : __("Checked out."));
			await mutate();
		} catch {
			/* the server's reason shows on the page */
		}
	};

	return (
		<FormPage title={__("Check-in")} onBack={() => go("")} loading={isLoading} error={error} onRetry={mutate}>
			{data && (
				<div className="flex flex-col gap-6">
					{!data.offered ? (
						<Alert tone="info">{__("HR has not turned on checking in from the phone.")}</Alert>
					) : (
						<>
							{record.errorMessage && <Alert tone="error">{record.errorMessage}</Alert>}
							{noLocation && <Alert tone="warning">{__("Your phone did not share where you are. Allow location for this site if HR needs it.")}</Alert>}
							<Button size="lg" loading={locating || record.loading} onClick={check}>
								{data.next === "IN" ? <LogIn /> : <LogOut />}
								{data.next === "IN" ? __("Check In") : __("Check Out")}
							</Button>
							{data.location && (
								<Text size="sm" muted>
									<MapPin aria-hidden className="mr-1 inline size-4" />
									{__("Where you are is recorded with each check-in, as HR asks.")}
								</Text>
							)}
						</>
					)}
					<Section title={__("Today")}>
						{data.today.length === 0 ? (
							<Text muted>{__("No check-ins today yet. Clock-ins on the office device show here too.")}</Text>
						) : (
							<List divided>
								{data.today.map((c) => (
									<ListItem
										key={c.name}
										primary={c.log_type === "IN" ? __("In") : __("Out")}
										secondary={c.device_id ? __("{0} · {1}", [formatDateTime(c.time), c.device_id]) : formatDateTime(c.time)}
									/>
								))}
							</List>
						)}
					</Section>
				</div>
			)}
		</FormPage>
	);
}

interface RequestsAnswer {
	attendance: Array<{ name: string; from_date: string; to_date: string; reason: string; docstatus: number }>;
	shifts: Array<{ name: string; shift_type: string; from_date: string; to_date: string | null; status: string; docstatus: number }>;
}

export function AttendanceList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<RequestsAnswer>(M.attendanceRequests);
	return (
		<ListPage
			title={__("Attendance Requests")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.attendanceNew)}>
					<Plus />
					{__("New Request")}
				</Button>
			}
		>
			{hasLoaded && !data?.attendance.length ? (
				<EmptyState icon={<MapPin />} title={__("No attendance requests")} description={__("Ask for days you worked from home or on duty elsewhere to count as attended.")} />
			) : (
				<List divided>
					{(data?.attendance ?? []).map((r) => (
						<ListItem
							key={r.name}
							primary={r.reason === "Work From Home" ? __("Work From Home") : __("On Duty")}
							secondary={__("{0} to {1}", [formatDate(r.from_date), formatDate(r.to_date)])}
							action={<Status value={r.docstatus === 1 ? "Approved" : r.docstatus === 2 ? "Cancelled" : "Open"} />}
							onClick={() => go(P.attendanceRecord(r.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

export function AttendanceForm() {
	const go = useGo();
	const notify = useNotify();
	const create = usePost<string>(M.requestAttendance);
	const schema = useMemo(() => z.object({ from_date: frappeDate(() => __("From Date")), to_date: frappeDate(() => __("To Date")), reason: required(() => __("Reason")) }).loose(), []);
	const form = useSealForm<{ from_date: string; to_date: string; reason: string; explanation: string; half_day: boolean }>({
		schema,
		defaultValues: { from_date: localToday(), to_date: localToday(), reason: "Work From Home", explanation: "", half_day: false },
	});
	const from = form.watch("from_date");
	return (
		<FormPage title={__("New Attendance Request")} onBack={() => go(P.attendance)}>
			<SealForm
				form={form}
				onSubmit={async (v) => {
					const name = await create.run({ ...v, half_day: v.half_day ? 1 : 0 });
					notify.success(__("Request sent to HR."));
					go(P.attendanceRecord(name));
				}}
			>
				<RadioInput
					name="reason"
					label={__("Reason")}
					required
					options={[
						{ value: "Work From Home", label: __("Work From Home") },
						{ value: "On Duty", label: __("On Duty"), description: __("Working away from the office, e.g. a field visit.") },
					]}
				/>
				<DateInput name="from_date" label={__("From Date")} required />
				<DateInput name="to_date" label={__("To Date")} required minDate={from || undefined} />
				<CheckboxInput name="half_day" label={__("Half Day")} />
				<TextInput name="explanation" label={__("Explanation")} multiline rows={3} />
				<FormActions submitLabel={__("Send Request")} onCancel={() => go(P.attendance)} />
			</SealForm>
		</FormPage>
	);
}

interface RequestRecordAnswer {
	name: string;
	employee_name: string;
	from_date: string;
	to_date: string | null;
	reason?: string;
	explanation?: string;
	half_day?: number;
	shift_type?: string;
	status?: string;
	docstatus: number;
	approver_name: string | null;
	mine: boolean;
}

export function RequestRecord({ doctype }: { doctype: "Attendance Request" | "Shift Request" }) {
	const go = useGo();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<RequestRecordAnswer>(M.attendanceRecord, { doctype, name });
	const shift = doctype === "Shift Request";
	return (
		<DetailPage
			title={shift ? __("Shift Request") : __("Attendance Request")}
			subtitle={data && (data.mine ? name : data.employee_name)}
			meta={data && <Status value={shift ? data.status : data.docstatus === 1 ? "Approved" : "Open"} />}
			onBack={() => go(shift ? P.shifts : P.attendance)}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<DescriptionList
					items={[
						{ label: __("Shift Type"), value: data.shift_type ?? null, hideWhenEmpty: true },
						{ label: __("Reason"), value: data.reason ?? null, hideWhenEmpty: true },
						{ label: __("From Date"), value: formatDate(data.from_date) },
						{ label: __("To Date"), value: data.to_date ? formatDate(data.to_date) : null, hideWhenEmpty: true },
						{ label: __("Approver"), value: data.approver_name, hideWhenEmpty: true },
						{ label: __("Explanation"), value: data.explanation ?? null, hideWhenEmpty: true, full: true },
					]}
				/>
			)}
		</DetailPage>
	);
}

export function ShiftList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<RequestsAnswer>(M.attendanceRequests);
	return (
		<ListPage
			title={__("Shift Requests")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.shiftNew)}>
					<Plus />
					{__("New Request")}
				</Button>
			}
		>
			{hasLoaded && !data?.shifts.length ? (
				<EmptyState icon={<Repeat />} title={__("No shift requests")} description={__("Ask to work a different shift for some days.")} />
			) : (
				<List divided>
					{(data?.shifts ?? []).map((r) => (
						<ListItem
							key={r.name}
							primary={r.shift_type}
							secondary={r.to_date ? __("{0} to {1}", [formatDate(r.from_date), formatDate(r.to_date)]) : __("From {0}", [formatDate(r.from_date)])}
							action={<Status value={r.status} />}
							onClick={() => go(P.shiftRecord(r.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface AttendanceOptions {
	shift_types: string[];
	shift_approver_name: string | null;
	has_shift_approver: boolean;
}

export function ShiftForm() {
	const go = useGo();
	const notify = useNotify();
	const options = useGet<AttendanceOptions>(M.attendanceOptions);
	const create = usePost<string>(M.requestShift);
	const schema = useMemo(() => z.object({ shift_type: required(() => __("Shift Type")), from_date: frappeDate(() => __("From Date")) }).loose(), []);
	const form = useSealForm<{ shift_type: string; from_date: string; to_date: string }>({ schema, defaultValues: { shift_type: "", from_date: localToday(), to_date: "" } });
	return (
		<FormPage title={__("New Shift Request")} onBack={() => go(P.shifts)} loading={options.isLoading} error={options.error} onRetry={options.mutate}>
			{options.data && !options.data.has_shift_approver && <Alert tone="warning">{__("Nobody approves your shift requests yet. Ask HR to set a shift approver.")}</Alert>}
			<SealForm
				form={form}
				onSubmit={async (v) => {
					const name = await create.run({ shift_type: v.shift_type, from_date: v.from_date, to_date: v.to_date || undefined });
					notify.success(__("Request sent to {0}.", [options.data?.shift_approver_name ?? __("your shift approver")]));
					go(P.shiftRecord(name));
				}}
			>
				<SelectInput name="shift_type" label={__("Shift Type")} required options={(options.data?.shift_types ?? []).map((s) => ({ value: s, label: s }))} />
				<DateInput name="from_date" label={__("From Date")} required />
				<DateInput name="to_date" label={__("To Date")} hint={__("Leave empty if the shift carries on.")} />
				<FormActions submitLabel={__("Send Request")} onCancel={() => go(P.shifts)} />
			</SealForm>
		</FormPage>
	);
}
