// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * A fresh check before a sensitive step (SIGN_IN.md §6). The server refuses with seal_common's
 * `VerificationNeeded` when the session has not proved who holds it lately; the section then asks the
 * shell (`useShell().verify()`: fingerprint or password) and tries once more. Where the site has no
 * fresh check the first try simply goes through.
 */

/** The person closed the "Confirm it is you" step: nothing was sent. */
export class VerificationCancelled extends Error {
	override name = "VerificationCancelled";
}

/** Whether an error from the library's callers is seal_common's VerificationNeeded, however wrapped. */
export function isVerificationNeeded(error: unknown, depth = 0): boolean {
	if (!error || typeof error !== "object" || depth > 3) return false;
	const e = error as Record<string, unknown>;
	if (e.exc_type === "VerificationNeeded") return true;
	if (typeof e.exception === "string" && e.exception.includes("VerificationNeeded")) return true;
	return isVerificationNeeded(e.payload, depth + 1) || isVerificationNeeded(e.original, depth + 1);
}

/** Run `action`; if the server asks for a fresh check, ask the person, then run it once more. */
export async function withVerification<T>(action: () => Promise<T>, verify: () => Promise<boolean>): Promise<T> {
	try {
		return await action();
	} catch (error) {
		if (!isVerificationNeeded(error)) throw error;
		if (!(await verify())) throw new VerificationCancelled();
		return action();
	}
}
