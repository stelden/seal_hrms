// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * My Details (HR_ON_MY_DESK §3, PWA-9): the person's own details, contact, dependants and beneficiaries,
 * and where they are paid, every number masked to its last four (the server never sends more). A change
 * to where pay goes is a request HR confirms on the desk; sending it asks the person to confirm it is
 * them (fingerprint or password, through the shell) and tells their old number and address.
 */

import { useMemo, useState } from "react";
import { useParams } from "react-router";
import { formatDate, formatDateTime, uploadFile, useGet, usePost } from "@stelden/seal-frontend";
import { FileInput, FormActions, MobileInputKE, RadioInput, SealForm, SelectInput, TextInput, useSealForm } from "@stelden/seal-frontend/forms";
import { useShell } from "@stelden/seal-frontend/section";
import { Alert, Button, ConfirmDialog, DescriptionList, DetailPage, FormPage, Input, Label, List, ListItem, SealDialog, Section, Text, __, useNotify } from "@stelden/seal-frontend/ui";

import { M } from "../lib/api";
import { payoutMissing, type PayoutChange } from "../lib/forms";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";
import { VerificationCancelled, withVerification } from "../lib/verify";

interface DetailsAnswer {
	employee: { name: string; employee_name: string; designation: string | null; department: string | null; company: string; date_of_joining: string | null; company_email: string | null; personal_email: string | null };
	mobile_no: string | null;
	has_contact: boolean;
	dependants: Array<{ name: string; full_name: string; type: string; relationship: string; dob: string | null }>;
	payout: { bank: string | null; account_name: string | null; account_no: string | null; mobile_no: string | null };
	payout_request: { name: string; status: string; change: string } | null;
	payout_requests: Array<{ name: string; status: string; change: string; creation: string }>;
}

export function MyDetails() {
	const go = useGo();
	const notify = useNotify();
	const { data, isLoading, error, mutate } = useGet<DetailsAnswer>(M.myDetails);
	const update = usePost<{ mobile_no: string }>(M.updateMyContact);
	const [editing, setEditing] = useState(false);
	const [mobile, setMobile] = useState("");

	return (
		<DetailPage title={__("My Details")} subtitle={data?.employee.employee_name} onBack={() => go("")} loading={isLoading} error={error} onRetry={mutate}>
			{data && (
				<div className="flex flex-col gap-6">
					<DescriptionList
						items={[
							{ label: __("Employee ID"), value: data.employee.name },
							{ label: __("Designation"), value: data.employee.designation, hideWhenEmpty: true },
							{ label: __("Department"), value: data.employee.department, hideWhenEmpty: true },
							{ label: __("Company"), value: data.employee.company },
							{ label: __("Date of Joining"), value: data.employee.date_of_joining ? formatDate(data.employee.date_of_joining) : null, hideWhenEmpty: true },
							{ label: __("Company Email"), value: data.employee.company_email, hideWhenEmpty: true },
							{ label: __("Personal Email"), value: data.employee.personal_email, hideWhenEmpty: true },
						]}
					/>

					<Section
						title={__("Contact")}
						action={
							data.has_contact ? (
								<Button variant="outline" onClick={() => setEditing(true)}>
									{__("Change Mobile Number")}
								</Button>
							) : undefined
						}
					>
						<DescriptionList items={[{ label: __("Mobile No."), value: data.mobile_no ?? __("None yet") }]} />
						{!data.has_contact && <Text muted>{__("HR has not linked a contact to your record yet; ask them to.")}</Text>}
					</Section>

					<Section title={__("Dependants and Beneficiaries")}>
						{data.dependants.length === 0 ? (
							<Text muted>{__("None recorded. HR records dependants and beneficiaries.")}</Text>
						) : (
							<List divided>
								{data.dependants.map((d) => (
									<ListItem key={d.name} primary={d.full_name} secondary={[d.relationship, d.type, d.dob ? formatDate(d.dob) : ""].filter(Boolean).join(" · ")} />
								))}
							</List>
						)}
					</Section>

					<Section
						title={__("Payout Details")}
						subtitle={__("Where your pay goes. Only the last four digits are shown.")}
						action={
							<Button disabled={!!data.payout_request} onClick={() => go(P.payoutNew)}>
								{__("Request a Change")}
							</Button>
						}
					>
						<DescriptionList
							items={[
								{ label: __("Bank"), value: data.payout.bank ?? __("None") },
								{ label: __("Account No."), value: data.payout.account_no, hideWhenEmpty: true },
								{ label: __("Account Name"), value: data.payout.account_name, hideWhenEmpty: true },
								{ label: __("Mobile Money"), value: data.payout.mobile_no ?? __("None") },
							]}
						/>
						{data.payout_requests.length > 0 && (
							<List divided>
								{data.payout_requests.map((r) => (
									<ListItem
										key={r.name}
										primary={r.change === "Mobile Money" ? __("Change to Mobile Money") : __("Change of Bank Account")}
										secondary={formatDateTime(r.creation)}
										action={<Status value={r.status} />}
										onClick={() => go(P.payoutRecord(r.name))}
									/>
								))}
							</List>
						)}
					</Section>
				</div>
			)}

			<SealDialog
				open={editing}
				onClose={() => setEditing(false)}
				title={__("Change Mobile Number")}
				description={__("Your contact number at work. Where your pay goes changes only by a request to HR.")}
				actions={
					<>
						<Button variant="outline" onClick={() => setEditing(false)}>
							{__("Cancel")}
						</Button>
						<Button
							loading={update.loading}
							disabled={!mobile.trim()}
							onClick={async () => {
								try {
									await update.run({ mobile_no: mobile });
									notify.success(__("Mobile number changed."));
									setEditing(false);
									setMobile("");
									await mutate();
								} catch {
									/* shown in the dialog */
								}
							}}
						>
							{__("Save")}
						</Button>
					</>
				}
			>
				<div className="flex flex-col gap-2">
					{update.errorMessage && <Alert tone="error">{update.errorMessage}</Alert>}
					<Label htmlFor="new-mobile">{__("New Mobile No.")}</Label>
					<Input id="new-mobile" type="tel" inputMode="tel" autoComplete="tel" value={mobile} onChange={(e) => setMobile(e.target.value)} />
				</div>
			</SealDialog>
		</DetailPage>
	);
}

interface PayoutValues {
	change: PayoutChange;
	bank: string;
	bank_account_no: string;
	branch_code: string;
	account_name: string;
	mobile_no: string;
	evidence: File | null;
	reason: string;
}

export function PayoutForm() {
	const go = useGo();
	const shell = useShell();
	const notify = useNotify();
	const options = useGet<{ banks: string[] }>(M.payoutOptions);
	const create = usePost<string>(M.requestPayoutChange);
	const setEvidence = usePost(M.setPayoutEvidence);
	const send = usePost<string>(M.sendPayoutChange);
	const form = useSealForm<PayoutValues>({
		defaultValues: { change: "Bank Account", bank: "", bank_account_no: "", branch_code: "", account_name: "", mobile_no: "", evidence: null, reason: "" },
	});
	const change = form.watch("change");
	const labels = useMemo(
		() => ({ bank: __("Bank"), bank_account_no: __("Account No."), account_name: __("Account Name"), mobile_no: __("Mobile No."), evidence: __("Evidence") }),
		[],
	);

	const submit = async (v: PayoutValues) => {
		const missing = payoutMissing(v);
		if (missing.length) return { errors: Object.fromEntries(missing.map((f) => [f, __("{0} is needed.", [labels[f as keyof typeof labels]])])) };
		const name = await create.run({
			change: v.change,
			bank: v.change === "Bank Account" ? v.bank : undefined,
			bank_account_no: v.change === "Bank Account" ? v.bank_account_no : undefined,
			branch_code: v.change === "Bank Account" ? v.branch_code : undefined,
			account_name: v.change === "Bank Account" ? v.account_name : undefined,
			mobile_no: v.change === "Mobile Money" ? v.mobile_no : undefined,
			reason: v.reason,
		});
		if (v.change === "Bank Account" && v.evidence) {
			const file = await uploadFile(v.evidence, { doctype: "Payout Change Request", docname: name, fieldname: "evidence", isPrivate: true });
			await setEvidence.run({ name, file_url: file.file_url });
		}
		try {
			await withVerification(() => send.run({ name }), shell.verify);
			notify.success(__("Sent to HR. Nothing changes until HR confirms it."));
		} catch (thrown) {
			if (!(thrown instanceof VerificationCancelled)) throw thrown;
			notify.info(__("Saved, not sent. Open it from My Details to send it."));
		}
		go(P.payoutRecord(name));
	};

	return (
		<FormPage title={__("Request a Change")} subtitle={__("Where your pay goes")} onBack={() => go(P.me)} loading={options.isLoading} error={options.error} onRetry={options.mutate}>
			<Alert tone="info">{__("HR confirms every change before any pay goes there. We also tell your current number and email, in case this was not you.")}</Alert>
			<SealForm form={form} onSubmit={submit}>
				<RadioInput
					name="change"
					label={__("Change")}
					required
					row
					options={[
						{ value: "Bank Account", label: __("Bank Account") },
						{ value: "Mobile Money", label: __("Mobile Money") },
					]}
				/>
				{change === "Bank Account" ? (
					<>
						<SelectInput name="bank" label={__("Bank")} required options={(options.data?.banks ?? []).map((b) => ({ value: b, label: b }))} />
						<TextInput name="bank_account_no" label={__("Account No.")} required />
						<TextInput name="branch_code" label={__("Branch")} />
						<TextInput name="account_name" label={__("Account Name")} required hint={__("As the bank has it. It must be in your own name.")} />
						<FileInput name="evidence" label={__("Evidence")} required upload={false} accept="image/*,application/pdf" hint={__("A bank letter or the top of a statement, showing the account in your name.")} />
					</>
				) : (
					<MobileInputKE name="mobile_no" label={__("Mobile No.")} required hint={__("The number your pay should go to by mobile money.")} />
				)}
				<TextInput name="reason" label={__("Reason")} multiline rows={2} />
				<FormActions submitLabel={__("Send to HR")} onCancel={() => go(P.me)} dirtyHint={false} />
			</SealForm>
		</FormPage>
	);
}

interface PayoutRecordAnswer {
	name: string;
	status: string;
	change: string;
	bank: string | null;
	account_name: string | null;
	account_no: string | null;
	mobile_no: string | null;
	provider: string | null;
	reason: string | null;
	has_evidence: boolean;
	sent_on: string | null;
	effective_from: string | null;
	decision_note: string | null;
	decided_on: string | null;
	mine: boolean;
}

export function PayoutRecord() {
	const go = useGo();
	const shell = useShell();
	const notify = useNotify();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<PayoutRecordAnswer>(M.payoutRequestRecord, { name });
	const send = usePost<string>(M.sendPayoutChange);
	const withdraw = usePost<string>(M.withdrawPayoutChange);
	const [confirmWithdraw, setConfirmWithdraw] = useState(false);

	const sendNow = async () => {
		try {
			await withVerification(() => send.run({ name }), shell.verify);
			notify.success(__("Sent to HR. Nothing changes until HR confirms it."));
			await mutate();
		} catch {
			/* a cancelled check or the server's reason: shown below */
		}
	};

	const header =
		data?.mine && data.status === "Draft" ? (
			<Button loading={send.loading} onClick={sendNow}>
				{__("Send to HR")}
			</Button>
		) : data?.mine && data.status === "Waiting for HR" ? (
			<Button variant="outline" onClick={() => setConfirmWithdraw(true)}>
				{__("Withdraw")}
			</Button>
		) : undefined;

	return (
		<DetailPage
			title={data?.change === "Mobile Money" ? __("Change to Mobile Money") : __("Change of Bank Account")}
			subtitle={name}
			meta={data && <Status value={data.status} />}
			onBack={() => go(P.me)}
			actions={header}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-4">
					{send.errorMessage && <Alert tone="error">{send.errorMessage}</Alert>}
					{data.status === "Waiting for HR" && <Alert tone="info">{__("HR confirms it on the desk. You are told either way.")}</Alert>}
					<DescriptionList
						items={[
							{ label: __("Bank"), value: data.bank, hideWhenEmpty: true },
							{ label: __("Account No."), value: data.account_no, hideWhenEmpty: true },
							{ label: __("Account Name"), value: data.account_name, hideWhenEmpty: true },
							{ label: __("Mobile No."), value: data.mobile_no, hideWhenEmpty: true },
							{ label: __("Provider"), value: data.provider, hideWhenEmpty: true },
							{ label: __("Evidence"), value: data.change === "Bank Account" ? (data.has_evidence ? __("Attached") : __("Missing")) : null, hideWhenEmpty: true },
							{ label: __("Sent On"), value: data.sent_on ? formatDateTime(data.sent_on) : null, hideWhenEmpty: true },
							{ label: __("Effective From"), value: data.effective_from ? formatDate(data.effective_from) : null, hideWhenEmpty: true },
							{ label: __("Decision Note"), value: data.decision_note, hideWhenEmpty: true, full: true },
							{ label: __("Reason"), value: data.reason, hideWhenEmpty: true, full: true },
						]}
					/>
				</div>
			)}
			<ConfirmDialog
				open={confirmWithdraw}
				onClose={() => setConfirmWithdraw(false)}
				title={__("Withdraw this request?")}
				confirmLabel={__("Withdraw")}
				destructive
				onConfirm={async () => {
					await withdraw.run({ name });
					notify.success(__("Request withdrawn."));
					await mutate();
				}}
			>
				{__("HR will not act on it. Your pay keeps going where it goes now.")}
			</ConfirmDialog>
		</DetailPage>
	);
}
