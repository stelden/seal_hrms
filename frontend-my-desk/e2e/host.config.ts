// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// A stand-in for seal_desk's shell, for browser checks while the shell is being built: lends React and
// the library through an import map exactly as the shell does (frappePortal lend), and loads the built
// Self Service section from /assets/seal_hrms/my-desk/ (MY_DESK_P5_PLAN §8; the library's consumer check).
import react from "@vitejs/plugin-react";
import { frappePortal } from "@stelden/seal-frontend/vite";
import { defineConfig, mergeConfig } from "vite";

export default defineConfig(
	mergeConfig(frappePortal({ app: "e2e_host", spa: "my-desk", outDir: "../.host", lend: true }), {
		root: new URL("./host", import.meta.url).pathname,
		plugins: [react()],
		build: { rollupOptions: { preserveEntrySignatures: "allow-extension" } },
	}),
);
