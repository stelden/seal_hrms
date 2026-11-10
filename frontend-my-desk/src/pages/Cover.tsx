// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Cover during leave on the phone (HR_ON_MY_DESK §3): handovers to answer, work being covered, the
 * person's own handovers; and one handover, where a stand-in agrees or declines each part (a reason on
 * Decline), leaves notes, and the owner says they are back. Every action is seal_hrms'
 * task_assignment_actions endpoint, which checks the caller itself.
 */

import { useState } from "react";
import { useParams } from "react-router";
import { formatDate, useGet, usePost } from "@stelden/seal-frontend";
import {
	Alert,
	Button,
	ConfirmDialog,
	DescriptionList,
	DetailPage,
	EmptyState,
	List,
	ListItem,
	ListPage,
	SealDialog,
	Section,
	TabPanel,
	TabsNav,
	Text,
	Textarea,
	__,
	useNotify,
} from "@stelden/seal-frontend/ui";
import { Users } from "@stelden/seal-frontend/icons";

import { M } from "../lib/api";
import { nameFrom, P } from "../lib/paths";
import { useGo } from "../lib/shell";
import { Status } from "../lib/Status";

interface CoverRow {
	name: string;
	employee_name: string;
	stand_in: string;
	leave_from: string;
	leave_to: string;
	return_date: string | null;
	status: string;
	waiting_for_me?: boolean;
}

interface CoverAnswer {
	to_answer: CoverRow[];
	covering: CoverRow[];
	mine: CoverRow[];
}

type Tab = "to_answer" | "covering" | "mine";

function rowsOf(rows: CoverRow[], mine: boolean, go: (p: string) => void) {
	return (
		<List divided>
			{rows.map((r) => (
				<ListItem
					key={r.name}
					primary={mine ? __("Covered by {0}", [r.stand_in]) : r.employee_name}
					secondary={__("{0} to {1}", [formatDate(r.leave_from), formatDate(r.leave_to)])}
					action={<Status value={r.waiting_for_me ? "Pending" : r.status} />}
					onClick={() => go(P.handover(r.name))}
				/>
			))}
		</List>
	);
}

export function CoverList() {
	const go = useGo();
	const [tab, setTab] = useState<Tab>("to_answer");
	const { data, isLoading, error, mutate, hasLoaded } = useGet<CoverAnswer>(M.cover);
	const empty = (title: string, description: string) => <EmptyState icon={<Users />} title={title} description={description} />;
	return (
		<ListPage title={__("Cover")} onBack={() => go("")} loading={isLoading} error={error} onRetry={mutate}>
			<TabsNav
				label={__("Handovers")}
				value={tab}
				onChange={setTab}
				items={[
					{ id: "to_answer", label: __("To Answer"), count: data?.to_answer.filter((r) => r.waiting_for_me).length },
					{ id: "covering", label: __("Covering"), count: data?.covering.length },
					{ id: "mine", label: __("Mine"), count: data?.mine.length },
				]}
			/>
			<TabPanel id="to_answer" value={tab}>
				{hasLoaded && !data?.to_answer.length
					? empty(__("Nobody has asked you to cover"), __("When a colleague names you as their stand-in, it shows here for you to agree or decline."))
					: rowsOf(data?.to_answer ?? [], false, go)}
			</TabPanel>
			<TabPanel id="covering" value={tab}>
				{hasLoaded && !data?.covering.length
					? empty(__("You are not covering anyone now"), __("Work you agreed to cover shows here while the person is away."))
					: rowsOf(data?.covering ?? [], false, go)}
			</TabPanel>
			<TabPanel id="mine" value={tab}>
				{hasLoaded && !data?.mine.length
					? empty(__("No handovers of your own"), __("When you apply for leave, the handover you send shows here."))
					: rowsOf(data?.mine ?? [], true, go)}
			</TabPanel>
		</ListPage>
	);
}

interface HandoverAnswer {
	name: string;
	employee_name: string;
	leave_application: string;
	leave_from: string;
	leave_to: string;
	return_date: string | null;
	status: string;
	stand_in: string;
	main_stand_in_is_me: boolean;
	acceptance: string | null;
	decline_reason: string | null;
	notes: string;
	return_note: string;
	work: Array<{ row: string; description: string; due_date: string | null; covered_by: string; mine: boolean; acceptance: string | null; progress: string | null; notes: string | null }>;
	approvals: Array<{ row: string; label: string; covered_by: string; mine: boolean; acceptance: string | null }>;
	is_owner: boolean;
	is_stand_in: boolean;
	can_answer: boolean;
	can_return: boolean;
	answered: boolean;
}

type Ask = { kind: "decline" } | { kind: "decline-approval"; row: string } | { kind: "note"; row: string; text: string } | { kind: "return-note" } | null;

export function HandoverRecord() {
	const go = useGo();
	const notify = useNotify();
	const name = nameFrom(useParams().name);
	const { data, isLoading, error, mutate } = useGet<HandoverAnswer>(M.handoverRecord, { name });
	const respond = usePost(M.respond);
	const respondAuthority = usePost(M.respondAuthority);
	const addNote = usePost(M.addNote);
	const returnNote = usePost(M.returnNote);
	const returnWork = usePost(M.returnWork);
	const [ask, setAsk] = useState<Ask>(null);
	const [text, setText] = useState("");
	const [confirmBack, setConfirmBack] = useState(false);
	const [busy, setBusy] = useState(false);
	const [failure, setFailure] = useState<unknown>(null);

	const act = async (call: () => Promise<unknown>, done: string) => {
		setBusy(true);
		setFailure(null);
		try {
			await call();
			notify.success(done);
			setAsk(null);
			setText("");
			await mutate();
		} catch (thrown) {
			setFailure(thrown);
		} finally {
			setBusy(false);
		}
	};

	const header =
		data && data.can_answer ? (
			<div className="flex gap-2">
				<Button variant="outline" onClick={() => setAsk({ kind: "decline" })}>
					{__("Decline")}
				</Button>
				<Button loading={busy} onClick={() => act(() => respond.run({ name, answer: "Accepted" }), __("You agreed to cover this."))}>
					{__("Accept")}
				</Button>
			</div>
		) : data && data.can_return ? (
			<Button onClick={() => setConfirmBack(true)}>{__("I'm Back")}</Button>
		) : undefined;

	return (
		<DetailPage
			title={data ? (data.is_owner ? __("My Handover") : __("Cover for {0}", [data.employee_name])) : __("Handover")}
			subtitle={data && __("{0} to {1}", [formatDate(data.leave_from), formatDate(data.leave_to)])}
			meta={data && <Status value={data.status} />}
			onBack={() => go(P.cover)}
			actions={header}
			loading={isLoading}
			error={error}
			onRetry={mutate}
		>
			{data && (
				<div className="flex flex-col gap-6">
					{failure ? <Alert tone="error">{respond.errorMessage || respondAuthority.errorMessage || returnWork.errorMessage || __("That did not go through. Try again.")}</Alert> : null}
					<DescriptionList
						items={[
							{ label: __("Stand-in"), value: data.stand_in },
							{ label: __("Back On"), value: data.return_date ? formatDate(data.return_date) : null, hideWhenEmpty: true },
							{ label: __("Decline Reason"), value: data.decline_reason, hideWhenEmpty: true, full: true },
							{ label: __("Handover Notes"), value: data.notes, hideWhenEmpty: true, full: true },
							{ label: __("Return Note"), value: data.return_note, hideWhenEmpty: true, full: true },
						]}
					/>

					<Section title={__("Work")}>
						{data.work.length === 0 ? (
							<Text muted>{__("No work items were handed over; the notes say what to look after.")}</Text>
						) : (
							<List divided>
								{data.work.map((w) => (
									<ListItem
										key={w.row}
										primary={w.description}
										secondary={[w.covered_by, w.due_date ? __("Due {0}", [formatDate(w.due_date)]) : "", w.notes ?? ""].filter(Boolean).join(" · ")}
										action={
											w.mine && data.status === "Active" ? (
												<Button variant="ghost" onClick={() => setAsk({ kind: "note", row: w.row, text: w.notes ?? "" })}>
													{__("Leave a Note")}
												</Button>
											) : w.progress || w.acceptance ? (
												<Status value={w.progress || w.acceptance} />
											) : undefined
										}
									/>
								))}
							</List>
						)}
					</Section>

					{data.approvals.length > 0 && (
						<Section title={__("Approvals")}>
							<List divided>
								{data.approvals.map((a) => (
									<ListItem
										key={a.row}
										primary={a.label}
										secondary={a.covered_by}
										action={
											a.mine && data.can_answer && a.acceptance === "Pending" ? (
												<div className="flex gap-1">
													<Button variant="ghost" onClick={() => setAsk({ kind: "decline-approval", row: a.row })}>
														{__("Decline")}
													</Button>
													<Button
														variant="ghost"
														onClick={() => act(() => respondAuthority.run({ name, row: a.row, answer: "Accepted" }), __("You agreed to approve in their place."))}
													>
														{__("Accept")}
													</Button>
												</div>
											) : a.acceptance ? (
												<Status value={a.acceptance} />
											) : undefined
										}
									/>
								))}
							</List>
						</Section>
					)}

					{data.is_stand_in && data.status === "Active" && (
						<Button variant="outline" onClick={() => setAsk({ kind: "return-note" })}>
							{__("Note for Return")}
						</Button>
					)}
				</div>
			)}

			<SealDialog
				open={!!ask}
				onClose={() => setAsk(null)}
				title={ask?.kind === "note" ? __("Leave a Note") : ask?.kind === "return-note" ? __("Note for Return") : __("Decline")}
				description={
					ask?.kind === "note"
						? __("What you did on this piece of work, for when they are back.")
						: ask?.kind === "return-note"
							? __("What they should know on their first day back.")
							: __("Say why you cannot cover it, so they can ask someone else.")
				}
				actions={
					<>
						<Button variant="outline" onClick={() => setAsk(null)}>
							{__("Cancel")}
						</Button>
						<Button
							loading={busy}
							disabled={!(ask?.kind === "note" ? ask.text : text).trim()}
							onClick={() => {
								if (!ask) return;
								if (ask.kind === "decline") void act(() => respond.run({ name, answer: "Declined", reason: text }), __("You declined."));
								else if (ask.kind === "decline-approval") void act(() => respondAuthority.run({ name, row: ask.row, answer: "Declined", reason: text }), __("You declined."));
								else if (ask.kind === "note") void act(() => addNote.run({ name, row: ask.row, note: ask.text }), __("Note saved."));
								else void act(() => returnNote.run({ name, note: text }), __("Note saved."));
							}}
						>
							{ask?.kind === "decline" || ask?.kind === "decline-approval" ? __("Decline") : __("Save Note")}
						</Button>
					</>
				}
			>
				<Textarea
					aria-label={__("Note")}
					rows={4}
					value={ask?.kind === "note" ? ask.text : text}
					onChange={(event) => (ask?.kind === "note" ? setAsk({ ...ask, text: event.target.value }) : setText(event.target.value))}
				/>
			</SealDialog>

			<ConfirmDialog
				open={confirmBack}
				onClose={() => setConfirmBack(false)}
				title={__("Take your work back now?")}
				confirmLabel={__("I'm Back")}
				onConfirm={async () => {
					await returnWork.run({ name });
					notify.success(__("Your work is back with you."));
					await mutate();
				}}
			>
				{__("Everything your stand-in was covering comes back to you, and they stop approving in your place.")}
			</ConfirmDialog>
		</DetailPage>
	);
}
