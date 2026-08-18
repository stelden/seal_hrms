// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/** Where the administrator's parked cookies live. */

import { join } from "node:path";

export const STATE_DIR = join(__dirname, "../artifacts/auth");

export function statePathFor(key: string): string {
	return join(STATE_DIR, `${key}.json`);
}

export const ADMIN = {
	usr: process.env.SEAL_E2E_USER || "Administrator",
	pwd: process.env.SEAL_E2E_PASSWORD || "21954124",
};
