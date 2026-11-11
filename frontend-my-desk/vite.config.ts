// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import react from "@vitejs/plugin-react";
import { frappeSection } from "@stelden/seal-frontend/vite";
import { defineConfig } from "vite";

// The Self Service section of the My Desk phone app (SECTIONS_CONTRACT §3): section.js, section.css and the
// section.json stamp into ../seal_hrms/public/my-desk/ (committed). React, the router, the SDK and the
// library are left to the shell, which lends them through its import map; icons are bundled.
export default defineConfig(frappeSection({ app: "seal_hrms", shell: "my-desk", plugins: [react()] }));
