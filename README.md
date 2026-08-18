# SEAL HRMS

> Kenyan statutory payroll reporting and an employee self-service shell.

A thin layer on Frappe HRMS: the monthly statutory registers (NSSF, SHIF, HELB, salary register, bank
advice), a Self Service workspace aimed at staff rather than HR officers, and the Employee-master
additions HRMS does not ship — dependants and beneficiaries, separation types, task hand-over.

## Dependencies

- `erpnext`
- `hrms`

Frappe v16 / ERPNext v16.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app seal_hrms --branch version-16
bench --site <site> install-app seal_hrms
bench --site <site> migrate
```

## Documentation

See [`DOCUMENTATION.md`](DOCUMENTATION.md) for the full developer and user guide —
what each record is for, how the modules fit together, the settings, and the
gotchas that have cost real time.

## Testing

```bash
# Browser
cd apps/seal_hrms/e2e && npx playwright test

# Python
bench --site <site> run-tests --app seal_hrms
```

## Contributing

This app uses `pre-commit` for formatting and linting (ruff, eslint, prettier,
pyupgrade):

```bash
cd apps/seal_hrms
pre-commit install
```

## Licence

GPL-3.0. See `license.txt`.
