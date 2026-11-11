// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Compensatory leave requests on the phone (Keith, 2026-11-11): Frappe HR's Compensatory Leave Request, for days
 * worked on a holiday or day off. The person's own, through their Employee record; sent at once to their leave
 * approver, who decides it from Approvals (seal_hrms.seal_hrms.compensatory_leave). Only the compensatory leave
 * types time off in lieu does not bank are offered (CL-1): extra hours on ordinary days stay a Time Off in Lieu
 * Claim.
 */

import { useMemo, useState } from "react";
import { useParams } from "react-router";
import { formatDate, useGet, usePost } from "@stelden/seal-frontend";
import { CheckboxInput, DateInput, FormActions, SealForm, SelectInput, TextInput, frappeDate, required, useSealForm, z } from "@stelden/seal-frontend/forms";
import { Alert, Button, ConfirmDialog, DescriptionList, DetailPage, EmptyState, FormPage, List, ListItem, ListPage, Text, __, useNotify } from "@stelden/seal-frontend/ui";
import { CalendarPlus, Hourglass, Plus } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { willApprove } from "../lib/approver";
import { workDays } from "../lib/forms";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";
import { localToday } from "../lib/week";

interface CompensatoryRow {
	name: string;
	leave_type: string;
	work_from_date: string;
	work_end_date: string;
	days: number;
	state: string;
}

/** "20 Oct 2026", or "20 Oct 2026 to 22 Oct 2026". */
function when(row: { work_from_date: string; work_end_date: string }): string {
	return row.work_from_date === row.work_end_date
		? formatDate(row.work_from_date)
		: __("{0} to {1}", [formatDate(row.work_from_date), formatDate(row.work_end_date)]);
}

export function CompensatoryList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<CompensatoryRow[]>(M.compensatoryList);
	return (
		<ListPage
			title={__("Compensatory Leave")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.compensatoryNew)}>
					<Plus />
					{__("New Request")}
				</Button>
			}
		>
			{hasLoaded && !data?.length ? (
				<EmptyState
					icon={<CalendarPlus />}
					title={__("No compensatory leave requests")}
					description={__("Worked on a public holiday or your day off? Ask for leave in return.")}
				/>
			) : (
				<List divided>
					{(data ?? []).map((r) => (
						<ListItem
							key={r.name}
							primary={r.leave_type}
							secondary={__("{0} · {1} days worked", [when(r), String(r.days)])}
							action={<Status value={r.state} />}
							onClick={() => go(P.compensatoryRecord(r.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface CompensatoryOptions {
	leave_types: string[];
	approver_name: string | null;
	workflow: boolean;
}

interface CompensatoryValues {
	leave_type: string;
	work_from_date: string;
	work_end_date: string;
	half_day: boolean;
	half_day_date: string;
	reason: string;
}

export function CompensatoryForm() {
	const go = useGo();
	const notify = useNotify();
	const options = useGet<CompensatoryOptions>(M.compensatoryOptions);
	const create = usePost<{ name: string; state: string }>(M.requestCompensatoryLeave);
	const schema = useMemo(
		() =>
			z
				.object({
					leave_type: required(() => __("Leave Type")),
					work_from_date: frappeDate(() => __("Work From Date")),
					work_end_date: frappeDate(() => __("Work End Date")),
					reason: required(() => __("Reason")),
				})
				.loose(),
		[],
	);
	const today = localToday();
	const form = useSealForm<CompensatoryValues>({
		schema,
		defaultValues: { leave_type: "", work_from_date: today, work_end_date: today, half_day: false, half_day_date: "", reason: "" },
	});
	const [from, to, halfDay] = [form.watch("work_from_date"), form.watch("work_end_date"), form.watch("half_day")];
	const days = workDays(from, to, halfDay);
	const types = options.data?.leave_types ?? [];

	return (
		<FormPage title={__("New Compensatory Leave Request")} onBack={() => go(P.compensatory)} loading={options.isLoading} error={options.error} onRetry={options.mutate}>
			{options.data && types.length === 0 ? (
				<EmptyState
					icon={<Hourglass />}
					title={__("Claim it as time off in lieu")}
					description={__("Your organisation gives time off for extra work through time off in lieu claims.")}
					action={<Button onClick={() => go(P.toilNew)}>{__("Claim Time Off")}</Button>}
				/>
			) : (
				<>
					{options.data && (
						<Alert tone={options.data.workflow || options.data.approver_name ? "info" : "warning"}>
							{options.data.workflow ? __("Your organisation's approval steps decide it.") : willApprove(options.data.approver_name)}
						</Alert>
					)}
					{create.errorMessage && <Alert tone="error">{create.errorMessage}</Alert>}
					<SealForm
						form={form}
						onSubmit={async (v) => {
							const answer = await create.run({
								leave_type: v.leave_type,
								work_from_date: v.work_from_date,
								work_end_date: v.work_end_date || v.work_from_date,
								reason: v.reason,
								half_day: v.half_day ? 1 : 0,
								half_day_date: v.half_day ? v.half_day_date || v.work_from_date : undefined,
							});
							notify.success(answer.state === "Waiting for Approval" ? __("Request sent.") : __("Request saved."));
							go(P.compensatoryRecord(answer.name));
						}}
					>
						<SelectInput name="leave_type" label={__("Leave Type")} required options={types.map((t) => ({ value: t, label: t }))} />
						<DateInput name="work_from_date" label={__("Work From Date")} required hint={__("The first holiday or day off you worked.")} />
						<DateInput name="work_end_date" label={__("Work End Date")} required minDate={from || undefined} />
						<CheckboxInput name="half_day" label={__("Half Day")} />
						{halfDay && from && to && from !== to && <DateInput name="half_day_date" label={__("Half Day Date")} minDate={from} maxDate={to} />}
						<TextInput name="reason" label={__("Reason")} required multiline rows={3} hint={__("What you worked on, so your approver can confirm it.")} />
						{days !== null && <Text muted>{__("{0} days of leave if approved.", [String(days)])}</Text>}
						<FormActions submitLabel={__("Send Request")} onCancel={() => go(P.compensatory)} />
					</SealForm>
				</>
			)}
		</FormPage>
	);
}

interface CompensatoryRecordAnswer {
	name: string;
	employee_name: string;
	leave_type: string;
	work_from_date: string;
	work_end_date: string;
	half_day: number;
	half_day_date: string | null;
	days: number;
	reason: string | null;
	state: string;
	docstatus: number;
	approver_name: string | null;
	note: string | null;
	mine: boolean;
	can_withdraw: boolean;
}

export function CompensatoryRecord() {
	const go = useGo();
	const notify = useNotify();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<CompensatoryRecordAnswer>(M.compensatoryRecord, { name });
	const withdraw = usePost<string>(M.compensatoryAction);
	const [confirmWithdraw, setConfirmWithdraw] = useState(false);
	return (
		<DetailPage
			title={__("Compensatory Leave Request")}
			subtitle={data && (data.mine ? name : data.employee_name)}
			meta={data && <Status value={data.state} />}
			onBack={() => go(P.compensatory)}
			actions={
				data?.can_withdraw ? (
					<Button variant="outline" onClick={() => setConfirmWithdraw(true)}>
						{__("Withdraw")}
					</Button>
				) : undefined
			}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-6">
					{withdraw.errorMessage && <Alert tone="error">{withdraw.errorMessage}</Alert>}
					{data.mine && data.state === "Waiting for Approval" && <Alert tone="info">{willApprove(data.approver_name)}</Alert>}
					{data.mine && data.state === "Rejected" && (
						<Alert tone="warning">{__("Not approved. Withdraw it, or ask your approver if something has changed.")}</Alert>
					)}
					<DescriptionList
						items={[
							{ label: __("Leave Type"), value: data.leave_type },
							{ label: __("Work From Date"), value: formatDate(data.work_from_date) },
							{ label: __("Work End Date"), value: formatDate(data.work_end_date) },
							{ label: __("Half Day Date"), value: data.half_day && data.half_day_date ? formatDate(data.half_day_date) : null, hideWhenEmpty: true },
							{ label: __("Days"), value: String(data.days) },
							{ label: __("Approver"), value: data.approver_name, hideWhenEmpty: true },
							{ label: __("Reason"), value: data.reason, hideWhenEmpty: true, full: true },
							{ label: __("Decision Note"), value: data.note, hideWhenEmpty: true, full: true },
						]}
					/>
					{!data.mine && data.state === "Waiting for Approval" && <Text muted>{__("Decide this request from Approvals.")}</Text>}
				</div>
			)}
			<ConfirmDialog
				open={confirmWithdraw}
				onClose={() => setConfirmWithdraw(false)}
				title={__("Withdraw this request?")}
				confirmLabel={__("Withdraw")}
				destructive
				onConfirm={async () => {
					await withdraw.run({ name, action: "Withdraw" });
					notify.success(__("Request withdrawn."));
					go(P.compensatory);
				}}
			>
				{__("It is deleted, and nobody will act on it.")}
			</ConfirmDialog>
		</DetailPage>
	);
}
