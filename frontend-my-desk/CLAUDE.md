@node_modules/@stelden/seal-frontend/docs/CLAUDE-PORTAL.md

# What is particular to the Self Service section (seal_hrms)

- This is a **section** of the My Desk phone app, not a portal: seal_desk's shell loads it at run time
  (`dev_notes/seal_desk/pwa/SECTIONS_CONTRACT.md`). It draws no chrome; its routes are relative to
  `/my-desk/apps/my-hr`; it asks the shell for the user, navigation and fresh checks with `useShell()`.
- Start at `dev_notes/seal_hrms/HANDOVER.md` (bench root); the design is `dev_notes/seal_desk/pwa/HR_ON_MY_DESK.md`
  §3, the plan and its choices `dev_notes/seal_hrms/MY_DESK_P5_PLAN.md`.
- Data comes only from `seal_hrms.my_desk.api.*` (and the few existing seal_hrms endpoints named in
  `src/lib/api.ts`). Every rule lives on the server; the section never decides who may do what.
- Routes and the `records` map are in `src/lib/paths.ts`; the hook's `claims` in `seal_hrms/hooks.py` must match
  (`src/lib/paths.test.ts` and `tests/test_my_desk_section.py`).
- No floating buttons: page actions go in the template's header as nodes (as the shell does, seal_desk D168).
- Checks: `npm test`, `npx seal-portal-check`, `npm run build` (node from nvm v24:
  `export PATH=~/.nvm/versions/node/v24.13.0/bin:$PATH`). The build writes `../seal_hrms/public/my-desk/`, committed.
- Browser check without the shell: `e2e/` mounts the built section in a small host at 390×844 (`npm run e2e`).
