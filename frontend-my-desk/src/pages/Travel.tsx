// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Travel requests on the phone (Keith, 2026-11-11): Frappe HR's Travel Request, asked for by the person and
 * decided by their line manager through the site's workflow (seal_hrms.seal_hrms.travel). The journeys and
 * the expected costs are the request's own rows, added and removed as on an expense claim. The company is
 * the person's own (the server's), and passport and ID details stay on the desk with HR (EM-5).
 */

import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router";
import { formatCurrency, formatDate, formatDateTime, useGet, usePost } from "@stelden/seal-frontend";
import { useShell } from "@stelden/seal-frontend/section";
import { CheckboxInput, DateTimeInput, FormActions, NumberInput, RowsInput, SealForm, SelectInput, TextInput, required, useSealForm, z } from "@stelden/seal-frontend/forms";
import { Alert, Button, DescriptionList, DetailPage, EmptyState, FormPage, List, ListItem, ListPage, Section, Text, __, useNotify } from "@stelden/seal-frontend/ui";
import { Plane, Plus } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { willApprove } from "../lib/approver";
import { savedDay, useDraft } from "../lib/drafts";
import { travelRows, type TravelCost, type TravelLeg } from "../lib/forms";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";

interface TravelRow {
	name: string;
	purpose_of_travel: string;
	travel_type: string;
	state: string;
	creation: string;
	travel_from: string | null;
	travel_to: string | null;
	departure_date: string | null;
}

/** "Nairobi to Kisumu", or the purpose when no journey names a place. */
function where(row: { travel_from: string | null; travel_to: string | null; purpose_of_travel: string }): string {
	if (row.travel_from && row.travel_to) return __("{0} to {1}", [row.travel_from, row.travel_to]);
	return row.travel_to || row.travel_from || row.purpose_of_travel;
}

export function TravelList() {
	const go = useGo();
	const { data, isLoading, error, mutate, hasLoaded } = useGet<TravelRow[]>(M.travelList);
	return (
		<ListPage
			title={__("Travel Requests")}
			onBack={() => go("")}
			loading={isLoading}
			error={error}
			onRetry={mutate}
			actions={
				<Button onClick={() => go(P.travelNew)}>
					<Plus />
					{__("New Travel Request")}
				</Button>
			}
		>
			{hasLoaded && !data?.length ? (
				<EmptyState icon={<Plane />} title={__("No travel requests yet")} description={__("Ask to travel for work. Your line manager approves it.")} />
			) : (
				<List divided>
					{(data ?? []).map((t) => (
						<ListItem
							key={t.name}
							primary={where(t)}
							secondary={[t.purpose_of_travel, t.departure_date ? formatDate(t.departure_date) : formatDate(t.creation)].filter(Boolean).join(" · ")}
							action={<Status value={t.state} />}
							onClick={() => go(P.travelRecord(t.name))}
						/>
					))}
				</List>
			)}
		</ListPage>
	);
}

interface TravelOptions {
	purposes: string[];
	expense_types: string[];
	travel_types: string[];
	funding: string[];
	modes: string[];
	currency: string;
	approver_name: string | null;
}

interface TravelValues {
	travel_type: string;
	purpose_of_travel: string;
	travel_funding: string;
	description: string;
	itinerary: TravelLeg[];
	costings: TravelCost[];
}

const blankLeg = (): TravelLeg => ({ travel_from: "", travel_to: "", mode_of_travel: "", departure_date: "", arrival_date: "", lodging_required: false });
const blankCost = (): TravelCost => ({ expense_type: "", total_amount: null, comments: "" });
const blank = (): TravelValues => ({ travel_type: "", purpose_of_travel: "", travel_funding: "", description: "", itinerary: [blankLeg()], costings: [] });

/** Frappe HR's own option words, translated: each written out so the translation tools find it. */
function optionLabel(value: string): string {
	switch (value) {
		case "Domestic": return __("Domestic");
		case "International": return __("International");
		case "Require Full Funding": return __("Require Full Funding");
		case "Fully Sponsored": return __("Fully Sponsored");
		case "Partially Sponsored, Require Partial Funding": return __("Partially Sponsored, Require Partial Funding");
		case "Flight": return __("Flight");
		case "Train": return __("Train");
		case "Taxi": return __("Taxi");
		case "Rented Car": return __("Rented Car");
		default: return value;
	}
}

export function TravelForm() {
	const go = useGo();
	const notify = useNotify();
	const options = useGet<TravelOptions>(M.travelOptions);
	const create = usePost<{ name: string; state: string }>(M.requestTravel);
	const schema = useMemo(
		() =>
			z
				.object({
					travel_type: required(() => __("Travel Type")),
					purpose_of_travel: required(() => __("Purpose of Travel")),
					itinerary: z.array(z.object({ travel_from: required(() => __("From")), travel_to: required(() => __("To")) }).loose()).min(1),
				})
				.loose(),
		[],
	);
	const form = useSealForm<TravelValues>({ schema, defaultValues: blank() });
	// Kept on the phone until it is sent (P6 drafts), as an expense claim is.
	const draft = useDraft<TravelValues>(useShell().user, "travel-request", "new");
	const [restoredAt, setRestoredAt] = useState<number | null>(null);
	useEffect(() => {
		if (draft.restored && Array.isArray(draft.restored.value?.itinerary)) {
			form.reset({ ...blank(), ...draft.restored.value });
			setRestoredAt(draft.restored.saved);
			draft.dismiss();
		}
		const watching = form.watch((values) => draft.keep(values as TravelValues));
		return () => watching.unsubscribe();
		// Deliberately not every dependency: once, when the screen opens
	}, []);
	const startAgain = () => {
		draft.clear();
		setRestoredAt(null);
		form.reset(blank());
	};

	const submit = async (values: TravelValues) => {
		const rows = travelRows(values.itinerary, values.costings);
		const answer = await create.run({
			travel_type: values.travel_type,
			purpose_of_travel: values.purpose_of_travel,
			travel_funding: values.travel_funding || undefined,
			description: values.description,
			itinerary: JSON.stringify(rows.itinerary),
			costings: JSON.stringify(rows.costings),
			send: 1,
		});
		draft.clear(); // the server has it now
		notify.success(options.data?.approver_name ? __("Travel request sent to {0}.", [options.data.approver_name]) : __("Travel request sent."));
		go(P.travelRecord(answer.name));
	};

	const choices = (values: string[] | undefined) => (values ?? []).map((v) => ({ value: v, label: optionLabel(v) }));
	return (
		<FormPage title={__("New Travel Request")} onBack={() => go(P.travel)} loading={options.isLoading} error={options.error} onRetry={options.mutate}>
			{restoredAt !== null && (
				<Alert tone="info" title={__("Restored From This Phone")} action={<Button onClick={startAgain}>{__("Start Again")}</Button>}>
					{__("You started this request on {0} and had not sent it.", [formatDate(savedDay(restoredAt))])}
				</Alert>
			)}
			{options.data && <Alert tone={options.data.approver_name ? "info" : "warning"}>{willApprove(options.data.approver_name)}</Alert>}
			<SealForm form={form} onSubmit={submit}>
				<SelectInput name="travel_type" label={__("Travel Type")} required options={choices(options.data?.travel_types)} />
				<SelectInput name="purpose_of_travel" label={__("Purpose of Travel")} required options={(options.data?.purposes ?? []).map((p) => ({ value: p, label: p }))} hint={options.data && !options.data.purposes.length ? __("HR has not set up purposes of travel yet. Ask them to.") : undefined} />
				<SelectInput name="travel_funding" label={__("Travel Funding")} options={choices(options.data?.funding)} />
				<RowsInput
					name="itinerary"
					label={__("Journeys")}
					minRows={1}
					addLabel={__("Add a Journey")}
					newRow={blankLeg}
					renderRow={(path) => (
						<>
							<TextInput name={path("travel_from")} label={__("From")} required />
							<TextInput name={path("travel_to")} label={__("To")} required />
							<SelectInput name={path("mode_of_travel")} label={__("Mode of Travel")} options={choices(options.data?.modes)} />
							<DateTimeInput name={path("departure_date")} label={__("Departure")} />
							<DateTimeInput name={path("arrival_date")} label={__("Arrival")} />
							<CheckboxInput name={path("lodging_required")} label={__("Lodging Required")} />
						</>
					)}
				/>
				<RowsInput
					name="costings"
					label={__("Expected Costs")}
					addLabel={__("Add a Cost")}
					newRow={blankCost}
					emptyText={__("None yet. Add what the trip is expected to cost, if you know.")}
					renderRow={(path) => (
						<>
							<SelectInput name={path("expense_type")} label={__("Expense Type")} options={(options.data?.expense_types ?? []).map((t) => ({ value: t, label: t }))} />
							<NumberInput name={path("total_amount")} label={__("Amount ({0})", [options.data?.currency ?? ""])} min={0} step={0.01} />
							<TextInput name={path("comments")} label={__("Comments")} />
						</>
					)}
				/>
				<TextInput name="description" label={__("Other Details")} multiline rows={3} />
				<FormActions submitLabel={__("Send for Approval")} onCancel={() => go(P.travel)} />
			</SealForm>
		</FormPage>
	);
}

interface TravelRecordAnswer {
	name: string;
	employee_name: string;
	state: string;
	docstatus: number;
	travel_type: string;
	purpose_of_travel: string;
	travel_funding: string | null;
	description: string | null;
	currency: string | null;
	approver_name: string | null;
	itinerary: Array<TravelLeg & { other_details?: string | null }>;
	costings: Array<{ expense_type: string | null; total_amount: number; comments: string | null }>;
	mine: boolean;
	can_send: boolean;
}

export function TravelRecord() {
	const go = useGo();
	const notify = useNotify();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<TravelRecordAnswer>(M.travelRecord, { name });
	const send = usePost<string>(M.travelAction);
	const sendNow = async () => {
		try {
			await send.run({ name, action: "Send for Approval" });
			notify.success(__("Travel request sent."));
			await mutate();
		} catch {
			/* the server's reason shows below */
		}
	};
	return (
		<DetailPage
			title={data ? where({ ...(data.itinerary[0] ?? { travel_from: null, travel_to: null }), purpose_of_travel: data.purpose_of_travel }) : __("Travel Request")}
			subtitle={data && (data.mine ? name : data.employee_name)}
			meta={data && <Status value={data.state} />}
			onBack={() => go(P.travel)}
			actions={
				data?.can_send ? (
					<Button loading={send.loading} onClick={sendNow}>
						{__("Send for Approval")}
					</Button>
				) : undefined
			}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-6">
					{send.errorMessage && <Alert tone="error">{send.errorMessage}</Alert>}
					{data.mine && data.state === "Pending Approval" && <Alert tone="info">{willApprove(data.approver_name)}</Alert>}
					<DescriptionList
						items={[
							{ label: __("Purpose of Travel"), value: data.purpose_of_travel },
							{ label: __("Travel Type"), value: optionLabel(data.travel_type) },
							{ label: __("Travel Funding"), value: data.travel_funding ? optionLabel(data.travel_funding) : null, hideWhenEmpty: true },
							{ label: __("Line Manager"), value: data.approver_name, hideWhenEmpty: true },
							{ label: __("Other Details"), value: data.description, hideWhenEmpty: true, full: true },
						]}
					/>
					<Section title={__("Journeys")}>
						<List divided>
							{data.itinerary.map((leg, i) => (
								<ListItem
									key={i}
									primary={__("{0} to {1}", [leg.travel_from || "?", leg.travel_to || "?"])}
									secondary={[leg.mode_of_travel ? optionLabel(leg.mode_of_travel) : "", leg.departure_date ? formatDateTime(leg.departure_date) : "", leg.lodging_required ? __("Lodging required") : ""]
										.filter(Boolean)
										.join(" · ")}
								/>
							))}
						</List>
					</Section>
					{data.costings.length > 0 && (
						<Section title={__("Expected Costs")}>
							<List divided>
								{data.costings.map((c, i) => (
									<ListItem key={i} primary={c.expense_type || __("Other")} secondary={c.comments ?? undefined} action={data.currency ? formatCurrency(c.total_amount, data.currency) : String(c.total_amount)} />
								))}
							</List>
						</Section>
					)}
					{!data.mine && <Text muted>{__("Decide this request from Approvals.")}</Text>}
				</div>
			)}
		</DetailPage>
	);
}
