// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Drafts of long forms kept on the phone until they are sent (My Desk DESIGN §6.9, phase P6).
 *
 * Contract shared with seal_desk's shell: each draft lives in localStorage under
 * `seal-draft:<user>:<form>:<id>`; the shell removes every `seal-draft:` key when the person signs out, so a
 * phone handed to someone else never shows the last person's half-written claim. The section restores a draft
 * when the screen opens and removes it once the server has the form.
 *
 * What is kept is what the person typed, never a server answer, and never files (a receipt photo cannot be
 * kept in localStorage; the person adds it again). Every read and write is wrapped: private windows and
 * full storage simply mean no draft.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { localToday } from "./week";

export const DRAFT_PREFIX = "seal-draft:";
/** A draft older than this is dropped when found: the week or the claim it was for has moved on. */
export const DRAFT_MAX_AGE_DAYS = 30;
/** Typing is saved this long after the last change (ms). */
export const DRAFT_DELAY = 400;

/** The forms that keep drafts. Their names are part of the key. */
export type DraftForm = "timesheet-week" | "expense-claim" | "leave-application" | "travel-request";

interface Stored<T> {
	saved: number;
	value: T;
}

/** `seal-draft:<user>:<form>:<id>`. */
export function draftKey(user: string, form: DraftForm, id: string): string {
	return `${DRAFT_PREFIX}${user}:${form}:${id}`;
}

function storage(): Storage | null {
	try {
		return typeof window !== "undefined" ? window.localStorage : null;
	} catch {
		return null;
	}
}

/** The draft under `key`, or null when there is none, it is unreadable, or older than {@link DRAFT_MAX_AGE_DAYS}. */
export function readDraft<T>(key: string, now: number = Date.now()): { value: T; saved: number } | null {
	const store = storage();
	if (!store) return null;
	try {
		const raw = store.getItem(key);
		if (!raw) return null;
		const stored = JSON.parse(raw) as Stored<T>;
		if (!stored || typeof stored.saved !== "number" || !("value" in stored)) throw new Error("not a draft");
		if (now - stored.saved > DRAFT_MAX_AGE_DAYS * 86_400_000) {
			store.removeItem(key);
			return null;
		}
		return { value: stored.value, saved: stored.saved };
	} catch {
		try {
			store.removeItem(key);
		} catch {
			/* nothing to do */
		}
		return null;
	}
}

/** Keep `value` under `key`. False when the phone would not keep it (storage full or blocked). */
export function writeDraft<T>(key: string, value: T, now: number = Date.now()): boolean {
	const store = storage();
	if (!store) return false;
	try {
		store.setItem(key, JSON.stringify({ saved: now, value } satisfies Stored<T>));
		return true;
	} catch {
		return false;
	}
}

/** Forget the draft under `key`. */
export function clearDraft(key: string): void {
	try {
		storage()?.removeItem(key);
	} catch {
		/* nothing to do */
	}
}

/**
 * Remove every draft (the shell does this on sign-out; exported so the section's tests can pin the prefix).
 * With `user`, only that person's.
 */
export function clearAllDrafts(user?: string): number {
	const store = storage();
	if (!store) return 0;
	const prefix = user ? `${DRAFT_PREFIX}${user}:` : DRAFT_PREFIX;
	const keys: string[] = [];
	try {
		for (let i = 0; i < store.length; i++) {
			const key = store.key(i);
			if (key?.startsWith(prefix)) keys.push(key);
		}
		keys.forEach((key) => store.removeItem(key));
	} catch {
		return 0;
	}
	return keys.length;
}

/**
 * A screen's draft: what was restored when it opened, `keep(value)` to save as the person types (debounced),
 * and `clear()` once the server has it (or the person starts again).
 *
 * `restored` is read once per key; a screen applies it to its form and shows that it did.
 */
export function useDraft<T>(user: string | null | undefined, form: DraftForm, id: string | null | undefined) {
	const key = user && id ? draftKey(user, form, id) : null;
	const [restored, setRestored] = useState<{ value: T; saved: number } | null>(() => (key ? readDraft<T>(key) : null));
	const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
	const lastKey = useRef(key);

	useEffect(() => {
		if (lastKey.current === key) return;
		lastKey.current = key;
		setRestored(key ? readDraft<T>(key) : null);
	}, [key]);

	useEffect(
		() => () => {
			if (timer.current) clearTimeout(timer.current);
		},
		[],
	);

	const keep = useCallback(
		(value: T) => {
			if (!key) return;
			if (timer.current) clearTimeout(timer.current);
			timer.current = setTimeout(() => writeDraft(key, value), DRAFT_DELAY);
		},
		[key],
	);

	const clear = useCallback(() => {
		if (timer.current) clearTimeout(timer.current);
		timer.current = null;
		if (key) clearDraft(key);
		setRestored(null);
	}, [key]);

	/** The person saw the restored draft; stop offering it (it stays stored until sent or cleared). */
	const dismiss = useCallback(() => setRestored(null), []);

	return { key, restored, keep, clear, dismiss };
}

/** The phone's own calendar day (YYYY-MM-DD) a draft was saved on (not UTC, which is a day off at night in Nairobi). */
export function savedDay(saved: number): string {
	return localToday(new Date(saved));
}
