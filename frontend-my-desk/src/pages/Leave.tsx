// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Leave: the person's applications, applying (with the handover in the same flow when the company's
 * rule covers the leave, HR_ON_MY_DESK §3), and one application with its handover. Minimum notice,
 * posting-date and lapsed-time rules are the server's: their messages show as they come.
 */

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router";
import { formatDate, useGet, usePost } from "@stelden/seal-frontend";
import { useShell } from "@stelden/seal-frontend/section";
import {
	AutocompleteInput,
	CheckboxInput,
	DateInput,
	SealForm,
	SelectInput,
	FormActions,
	FormSection,
	TextInput,
	frappeDate,
	required,
	useSealForm,
	z,
} from "@stelden/seal-frontend/forms";
import {
	Alert,
	Button,
	DescriptionList,
	DetailPage,
	EmptyState,
	FilterChips,
	FormPage,
	List,
	ListItem,
	ListPage,
	Text,
	__,
	useNotify,
} from "@stelden/seal-frontend/ui";
import { CalendarDays, Plus } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { savedDay, useDraft } from "../lib/drafts";
import { handoverStep } from "../lib/forms";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";

interface LeaveRow {
	name: string;
	leave_type: string;
	from_date: string;
	to_date: string;
	total_leave_days: number;
	status: string;
	docstatus: number;
	handover: { name: string; status: string; stand_in: string } | null;
}

type Filter = "all" | "open" | "decided";

export function LeaveList() {
	const go = useGo();
	const [filter, setFilter] = useState<Filter>("all");
	const { data, isLoading, error, mutate, hasLoaded } = useGet<LeaveRow[]>(M.leaveList);
	const rows = data ?? [];
	const open = rows.filter((r) => r.status === "Open" && r.docstatus === 0);
	const shown = filter === "open" ? open : filter === "decided" ? rows.filter((r) => !open.includes(r)) : rows;
	return (
		<ListPage
			title={__("Leave")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.leaveNew)}>
					<Plus />
					{__("Apply for Leave")}
				</Button>
			}
			toolbar={
				<FilterChips
					label={__("Show")}
					value={filter}
					onChange={setFilter}
					options={[
						{ value: "all", label: __("All"), count: rows.length },
						{ value: "open", label: __("Waiting"), count: open.length },
						{ value: "decided", label: __("Decided"), count: rows.length - open.length },
					]}
				/>
			}
		>
			{hasLoaded && shown.length === 0 ? (
				<EmptyState icon={<CalendarDays />} title={__("No leave here")} description={__("Leave you apply for shows here until it is decided, and after.")} />
			) : (
				<List divided>
					{shown.map((r) => (
						<ListItem
							key={r.name}
							primary={r.leave_type}
							secondary={
								r.handover
									? __("{0} to {1} · {2} days · covered by {3}", [formatDate(r.from_date), formatDate(r.to_date), String(r.total_leave_days), r.handover.stand_in])
									: __("{0} to {1} · {2} days", [formatDate(r.from_date), formatDate(r.to_date), String(r.total_leave_days)])
							}
							action={<Status value={r.status} />}
							onClick={() => go(P.leaveRecord(r.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface LeaveOptions {
	leave_types: Array<{ name: string; left: number | null; allocated: number | null }>;
	approver_name: string | null;
	days: number | null;
	handover: { needed: boolean; required: boolean; rule: string | null };
	work: Array<{ todo: string; description: string; due_date: string | null }>;
	approvals: Array<{ authority: string; authority_label: string }>;
}

interface LeaveValues {
	leave_type: string;
	from_date: string;
	to_date: string;
	half_day: boolean;
	description: string;
	stand_in: string;
	handover_notes: string;
	todos: string[];
	approvals: string[];
}

export function LeaveForm() {
	const go = useGo();
	const notify = useNotify();
	const [params] = useSearchParams();
	const schema = useMemo(
		() =>
			z.object({
				leave_type: required(() => __("Leave Type")),
				from_date: frappeDate(() => __("From Date")),
				to_date: frappeDate(() => __("To Date")),
			}),
		[],
	);
	const blank = (): LeaveValues => ({ leave_type: params.get("type") ?? "", from_date: "", to_date: "", half_day: false, description: "", stand_in: "", handover_notes: "", todos: [], approvals: [] });
	const form = useSealForm<LeaveValues>({ schema: schema.passthrough(), defaultValues: blank() });
	// The application and its handover stay on the phone until applied for (P6 drafts). A leave type asked for
	// in the link ("Apply for Leave" from an approved time off claim) starts afresh rather than restoring.
	const draft = useDraft<LeaveValues>(useShell().user, "leave-application", "new");
	const [restoredAt, setRestoredAt] = useState<number | null>(null);
	useEffect(() => {
		if (draft.restored?.value && !params.get("type")) {
			form.reset({ ...blank(), ...draft.restored.value });
			setRestoredAt(draft.restored.saved);
		}
		draft.dismiss();
		const watching = form.watch((values) => draft.keep({ ...blank(), ...(values as Partial<LeaveValues>) }));
		return () => watching.unsubscribe();
		// Deliberately not every dependency: once, when the screen opens
	}, []);
	const startAgain = () => {
		draft.clear();
		setRestoredAt(null);
		form.reset(blank());
	};
	const [leaveType, fromDate, toDate, halfDay] = form.watch(["leave_type", "from_date", "to_date", "half_day"]);
	const ready = !!(leaveType && fromDate && toDate);
	// Two reads of the same endpoint: the leave types once, and what the chosen dates mean (days, approver,
	// handover) as they change. One read keyed on the dates emptied the type list while it reloaded, and
	// the select dropped the chosen type with it (found by the P6 walk in the real shell).
	const types = useGet<LeaveOptions>(M.leaveOptions);
	const detail = useGet<LeaveOptions>(M.leaveOptions, { leave_type: leaveType, from_date: fromDate, to_date: toDate, half_day: halfDay ? 1 : 0 }, { enabled: ready });
	const options = { ...detail, data: ready ? detail.data : undefined };
	const colleagues = useGet<Array<{ name: string; employee_name: string }>>(M.colleagues, {}, { enabled: !!options.data?.handover.needed });
	const apply = usePost<{ name: string; handover: string | null }>(M.applyForLeave);
	const step = handoverStep(ready ? options.data?.handover : undefined);
	const chosen = (options.data ?? types.data)?.leave_types.find((t) => t.name === leaveType);

	const submit = async (values: LeaveValues) => {
		if (step.standInRequired && !values.stand_in) return { errors: { stand_in: __("Your company asks for cover on this leave. Choose who will cover your work.") } };
		const answer = await apply.run({
			leave_type: values.leave_type,
			from_date: values.from_date,
			to_date: values.to_date,
			half_day: values.half_day ? 1 : 0,
			description: values.description,
			stand_in: step.show ? values.stand_in || undefined : undefined,
			handover_notes: values.handover_notes,
			todos: JSON.stringify(values.todos),
			approvals: JSON.stringify(values.approvals),
		});
		draft.clear(); // applied for: nothing left to keep
		notify.success(answer.handover ? __("Leave applied for, and the handover sent to your stand-in.") : __("Leave applied for."));
		go(P.leaveRecord(answer.name));
	};

	return (
		<FormPage title={__("Apply for Leave")} onBack={() => go(P.leave)} loading={types.isLoading && !types.data} error={types.error} onRetry={types.mutate}>
			{restoredAt !== null && (
				<Alert tone="info" title={__("Restored From This Phone")} action={<Button onClick={startAgain}>{__("Start Again")}</Button>}>
					{__("You started this application on {0} and had not sent it.", [formatDate(savedDay(restoredAt))])}
				</Alert>
			)}
			<SealForm form={form} onSubmit={submit}>
				{/* One page, the handover as a section beneath the leave, rather than the library's Wizard: its
				    Continue button becomes Apply in the same click and sent the leave without its handover
				    (found by the P6 walk in the real shell; P6-6). */}
				<FormSection title={__("Leave")}>
					<div className="flex flex-col gap-4">
									<SelectInput
										name="leave_type"
										label={__("Leave Type")}
										required
										options={(types.data?.leave_types ?? []).map((t) => ({
											value: t.name,
											label: t.name,
											description: t.left === null ? __("Unpaid") : __("{0} days left", [String(t.left)]),
										}))}
										hint={chosen && chosen.left !== null ? __("{0} days left", [String(chosen.left)]) : undefined}
									/>
									<DateInput name="from_date" label={__("From Date")} required />
									<DateInput name="to_date" label={__("To Date")} required minDate={fromDate || undefined} />
									<CheckboxInput name="half_day" label={__("Half Day")} hint={__("Only the first day is a half day.")} />
									<TextInput name="description" label={__("Reason")} multiline rows={3} />
									{ready && options.data && (
										<Alert tone="info">
											{options.data.days !== null
												? __("{0} days, approved by {1}.", [String(options.data.days), options.data.approver_name ?? __("your leave approver")])
												: __("Approved by {0}.", [options.data.approver_name ?? __("your leave approver")])}
										</Alert>
									)}
								</div>
				</FormSection>
				{step.show && (
					<FormSection
						title={__("Handover")}
						description={
							step.standInRequired
								? __("Your company asks for cover on leave like this. Your stand-in is asked to agree before the leave is approved.")
								: __("Your company suggests arranging cover. You can leave this out.")
						}
					>
						<div className="flex flex-col gap-4">
									<AutocompleteInput
										name="stand_in"
										label={__("Stand-in")}
										required={step.standInRequired}
										options={(colleagues.data ?? []).map((c) => ({ value: c.name, label: c.employee_name }))}
										hint={__("A colleague in your company who is not away at the same time.")}
									/>
									<TextInput name="handover_notes" label={__("Handover Notes")} multiline rows={4} hint={__("What your stand-in needs to know.")} />
									{(options.data?.work.length ?? 0) > 0 && (
										<AutocompleteInput
											name="todos"
											multiple
											label={__("Work to Hand Over")}
											options={(options.data?.work ?? []).map((w) => ({ value: w.todo, label: w.description, description: w.due_date ? __("Due {0}", [formatDate(w.due_date)]) : undefined }))}
											hint={__("Open items on your work list. Your stand-in gets them while you are away.")}
										/>
									)}
									{(options.data?.approvals.length ?? 0) > 0 && (
										<AutocompleteInput
											name="approvals"
											multiple
											label={__("Approvals to Hand Over")}
											options={(options.data?.approvals ?? []).map((a) => ({ value: a.authority, label: a.authority_label }))}
											hint={__("Your stand-in approves these in your place, once they agree.")}
										/>
									)}
								</div>
					</FormSection>
				)}
				<FormActions submitLabel={__("Apply")} onCancel={() => go(P.leave)} />
			</SealForm>
		</FormPage>
	);
}

interface LeaveRecordAnswer {
	name: string;
	employee_name: string;
	leave_type: string;
	from_date: string;
	to_date: string;
	total_leave_days: number;
	half_day: number;
	description: string | null;
	status: string;
	docstatus: number;
	leave_approver_name: string | null;
	posting_date: string;
	mine: boolean;
	handover: { name: string; status: string; stand_in: string } | null;
}

export function LeaveRecord() {
	const go = useGo();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<LeaveRecordAnswer>(M.leaveRecord, { name });
	return (
		<DetailPage
			title={data ? data.leave_type : __("Leave")}
			subtitle={data && !data.mine ? data.employee_name : name}
			meta={data && <Status value={data.status} />}
			onBack={() => go(P.leave)}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-4">
					<DescriptionList
						items={[
							{ label: __("From Date"), value: formatDate(data.from_date) },
							{ label: __("To Date"), value: formatDate(data.to_date) },
							{ label: __("Days"), value: String(data.total_leave_days) },
							{ label: __("Half Day"), value: data.half_day ? __("Yes") : __("No") },
							{ label: __("Leave Approver"), value: data.leave_approver_name, hideWhenEmpty: true },
							{ label: __("Applied On"), value: formatDate(data.posting_date) },
							{ label: __("Reason"), value: data.description, hideWhenEmpty: true, full: true },
						]}
					/>
					{data.handover ? (
						<List divided>
							<ListItem
								primary={__("Handover to {0}", [data.handover.stand_in])}
								action={<Status value={data.handover.status} />}
								onClick={() => go(P.handover(data.handover!.name))}
							/>
						</List>
					) : (
						<Text muted>{__("No handover for this leave.")}</Text>
					)}
				</div>
			)}
		</DetailPage>
	);
}
