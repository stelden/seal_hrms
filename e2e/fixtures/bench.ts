// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Server-side Python, without shipping a code-execution endpoint.
 *
 * Some setup has no REST surface: flipping a Settings single, forcing a
 * scheduler task, reading a field the API masks, asserting on something only
 * the ORM can see. The obvious fix is a whitelisted `run(code)` method — and it
 * is the wrong fix. That endpoint would live in the app forever, one
 * `developer_mode` misconfiguration away from remote code execution on a
 * production procurement system.
 *
 * The suite runs on the same machine as the bench, so it can just call the
 * bench's own Python. Nothing new is exposed over HTTP, and there is no app
 * code to accidentally deploy.
 *
 * `bench execute` is deliberately not used: it takes a dotted path, not a
 * statement, and it cannot resolve modules created during the same run.
 */

import { execFile } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const exec = promisify(execFile);

const BENCH = process.env.SEAL_E2E_BENCH || "/home/frappe/frappe-bench";
const PYTHON = join(BENCH, "env/bin/python");
const SITES = join(BENCH, "sites");
const SITE = process.env.SEAL_E2E_SITE || "dev.local";

/**
 * Run a Python snippet inside a connected Frappe context.
 *
 * The snippet's job is to `print()` one line of JSON, which comes back parsed.
 * Anything it prints before that is treated as noise and discarded — the bench
 * emits a `module seal_npo`
 * warning on every single invocation, and a naive `JSON.parse(stdout)` chokes
 * on it.
 *
 * A file on disk, never a heredoc: heredocs through a shell tool swallow
 * stderr, mangle multi-byte characters, and double-escape triple-quoted
 * strings, so a failing script reports as a silent success.
 */
export async function runPython<T = any>(code: string): Promise<T> {
	const dir = mkdtempSync(join(tmpdir(), "seal-e2e-"));
	const script = join(dir, "snippet.py");
	const preamble = [
		"import json, frappe",
		`frappe.init(site=${JSON.stringify(SITE)})`,
		"frappe.connect()",
		'frappe.set_user("Administrator")',
		"",
		"def __seal_e2e_main():",
	].join("\n");
	const indented = code
		.trim()
		.split("\n")
		.map((line) => "    " + line)
		.join("\n");
	const epilogue = [
		"",
		"try:",
		"    __seal_e2e_result = __seal_e2e_main()",
		"    frappe.db.commit()",
		'    print("__SEAL_E2E__" + json.dumps(__seal_e2e_result, default=str))',
		"finally:",
		"    frappe.destroy()",
	].join("\n");

	writeFileSync(script, [preamble, indented, epilogue].join("\n"));
	try {
		const { stdout, stderr } = await exec(PYTHON, [script], {
			cwd: SITES,
			maxBuffer: 32 * 1024 * 1024,
			timeout: 180_000,
		});
		const marker = stdout.lastIndexOf("__SEAL_E2E__");
		if (marker === -1) {
			throw new Error(
				`python snippet printed no result.\nstdout: ${stdout.slice(-2000)}\nstderr: ${stderr.slice(-2000)}`,
			);
		}
		return JSON.parse(stdout.slice(marker + "__SEAL_E2E__".length).trim()) as T;
	} catch (err: any) {
		// execFile puts the traceback on the error, not in a variable anyone
		// thinks to read. Surface it or every failure here reads "Command failed".
		const detail = [err.stdout, err.stderr].filter(Boolean).join("\n").slice(-4000);
		throw new Error(`runPython failed: ${err.message}\n${detail}`);
	} finally {
		rmSync(dir, { recursive: true, force: true });
	}
}

/**
 * Run a Python snippet for its side effects only.
 *
 * Sugar for the common case, so callers do not have to remember to
 * `return None` from something that was only ever meant to write.
 */
export async function runPythonVoid(code: string): Promise<void> {
	await runPython(`${code.trim()}\nreturn None`);
}
