// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Screens that ask "is it still you?" before they show anything: payslips and where a person is paid
 * (seal_hrms.sensitive; which screens ask is a SEAL HRMS Settings choice). The server refuses the read with
 * seal_common's `VerificationNeeded`; the screen asks the shell for a fingerprint or the password once, on
 * arrival, then reads again. If the person closes that, the screen offers a Confirm button instead.
 */

import { useEffect, useRef, useState } from "react";
import { useShell } from "@stelden/seal-frontend/section";
import { Alert, Button, __ } from "@stelden/seal-frontend/ui";

import { isVerificationNeeded } from "./verify";

/** Whether a read failed only because the screen must ask first; then `error` is not an error to show. */
export function useConfirmToSee(error: unknown, reload: () => unknown) {
	const shell = useShell();
	const needed = isVerificationNeeded(error);
	const [busy, setBusy] = useState(false);
	const asked = useRef(false);

	const confirm = async () => {
		setBusy(true);
		try {
			if (await shell.verify()) await reload();
		} finally {
			setBusy(false);
		}
	};

	useEffect(() => {
		if (needed && !asked.current) {
			asked.current = true; // once on arrival; after that the person presses Confirm
			void confirm();
		}
		// Deliberately only when the refusal first arrives
	}, [needed]);

	return { needed, busy, confirm, error: needed ? undefined : error };
}

/** What shows in place of the screen while it waits for the person to confirm. */
export function ConfirmToSee({ what, busy, onConfirm }: { what: string; busy: boolean; onConfirm: () => void }) {
	return (
		<Alert
			tone="info"
			role="status"
			title={__("Confirm It Is You")}
			action={
				<Button loading={busy} onClick={onConfirm}>
					{__("Confirm")}
				</Button>
			}
		>
			{what}
		</Alert>
	);
}
