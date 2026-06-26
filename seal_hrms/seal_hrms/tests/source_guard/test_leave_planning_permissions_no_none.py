# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import unittest

from seal_hrms.seal_hrms.leave_planning import permissions as perms_module
from seal_hrms.seal_hrms.tests.source_guard._helpers import (
	assert_has_permission_returns_explicit_bool,
)


class TestLeavePlanningPermissionsNoImplicitNone(unittest.TestCase):
	def test_no_has_permission_hook_can_return_implicit_none(self):
		assert_has_permission_returns_explicit_bool(perms_module)
