// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Timesheets on the phone (HR_ON_MY_DESK §3): a week one day at a time (arrows), lines per piece of
 * work, the day's total beside what attendance shows, rest days, holidays and leave marked; Copy Last
 * Week; the weekly check; Send for Approval; Claim as Time Off in Lieu once approved. The server writes
 * the time lines from the week (timesheets/week.py), exactly as the desk's grid does. Only companies
 * that keep weekly timesheets edit here (P5-10); other timesheets open read only.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router";
import { formatDate, useGet, usePost } from "@stelden/seal-frontend";
import { useShell } from "@stelden/seal-frontend/section";
import {
	Alert,
	Badge,
	Button,
	Card,
	CardContent,
	DescriptionList,
	DetailPage,
	EmptyState,
	FormPage,
	IconButton,
	Input,
	Label,
	List,
	ListItem,
	ListPage,
	Section,
	Select,
	Text,
	__,
	useNotify,
} from "@stelden/seal-frontend/ui";
import { ChevronLeft, ChevronRight, Clock, Copy, Plus, Trash2 } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { nameFrom, P } from "../lib/paths";
import { clearDraft, readDraft, savedDay, useDraft } from "../lib/drafts";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";
import { addDays, copyLastWeek, dayTotal, forSaving, localToday, mondayOf, newEntry, setHours, weekDays, weekTotal, type WeekEntry } from "../lib/week";

interface TimesheetsAnswer {
	weekly: boolean;
	timesheets: Array<{ name: string; start_date: string; end_date: string; total_hours: number; status: string; docstatus: number; custom_week_start?: string; custom_approval_state?: string }>;
}

export function TimesheetList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<TimesheetsAnswer>(M.timesheets);
	return (
		<ListPage
			title={__("Timesheets")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				data?.weekly ? (
					<Button onClick={() => go(P.week(mondayOf(localToday())))}>
						<Clock />
						{__("This Week")}
					</Button>
				) : undefined
			}
		>
			{data && !data.weekly && <Alert tone="info">{__("Your company does not keep weekly timesheets. Fill timesheets in on a computer; they show here.")}</Alert>}
			{hasLoaded && !data?.timesheets.length ? (
				<EmptyState icon={<Clock />} title={__("No timesheets yet")} description={__("Your timesheets show here, newest first.")} />
			) : (
				<List divided>
					{(data?.timesheets ?? []).map((t) => (
						<ListItem
							key={t.name}
							primary={__("{0} to {1}", [formatDate(t.start_date), formatDate(t.end_date)])}
							secondary={__("{0} hours", [String(t.total_hours ?? 0)])}
							action={<Status value={t.docstatus === 1 ? "Approved" : t.custom_approval_state || t.status} />}
							onClick={() => go(data?.weekly && t.custom_week_start ? P.week(t.custom_week_start) : P.timesheetRecord(t.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface WeekAnswer {
	weekly: boolean;
	checks: string[];
	week_start: string;
	hours_per_day: number;
	default_activity_type: string | null;
	days: Array<{ date: string; kind: string; leave: string | null; leave_fraction: number; attendance_hours: number | null }>;
	previous_entries: WeekEntry[];
	activity_types: string[];
	approval: boolean;
	timesheet: null | {
		name: string;
		docstatus: number;
		state: string;
		return_reason: string | null;
		approver_name: string | null;
		entries: WeekEntry[];
		total_hours: number;
		can_edit: boolean;
		can_send: boolean;
		can_claim: boolean;
	};
}

/** The day's kind in the person's words (the server's calendar names: working day, rest day, public holiday). */
function dayKind(kind: string): string | null {
	if (kind === "Rest day") return __("Rest Day");
	if (kind === "Public holiday") return __("Public Holiday");
	return null;
}

function weekday(day: string): string {
	const index = (new Date(`${day}T12:00:00Z`).getUTCDay() + 6) % 7;
	return [__("Monday"), __("Tuesday"), __("Wednesday"), __("Thursday"), __("Friday"), __("Saturday"), __("Sunday")][index];
}

export function TimesheetWeek() {
	const go = useGo();
	const notify = useNotify();
	const monday = mondayOf(useParams().week || localToday());
	const { data, isLoading, error, mutate } = useGet<WeekAnswer>(M.timesheetWeek, { week_start: monday });
	const save = usePost<{ name: string; state: string }>(M.saveTimesheetWeek);
	const claim = usePost<string>(M.timesheetClaim);
	const [entries, setEntries] = useState<WeekEntry[]>([]);
	const [dayIndex, setDayIndex] = useState(() => {
		const today = localToday();
		return today >= monday && today <= addDays(monday, 6) ? weekDays(monday).indexOf(today) : 0;
	});
	const [dirty, setDirtyState] = useState(false);
	// Read inside the effect below: a refetch while the person is typing must not wipe what they typed.
	const dirtyRef = useRef(false);
	const setDirty = (value: boolean) => {
		dirtyRef.current = value;
		setDirtyState(value);
	};
	// The week as typed is kept on the phone until the server has it (P6 drafts, DESIGN §6.9).
	const draft = useDraft<WeekEntry[]>(useShell().user, "timesheet-week", monday);
	const [restoredAt, setRestoredAt] = useState<number | null>(null);
	const serverEntries = (answer: WeekAnswer) => (answer.timesheet?.entries.length ? answer.timesheet.entries : [newEntry([], answer.default_activity_type)]);
	const shownWeek = useRef<string | null>(null);

	useEffect(() => {
		if (!data || data.week_start !== monday) return;
		const sameWeek = shownWeek.current === monday;
		shownWeek.current = monday;
		if (sameWeek && dirtyRef.current) return; // a refetch: keep what is being typed
		const canEdit = data.weekly && (!data.timesheet || data.timesheet.can_edit);
		const kept = draft.key ? readDraft<WeekEntry[]>(draft.key) : null;
		if (kept && canEdit && Array.isArray(kept.value) && kept.value.length) {
			setEntries(kept.value);
			setDirty(true);
			setRestoredAt(kept.saved);
			return;
		}
		// Sent or decided since the draft was kept (perhaps on a computer): the server's week wins.
		if (kept && draft.key) clearDraft(draft.key);
		setEntries(serverEntries(data));
		setDirty(false);
		setRestoredAt(null);
		// Deliberately not every dependency: runs when the server's week arrives, not on each keystroke
	}, [data, monday]);

	const days = weekDays(monday);
	const day = data?.days[dayIndex];
	const editable = !!data?.weekly && (!data.timesheet || data.timesheet.can_edit);
	const options = useMemo(() => (data?.activity_types ?? []).map((a) => ({ value: a, label: a })), [data]);
	const change = (next: WeekEntry[]) => {
		setEntries(next);
		setDirty(true);
		draft.keep(next);
	};
	const discard = () => {
		draft.clear();
		setRestoredAt(null);
		if (data) setEntries(serverEntries(data));
		setDirty(false);
	};

	const store = async (send: boolean) => {
		try {
			const answer = await save.run({ week_start: monday, entries: JSON.stringify(forSaving(entries)), send: send ? 1 : 0 });
			notify.success(send ? __("Week sent for approval.") : __("Week saved."));
			draft.clear(); // the server has it now
			setRestoredAt(null);
			setDirty(false);
			await mutate();
			return answer;
		} catch {
			return null; // the server's reason shows above the week
		}
	};

	const header = data?.timesheet?.can_claim ? (
		<Button
			onClick={async () => {
				try {
					go(P.toilRecord(await claim.run({ name: data.timesheet!.name })));
				} catch {
					/* shown above */
				}
			}}
			loading={claim.loading}
		>
			{__("Claim as Time Off in Lieu")}
		</Button>
	) : editable ? (
		<div className="flex gap-2">
			<Button variant="outline" loading={save.loading} disabled={!dirty} onClick={() => store(false)}>
				{__("Save")}
			</Button>
			{data?.approval && (
				<Button loading={save.loading} onClick={() => store(true)}>
					{__("Send for Approval")}
				</Button>
			)}
		</div>
	) : undefined;

	return (
		<FormPage
			title={__("Week of {0}", [formatDate(monday)])}
			subtitle={__("{0} hours this week", [String(weekTotal(entries))])}
			meta={data?.timesheet && <Status value={data.timesheet.docstatus === 1 ? "Approved" : data.timesheet.state} />}
			onBack={() => go(P.timesheet)}
			actions={header}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-4">
					{(save.errorMessage || claim.errorMessage) && <Alert tone="error">{save.errorMessage || claim.errorMessage}</Alert>}
					{restoredAt !== null && (
						<Alert
							tone="info"
							title={__("Restored From This Phone")}
							action={
								<Button onClick={discard}>{__("Discard")}</Button>
							}
						>
							{__("What you entered on {0} was not saved yet. Save or send it when you are ready.", [formatDate(savedDay(restoredAt))])}
						</Alert>
					)}
					{!data.weekly && <Alert tone="info">{__("Your company does not keep weekly timesheets. Fill timesheets in on a computer.")}</Alert>}
					{data.timesheet?.state === "Returned" && data.timesheet.return_reason && (
						<Alert tone="warning" title={__("Returned to You")}>
							{data.timesheet.return_reason}
						</Alert>
					)}

					<div className="flex items-center justify-between gap-2">
						<IconButton label={__("Previous Day")} variant="outline" onClick={() => (dayIndex > 0 ? setDayIndex(dayIndex - 1) : go(P.week(addDays(monday, -7))))}>
							<ChevronLeft />
						</IconButton>
						<div className="flex flex-col items-center">
							<Text size="lg">{weekday(days[dayIndex])}</Text>
							<Text size="sm" muted>
								{formatDate(days[dayIndex])}
							</Text>
						</div>
						<IconButton label={__("Next Day")} variant="outline" onClick={() => (dayIndex < 6 ? setDayIndex(dayIndex + 1) : go(P.week(addDays(monday, 7))))}>
							<ChevronRight />
						</IconButton>
					</div>

					<div className="flex flex-wrap gap-2">
						<Badge>{__("{0} hours entered", [String(dayTotal(entries, dayIndex))])}</Badge>
						{day?.attendance_hours !== null && day?.attendance_hours !== undefined && <Badge variant="outline">{__("Attendance {0} hours", [String(day.attendance_hours)])}</Badge>}
						{day && dayKind(day.kind) && <Badge tone="info">{dayKind(day.kind)}</Badge>}
						{day?.leave && <Badge tone="warning">{day.leave_fraction === 0.5 ? __("Half Day of Leave") : __("On Leave")}</Badge>}
					</div>

					{entries.map((entry) => (
						<Card key={entry.row}>
							<CardContent className="flex flex-col gap-3">
								<div className="flex flex-col gap-1">
									<Label htmlFor={`activity-${entry.row}`}>{__("Activity Type")}</Label>
									<Select
										id={`activity-${entry.row}`}
										value={entry.activity_type}
										options={options}
										disabled={!editable}
										onValueChange={(value) => change(entries.map((e) => (e.row === entry.row ? { ...e, activity_type: value } : e)))}
									/>
								</div>
								<div className="flex flex-col gap-1">
									<Label htmlFor={`description-${entry.row}`}>{__("Description")}</Label>
									<Input
										id={`description-${entry.row}`}
										value={entry.description ?? ""}
										disabled={!editable}
										onChange={(event) => change(entries.map((e) => (e.row === entry.row ? { ...e, description: event.target.value } : e)))}
									/>
								</div>
								<div className="flex items-end gap-2">
									<div className="flex flex-1 flex-col gap-1">
										<Label htmlFor={`hours-${entry.row}`}>{__("Hours on {0}", [weekday(days[dayIndex])])}</Label>
										<Input
											id={`hours-${entry.row}`}
											type="number"
											inputMode="decimal"
											min={0}
											max={24}
											step={0.25}
											value={entry.hours[dayIndex] ? String(entry.hours[dayIndex]) : ""}
											disabled={!editable}
											onChange={(event) => change(setHours(entries, entry.row, dayIndex, event.target.value))}
										/>
									</div>
									{editable && entries.length > 1 && (
										<IconButton label={__("Remove Line")} variant="ghost" onClick={() => change(entries.filter((e) => e.row !== entry.row))}>
											<Trash2 />
										</IconButton>
									)}
								</div>
							</CardContent>
						</Card>
					))}

					{editable && (
						<div className="flex flex-wrap gap-2">
							<Button variant="outline" onClick={() => change([...entries, newEntry(entries, data.default_activity_type)])}>
								<Plus />
								{__("Add Line")}
							</Button>
							{data.previous_entries.length > 0 && (
								<Button variant="outline" onClick={() => change(copyLastWeek(data.previous_entries))}>
									<Copy />
									{__("Copy Last Week")}
								</Button>
							)}
						</div>
					)}

					{data.checks.length > 0 && (
						<Section title={__("Weekly Check")}>
							<List divided>
								{data.checks.map((check) => (
									<ListItem key={check} primary={check} />
								))}
							</List>
						</Section>
					)}
				</div>
			)}
		</FormPage>
	);
}

interface TimesheetRecordAnswer {
	name: string;
	employee_name: string;
	start_date: string;
	end_date: string;
	total_hours: number;
	docstatus: number;
	status: string;
	state: string;
	week_start: string | null;
	mine: boolean;
	lines: Array<{ date: string | null; activity_type: string | null; hours: number; description: string | null }>;
}

export function TimesheetRecord() {
	const go = useGo();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<TimesheetRecordAnswer>(M.timesheetRecord, { name });
	return (
		<DetailPage
			title={__("Timesheet")}
			subtitle={data && (data.mine ? name : data.employee_name)}
			meta={data && <Status value={data.docstatus === 1 ? "Approved" : data.state} />}
			onBack={() => go(P.timesheet)}
			actions={data?.mine && data.week_start ? <Button onClick={() => go(P.week(data.week_start!))}>{__("Open the Week")}</Button> : undefined}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-4">
					<DescriptionList
						items={[
							{ label: __("From"), value: formatDate(data.start_date) },
							{ label: __("To"), value: formatDate(data.end_date) },
							{ label: __("Total Hours"), value: String(data.total_hours ?? 0) },
						]}
					/>
					<List divided>
						{data.lines.map((l, i) => (
							<ListItem key={i} primary={__("{0} · {1} hours", [formatDate(l.date), String(l.hours)])} secondary={[l.activity_type, l.description].filter(Boolean).join(" · ")} />
						))}
					</List>
				</div>
			)}
		</DetailPage>
	);
}
