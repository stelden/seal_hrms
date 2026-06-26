# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import ast
import inspect


_FORBIDDEN_IN_VALIDATE = (
	"frappe.sendmail",
	"frappe.publish_realtime",
	"frappe.db.set_value",
	"frappe.db.sql",
	"frappe.db.commit",
)


def _flatten_attribute(node):
	"""Reconstruct a dotted name from an ast.Attribute / ast.Name chain."""
	parts = []
	while isinstance(node, ast.Attribute):
		parts.append(node.attr)
		node = node.value
	if isinstance(node, ast.Name):
		parts.append(node.id)
	return ".".join(reversed(parts))


def _find_method_node(class_source, method_name):
	tree = ast.parse(class_source)
	for node in ast.walk(tree):
		if isinstance(node, ast.FunctionDef) and node.name == method_name:
			return node
	return None


def scan_method_for_forbidden(cls, method_name="validate"):
	"""Walk the AST of cls.method_name and return any forbidden call names.

	Returns an empty list if the method is not defined on this class
	(inherited methods are not scanned — that's the parent's responsibility).
	"""
	try:
		src = inspect.getsource(cls)
	except (TypeError, OSError):
		return []

	node = _find_method_node(src, method_name)
	if node is None:
		return []

	violations = []
	for sub in ast.walk(node):
		if isinstance(sub, ast.Call):
			name = _flatten_attribute(sub.func)
			if name in _FORBIDDEN_IN_VALIDATE:
				violations.append(f"{name} at line {sub.lineno}")
	return violations


def assert_validate_clean(cls):
	"""Per SEAL_DEV_RULES §3.1 / §3.10 — validate() must have no forbidden side effects."""
	violations = scan_method_for_forbidden(cls, "validate")
	if violations:
		raise AssertionError(
			f"{cls.__name__}.validate() contains forbidden calls: {violations}. "
			f"Forbidden calls inside validate: {_FORBIDDEN_IN_VALIDATE}. "
			f"Move side effects to a v2 endpoint per SEAL_DEV_RULES §3.1."
		)


def scan_module_has_permission_returns(module) -> list[str]:
	"""Per §2.9 — has_permission hooks must return True/False, never None.

	Walks the AST of every function in `module` whose name contains
	'has_permission' and reports:
	  - explicit `return None` statements
	  - bare `return` statements (implicit None)
	  - missing fallback return at function end (implicit None on fall-through)
	"""
	src = inspect.getsource(module)
	tree = ast.parse(src)
	issues: list[str] = []

	for node in ast.walk(tree):
		if not (isinstance(node, ast.FunctionDef) and "has_permission" in node.name):
			continue

		for sub in ast.walk(node):
			if isinstance(sub, ast.Return):
				if sub.value is None:
					issues.append(f"{node.name}:{sub.lineno} bare 'return' (implicit None)")
				elif isinstance(sub.value, ast.Constant) and sub.value.value is None:
					issues.append(f"{node.name}:{sub.lineno} explicit 'return None'")

		last = node.body[-1] if node.body else None
		if last is not None and not _ends_with_return(last):
			issues.append(
				f"{node.name}:{node.lineno} can fall off the end without an explicit return "
				f"(implicit None — silently denies write/submit per §2.9)"
			)

	return issues


def _ends_with_return(node) -> bool:
	if isinstance(node, ast.Return):
		return True
	if isinstance(node, ast.If):
		if not node.orelse:
			return False
		return _ends_with_return(node.body[-1]) and _ends_with_return(node.orelse[-1])
	if isinstance(node, ast.Raise):
		return True
	return False


def assert_has_permission_returns_explicit_bool(module):
	issues = scan_module_has_permission_returns(module)
	if issues:
		raise AssertionError(
			f"Permission hooks in {module.__name__} risk implicit None returns:\n  - "
			+ "\n  - ".join(issues)
			+ "\nPer §2.9, has_permission must return True/False explicitly. "
			+ "None silently denies write/submit/cancel for all users."
		)
