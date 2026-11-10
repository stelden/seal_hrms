// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// SEAL portal lint (SEAL_DEV_RULES §1.16): typescript-eslint's recommended rules and every seal rule.
import tseslint from "typescript-eslint";
import { sealConfig } from "@stelden/seal-frontend/eslint";

export default tseslint.config(
	{ ignores: ["node_modules/**", "*.config.ts", "*.config.js", "e2e/**"] },
	...tseslint.configs.recommended,
	...sealConfig(),
	// Tests hold fixture data (people's names, document titles), not words the section shows.
	{ files: ["src/**/*.test.{ts,tsx}"], rules: { "seal/translatable-text": "off" } },
);
