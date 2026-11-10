// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

import { useCallback } from "react";
import { useShell } from "@stelden/seal-frontend/section";

/** Go to another screen of this section (a path relative to it, e.g. "leave/new"), through the shell. */
export function useGo(): (path: string) => void {
	const shell = useShell();
	return useCallback((path: string) => shell.navigate(path), [shell]);
}
