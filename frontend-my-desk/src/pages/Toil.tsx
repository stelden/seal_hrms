// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Time off in lieu on the phone (HR_ON_MY_DESK §3): what is left and when it lapses, the claims, a claim
 * as a list of days (date, hours, what the work was) with Fill from Records, where a claim is (Now /
 * Next / Do, worked out by the server for this viewer), sending it on, and Apply for Leave from what an
 * approved claim gave.
 */

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router";
import { formatDate, useFrappeCall, useGet, usePost } from "@stelden/seal-frontend";
import { DateInput, FormActions, NumberInput, RowsInput, SealForm, TextInput, useSealForm } from "@stelden/seal-frontend/forms";
import {
	Alert,
	Button,
	DescriptionList,
	DetailPage,
	EmptyState,
	FormPage,
	List,
	ListItem,
	ListPage,
	Section,
	StatCard,
	StatGrid,
	Text,
	__,
	useNotify,
} from "@stelden/seal-frontend/ui";
import { Hourglass, Plus } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { willApprove } from "../lib/approver";
import { mergeFill, type ToilLine } from "../lib/forms";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";
import { addDays, localToday } from "../lib/week";

interface ToilListAnswer {
	employee: string;
	eligible: boolean;
	/** Who will approve a claim the person sends. */
	approver_name?: string | null;
	leave_type: string | null;
	mode: string | null;
	from_attendance: boolean;
	from_timesheets: boolean;
	left: number;
	lapsing: number;
	first_lapse: string | null;
	claims: Array<{ name: string; status: string; docstatus: number; total_hours: number; days: number; days_left: number | null; lapses_on: string | null; creation: string }>;
}

export function ToilList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<ToilListAnswer>(M.toilList);
	return (
		<ListPage
			title={__("Time Off in Lieu")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				data?.eligible ? (
					<Button onClick={() => go(P.toilNew)}>
						<Plus />
						{__("Claim Time Off")}
					</Button>
				) : undefined
			}
		>
			{data && !data.eligible && (
				<Alert tone="info">{__("Your grade does not bank extra hours as time off. Ask HR if you think it should.")}</Alert>
			)}
			{data?.eligible && (
				<StatGrid columns={2}>
					<StatCard label={__("Days Left")} value={String(data.left)} />
					<StatCard
						label={__("Lapsing in 30 Days")}
						value={String(data.lapsing)}
						hint={data.first_lapse ? __("First on {0}", [formatDate(data.first_lapse)]) : undefined}
					/>
				</StatGrid>
			)}
			{hasLoaded && !data?.claims.length ? (
				<EmptyState icon={<Hourglass />} title={__("No claims yet")} description={__("Claim the extra hours you worked, a day at a time.")} />
			) : (
				<List divided>
					{(data?.claims ?? []).map((c) => (
						<ListItem
							key={c.name}
							primary={__("{0} hours · {1} days", [String(c.total_hours ?? 0), String(c.days ?? 0)])}
							secondary={
								c.status === "Approved" && c.lapses_on
									? __("{0} days left, usable until {1}", [String(c.days_left ?? 0), formatDate(c.lapses_on)])
									: formatDate(c.creation)
							}
							action={<Status value={c.status} />}
							onClick={() => go(P.toilRecord(c.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface ToilValues {
	lines: ToilLine[];
	note: string;
}

const blankLine = (): ToilLine => ({ work_date: "", hours: null, work_done: "" });

export function ToilForm() {
	const go = useGo();
	const notify = useNotify();
	const [params] = useSearchParams();
	const editing = params.get("claim");
	const info = useGet<ToilListAnswer>(M.toilList);
	const existing = useGet<ToilRecordAnswer>(M.toilRecord, { name: editing ?? "" }, { enabled: !!editing });
	const save = usePost<string>(M.saveToilClaim);
	const api = useFrappeCall();
	const [filling, setFilling] = useState(false);
	const [fillNote, setFillNote] = useState<string | null>(null);
	const form = useSealForm<ToilValues>({ defaultValues: { lines: [blankLine()], note: "" } });

	useEffect(() => {
		if (existing.data) form.reset({ lines: existing.data.lines.map((l) => ({ work_date: l.work_date, hours: l.hours, work_done: l.work_done })), note: existing.data.note ?? "" });
	}, [existing.data, form]);

	// Fill from Records: a click fetches once, so an imperative call, not a hook (REACT_SDK_RULES §8).
	const fill = async () => {
		if (!info.data) return;
		setFilling(true);
		setFillNote(null);
		try {
			const source = info.data.from_attendance ? "Attendance" : "Timesheet";
			const today = localToday();
			const rows = (await api.get<Array<{ work_date: string; hours: number }>>(M.extraTime, { employee: info.data.employee, from_date: addDays(today, -30), to_date: today, source })) ?? [];
			const current = form.getValues("lines").filter((l) => l.work_date);
			form.setValue("lines", mergeFill(current, rows), { shouldDirty: true });
			setFillNote(rows.length ? __("{0} days found in the last 30 days. Say what the work was on each.", [String(rows.length)]) : __("The records show no extra hours you have not claimed in the last 30 days."));
		} catch {
			setFillNote(__("The records could not be read. Enter the days yourself."));
		} finally {
			setFilling(false);
		}
	};

	const submit = async (values: ToilValues) => {
		const name = await save.run({ lines: JSON.stringify(values.lines.filter((l) => l.work_date)), note: values.note, name: editing ?? undefined });
		notify.success(__("Claim saved. Send it when it is ready."));
		go(P.toilRecord(name));
	};

	const canFill = info.data && (info.data.from_attendance || info.data.from_timesheets);
	return (
		<FormPage
			title={editing ? __("Change Claim") : __("Claim Time Off")}
			onBack={() => go(editing ? P.toilRecord(editing) : P.toil)}
			loading={info.isLoading || existing.isLoading}
			error={info.error ?? existing.error}
			actions={
				canFill ? (
					<Button variant="outline" loading={filling} onClick={fill}>
						{__("Fill from Records")}
					</Button>
				) : undefined
			}
		>
			{info.data && <Alert tone={info.data.approver_name ? "info" : "warning"}>{willApprove(info.data.approver_name)}</Alert>}
			{fillNote && <Alert tone="info">{fillNote}</Alert>}
			<SealForm form={form} onSubmit={submit}>
				<RowsInput
					name="lines"
					label={__("Days Worked")}
					minRows={1}
					addLabel={__("Add a Day")}
					newRow={blankLine}
					renderRow={(path) => (
						<>
							<DateInput name={path("work_date")} label={__("Date")} required maxDate={localToday()} />
							<NumberInput name={path("hours")} label={__("Hours Worked")} min={0} max={24} step={0.25} />
							<TextInput name={path("work_done")} label={__("Work Done")} required multiline rows={2} />
						</>
					)}
				/>
				<TextInput name="note" label={__("Note")} multiline rows={2} hint={__("Anything your approver should know about these days.")} />
				<FormActions submitLabel={__("Save Claim")} onCancel={() => go(editing ? P.toilRecord(editing) : P.toil)} />
			</SealForm>
		</FormPage>
	);
}

interface ToilRecordAnswer {
	name: string;
	employee_name: string;
	status: string;
	docstatus: number;
	approver_name: string | null;
	note: string | null;
	decision_note: string | null;
	total_hours: number;
	credited_hours: number;
	days: number;
	days_left: number | null;
	lapses_on: string | null;
	leave_type: string | null;
	lines: Array<{ work_date: string; hours: number; planned_hours: number | null; work_done: string; day_kind: string | null; credited_hours: number; supported_by: string | null }>;
	stage: { tone: "info" | "success" | "warning" | "error"; items: Array<{ label: string; text: string }> };
	mine: boolean;
	can_edit: boolean;
	actions: string[];
}

export function ToilRecord() {
	const go = useGo();
	const notify = useNotify();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<ToilRecordAnswer>(M.toilRecord, { name });
	const action = usePost<string>(M.toilAction);

	const send = async (step: string) => {
		try {
			await action.run({ name, action: step });
			notify.success(__("Claim sent."));
			await mutate();
		} catch {
			/* the message shows above the claim */
		}
	};

	const header = data && (
		<div className="flex gap-2">
			{data.can_edit && (
				<Button variant="outline" onClick={() => go(`${P.toilNew}?claim=${encodeURIComponent(name)}`)}>
					{__("Change")}
				</Button>
			)}
			{data.actions.map((a) => (
				<Button key={a} loading={action.loading} onClick={() => send(a)}>
					{a === "Send for Authorisation" ? __("Send for Authorisation") : __("Send for Approval")}
				</Button>
			))}
			{data.mine && data.status === "Approved" && (data.days_left ?? 0) > 0 && data.leave_type && (
				<Button onClick={() => go(`${P.leaveNew}?type=${encodeURIComponent(data.leave_type ?? "")}`)}>{__("Apply for Leave")}</Button>
			)}
		</div>
	);

	return (
		<DetailPage
			title={__("Time Off in Lieu Claim")}
			subtitle={data && !data.mine ? data.employee_name : name}
			meta={data && <Status value={data.status} />}
			onBack={() => go(P.toil)}
			actions={header}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-6">
					{action.errorMessage && <Alert tone="error">{action.errorMessage}</Alert>}
					{data.stage.items.length > 0 && (
						<Alert tone={data.stage.tone}>
							<div className="flex flex-col gap-1">
								{data.stage.items.map((item) => (
									<Text key={item.label}>
										<strong>{item.label}:</strong> {item.text}
									</Text>
								))}
							</div>
						</Alert>
					)}
					<DescriptionList
						items={[
							{ label: __("Total Extra Hours"), value: String(data.total_hours ?? 0) },
							{ label: __("Time Off (Days)"), value: String(data.days ?? 0) },
							{ label: __("Approver"), value: data.approver_name, hideWhenEmpty: true },
							{ label: __("Days Left"), value: data.days_left === null ? null : String(data.days_left), hideWhenEmpty: true },
							{ label: __("Usable Until"), value: data.lapses_on ? formatDate(data.lapses_on) : null, hideWhenEmpty: true },
							{ label: __("Note"), value: data.note, hideWhenEmpty: true, full: true },
							{ label: __("Approver's Note"), value: data.decision_note, hideWhenEmpty: true, full: true },
						]}
					/>
					<Section title={__("Days Worked")}>
						<List divided>
							{data.lines.map((l) => (
								<ListItem
									key={l.work_date}
									primary={__("{0} · {1} hours", [formatDate(l.work_date), String(l.hours ?? l.planned_hours ?? 0)])}
									secondary={[l.work_done, l.supported_by ?? ""].filter(Boolean).join(" · ")}
								/>
							))}
						</List>
					</Section>
				</div>
			)}
		</DetailPage>
	);
}
