__version__ = "0.1.9"

# Extend ERPNext Payment Entry to settle Expense Requisition references (monkeypatch — hrms
# already overrides the Payment Entry class, so override_doctype_class is unavailable).
try:
	from seal_hrms.seal_hrms.overrides.payment_entry import apply_patches as _seal_apply_pe_patches

	_seal_apply_pe_patches()
except Exception:
	# erpnext not importable yet, or a transient import error — the patch is idempotent and
	# re-applied on the next process boot. Never block app import.
	pass
