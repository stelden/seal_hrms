// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Money on the phone (HR_ON_MY_DESK §3): expense claims with receipts from the camera, advances and what
 * is left to settle, and payslips with the PDF in the client's own print format (PWA-7, chosen by the
 * server). Each new record is the person's own, in their company, to their approver (P5-2).
 */

import { useMemo } from "react";
import { useParams } from "react-router";
import { formatCurrency, formatDate, uploadFile, useGet, usePost } from "@stelden/seal-frontend";
import { DateInput, FileInput, FormActions, NumberInput, RowsInput, SealForm, SelectInput, TextInput, amount, required, useSealForm, z } from "@stelden/seal-frontend/forms";
import { Alert, Button, DescriptionList, DetailPage, EmptyState, FormPage, List, ListItem, ListPage, Section, __, useNotify } from "@stelden/seal-frontend/ui";
import { Download, HandCoins, Plus, Receipt, Wallet } from "@stelden/seal-frontend/icons";

import { M, payslipPdfUrl } from "../lib/api";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";
import { localToday } from "../lib/week";

// ---------------------------------------------------------------- expense claims

interface ExpenseRow {
	name: string;
	posting_date: string | null;
	creation: string;
	total_claimed_amount: number;
	currency: string;
	approval_status: string | null;
	status: string;
	docstatus: number;
}

export function ExpenseList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<ExpenseRow[]>(M.expenseList);
	return (
		<ListPage
			title={__("Expense Claims")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.expenseNew)}>
					<Plus />
					{__("New Expense Claim")}
				</Button>
			}
		>
			{hasLoaded && !data?.length ? (
				<EmptyState icon={<Receipt />} title={__("No expense claims yet")} description={__("Claim what you spent for work, with a photo of each receipt.")} />
			) : (
				<List divided>
					{(data ?? []).map((c) => (
						<ListItem
							key={c.name}
							primary={formatCurrency(c.total_claimed_amount, c.currency)}
							secondary={formatDate(c.posting_date || c.creation)}
							action={<Status value={c.docstatus === 0 ? c.approval_status || "Draft" : c.status} />}
							onClick={() => go(P.expenseRecord(c.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface ExpenseOptions {
	types: Array<{ name: string; description: string | null }>;
	currency: string;
	approver_name: string | null;
}

interface ExpenseValues {
	lines: Array<{ expense_date: string; expense_type: string; amount: number | null; description: string }>;
	remark: string;
	receipts: File[];
}

export function ExpenseForm() {
	const go = useGo();
	const notify = useNotify();
	const options = useGet<ExpenseOptions>(M.expenseOptions);
	const create = usePost<string>(M.claimExpenses);
	const schema = useMemo(
		() =>
			z.object({
				lines: z.array(z.object({ expense_type: required(() => __("Expense Type")), amount: amount(() => __("Amount"), { min: 0.01 }) }).loose()).min(1),
			}).loose(),
		[],
	);
	const form = useSealForm<ExpenseValues>({ schema, defaultValues: { lines: [{ expense_date: localToday(), expense_type: "", amount: null, description: "" }], remark: "", receipts: [] } });

	const submit = async (values: ExpenseValues) => {
		const name = await create.run({ lines: JSON.stringify(values.lines), remark: values.remark });
		const failed: string[] = [];
		for (const file of values.receipts ?? []) {
			try {
				await uploadFile(file, { doctype: "Expense Claim", docname: name, isPrivate: true });
			} catch {
				failed.push(file.name);
			}
		}
		if (failed.length) notify.warning(__("The claim was saved, but {0} receipts did not upload. Add them on a computer.", [String(failed.length)]));
		else notify.success(__("Claim sent to {0}.", [options.data?.approver_name ?? __("your expense approver")]));
		go(P.expenseRecord(name));
	};

	return (
		<FormPage title={__("New Expense Claim")} onBack={() => go(P.expenses)} loading={options.isLoading} error={options.error} onRetry={options.mutate}>
			{options.data && !options.data.approver_name && <Alert tone="warning">{__("Nobody approves your expense claims yet. Ask HR to set an expense approver.")}</Alert>}
			<SealForm form={form} onSubmit={submit}>
				<RowsInput
					name="lines"
					label={__("Expenses")}
					minRows={1}
					addLabel={__("Add an Expense")}
					newRow={() => ({ expense_date: localToday(), expense_type: "", amount: null, description: "" })}
					renderRow={(path) => (
						<>
							<SelectInput name={path("expense_type")} label={__("Expense Type")} required options={(options.data?.types ?? []).map((t) => ({ value: t.name, label: t.name, description: t.description ?? undefined }))} />
							<NumberInput name={path("amount")} label={__("Amount ({0})", [options.data?.currency ?? ""])} required min={0} step={0.01} />
							<DateInput name={path("expense_date")} label={__("Date")} maxDate={localToday()} />
							<TextInput name={path("description")} label={__("Description")} />
						</>
					)}
				/>
				<FileInput name="receipts" label={__("Receipts")} multiple upload={false} accept="image/*,application/pdf" hint={__("Take a photo of each receipt, or choose a file. Only you, your approver and HR can open them.")} />
				<TextInput name="remark" label={__("Note")} multiline rows={2} />
				<FormActions submitLabel={__("Send Claim")} onCancel={() => go(P.expenses)} />
			</SealForm>
		</FormPage>
	);
}

interface ExpenseRecordAnswer {
	name: string;
	employee_name: string;
	posting_date: string | null;
	currency: string;
	total_claimed_amount: number;
	total_sanctioned_amount: number;
	approval_status: string | null;
	status: string;
	docstatus: number;
	approver_name: string | null;
	remark: string | null;
	mine: boolean;
	expenses: Array<{ expense_date: string; expense_type: string; description: string | null; amount: number; sanctioned_amount: number }>;
	receipts: Array<{ name: string; file_name: string; file_url: string }>;
}

export function ExpenseRecord() {
	const go = useGo();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<ExpenseRecordAnswer>(M.expenseRecord, { name });
	return (
		<DetailPage
			title={data ? formatCurrency(data.total_claimed_amount, data.currency) : __("Expense Claim")}
			subtitle={data && (data.mine ? name : data.employee_name)}
			meta={data && <Status value={data.docstatus === 0 ? data.approval_status || "Draft" : data.status} />}
			onBack={() => go(P.expenses)}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-6">
					<DescriptionList
						items={[
							{ label: __("Claimed"), value: formatCurrency(data.total_claimed_amount, data.currency) },
							{ label: __("Approved Amount"), value: data.docstatus === 1 ? formatCurrency(data.total_sanctioned_amount, data.currency) : null, hideWhenEmpty: true },
							{ label: __("Expense Approver"), value: data.approver_name, hideWhenEmpty: true },
							{ label: __("Note"), value: data.remark, hideWhenEmpty: true, full: true },
						]}
					/>
					<Section title={__("Expenses")}>
						<List divided>
							{data.expenses.map((e, i) => (
								<ListItem key={i} primary={`${e.expense_type} · ${formatCurrency(e.amount, data.currency)}`} secondary={[formatDate(e.expense_date), e.description ?? ""].filter(Boolean).join(" · ")} />
							))}
						</List>
					</Section>
					{data.receipts.length > 0 && (
						<Section title={__("Receipts")}>
							<List divided>
								{data.receipts.map((r) => (
									<ListItem key={r.name} primary={r.file_name} href={r.file_url} />
								))}
							</List>
						</Section>
					)}
				</div>
			)}
		</DetailPage>
	);
}

// ---------------------------------------------------------------- advances

interface AdvanceRow {
	name: string;
	posting_date: string | null;
	purpose: string;
	advance_amount: number;
	paid_amount: number;
	to_settle: number;
	currency: string;
	status: string;
	docstatus: number;
}

export function AdvanceList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<AdvanceRow[]>(M.advanceList);
	return (
		<ListPage
			title={__("Advances")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.advanceNew)}>
					<Plus />
					{__("Request an Advance")}
				</Button>
			}
		>
			{hasLoaded && !data?.length ? (
				<EmptyState icon={<HandCoins />} title={__("No advances")} description={__("Money paid to you ahead of work shows here, with what is left to settle.")} />
			) : (
				<List divided>
					{(data ?? []).map((a) => (
						<ListItem
							key={a.name}
							primary={a.purpose}
							secondary={
								a.to_settle > 0
									? __("{0} · {1} left to settle", [formatCurrency(a.advance_amount, a.currency), formatCurrency(a.to_settle, a.currency)])
									: formatCurrency(a.advance_amount, a.currency)
							}
							action={<Status value={a.docstatus === 0 ? "Draft" : a.status} />}
							onClick={() => go(P.advanceRecord(a.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

export function AdvanceForm() {
	const go = useGo();
	const notify = useNotify();
	const request = usePost<string>(M.requestAdvance);
	const schema = useMemo(() => z.object({ purpose: required(() => __("Purpose")), amount: amount(() => __("Amount"), { min: 1 }) }), []);
	const form = useSealForm<{ purpose: string; amount: number | null }>({ schema, defaultValues: { purpose: "", amount: null } });
	return (
		<FormPage title={__("Request an Advance")} onBack={() => go(P.advances)}>
			<SealForm
				form={form}
				onSubmit={async (values) => {
					const name = await request.run({ purpose: values.purpose, amount: values.amount });
					notify.success(__("Advance requested."));
					go(P.advanceRecord(name));
				}}
			>
				<TextInput name="purpose" label={__("Purpose")} required multiline rows={2} hint={__("What the money is for, e.g. a field visit.")} />
				<NumberInput name="amount" label={__("Amount")} required min={1} step={1} />
				<FormActions submitLabel={__("Request")} onCancel={() => go(P.advances)} />
			</SealForm>
		</FormPage>
	);
}

interface AdvanceRecordAnswer extends AdvanceRow {
	employee_name: string;
	claimed_amount: number;
	return_amount: number;
	mine: boolean;
}

export function AdvanceRecord() {
	const go = useGo();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<AdvanceRecordAnswer>(M.advanceRecord, { name });
	return (
		<DetailPage
			title={data?.purpose ?? __("Advance")}
			subtitle={data && (data.mine ? name : data.employee_name)}
			meta={data && <Status value={data.docstatus === 0 ? "Draft" : data.status} />}
			onBack={() => go(P.advances)}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<DescriptionList
					items={[
						{ label: __("Amount"), value: formatCurrency(data.advance_amount, data.currency) },
						{ label: __("Paid"), value: formatCurrency(data.paid_amount, data.currency) },
						{ label: __("Claimed"), value: formatCurrency(data.claimed_amount, data.currency) },
						{ label: __("Returned"), value: formatCurrency(data.return_amount, data.currency) },
						{ label: __("Left to Settle"), value: formatCurrency(data.to_settle, data.currency) },
						{ label: __("Requested On"), value: formatDate(data.posting_date) },
					]}
				/>
			)}
		</DetailPage>
	);
}

// ---------------------------------------------------------------- payslips

interface SlipRow {
	name: string;
	start_date: string;
	end_date: string;
	net_pay: number;
	gross_pay: number;
	currency: string;
}

export function PayList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<SlipRow[]>(M.payslips);
	return (
		<ListPage title={__("Payslips")} onBack={() => go("")} loading={isLoading} error={error} onRetry={mutate}>
			{hasLoaded && !data?.length ? (
				<EmptyState icon={<Wallet />} title={__("No payslips yet")} description={__("Your payslips show here once payroll is run.")} />
			) : (
				<List divided>
					{(data ?? []).map((s) => (
						<ListItem
							key={s.name}
							primary={__("{0} to {1}", [formatDate(s.start_date), formatDate(s.end_date)])}
							secondary={__("Net pay {0}", [formatCurrency(s.net_pay, s.currency)])}
							onClick={() => go(P.payRecord(s.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface SlipAnswer extends SlipRow {
	employee_name: string;
	posting_date: string;
	total_deduction: number;
	earnings: Array<{ component: string; amount: number }>;
	deductions: Array<{ component: string; amount: number }>;
}

export function PayRecord() {
	const go = useGo();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<SlipAnswer>(M.payslipRecord, { name });
	return (
		<DetailPage
			title={data ? __("{0} to {1}", [formatDate(data.start_date), formatDate(data.end_date)]) : __("Payslip")}
			subtitle={data?.employee_name}
			onBack={() => go(P.pay)}
			actions={
				<Button href={payslipPdfUrl(name)} target="_blank" rel="noopener">
					<Download />
					{__("Open Payslip")}
				</Button>
			}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-6">
					<DescriptionList
						items={[
							{ label: __("Gross Pay"), value: formatCurrency(data.gross_pay, data.currency) },
							{ label: __("Total Deduction"), value: formatCurrency(data.total_deduction, data.currency) },
							{ label: __("Net Pay"), value: formatCurrency(data.net_pay, data.currency) },
						]}
					/>
					<Section title={__("Earnings")}>
						<List divided>
							{data.earnings.map((e) => (
								<ListItem key={e.component} primary={e.component} action={formatCurrency(e.amount, data.currency)} />
							))}
						</List>
					</Section>
					<Section title={__("Deductions")}>
						<List divided>
							{data.deductions.map((d) => (
								<ListItem key={d.component} primary={d.component} action={formatCurrency(d.amount, data.currency)} />
							))}
						</List>
					</Section>
				</div>
			)}
		</DetailPage>
	);
}
