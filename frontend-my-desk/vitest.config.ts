// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Separate from vite.config.ts so tests never run the section build. The library imports
// frappe-react-sdk, which has no exports map: inlined, so Node keeps its named exports.
export default defineConfig({
	plugins: [react()],
	test: {
		environment: "jsdom",
		include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
		setupFiles: ["src/test-setup.ts"],
		server: { deps: { inline: [/@stelden\/seal-frontend/, "frappe-react-sdk"] } },
	},
});
