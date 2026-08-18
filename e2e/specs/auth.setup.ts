// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

/**
 * Log in once and park the cookies, so no later spec pays the login cost or
 * contains a login it did not mean to test.
 *
 * Through the API rather than the login form: a form login here would make
 * every spec depend on the login page's markup, so a restyled button would fail
 * the whole suite for a reason that has nothing to do with seal_npo.
 */

import { test as setup, expect, request } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

import { ADMIN, statePathFor } from "../fixtures/auth";

setup("authenticate administrator", async ({ baseURL }) => {
	const ctx = await request.newContext({ baseURL });
	const res = await ctx.post("/api/method/login", {
		form: { usr: ADMIN.usr, pwd: ADMIN.pwd },
	});
	expect(res.status(), "login must succeed").toBe(200);

	const who = await ctx.get("/api/method/frappe.auth.get_logged_user");
	expect((await who.json()).message, "logged in as the wrong user").toBe(ADMIN.usr);

	const path = statePathFor("admin");
	mkdirSync(dirname(path), { recursive: true });
	await ctx.storageState({ path });
	await ctx.dispose();
});
