# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

import unittest

from seal_hrms.seal_hrms.doctype.leave_planning_cycle_member.leave_planning_cycle_member import (
	LeavePlanningCycleMember,
)
from seal_hrms.seal_hrms.tests.source_guard._helpers import assert_validate_clean


class TestLeavePlanningCycleMemberSourceGuard(unittest.TestCase):
	def test_validate_has_no_forbidden_side_effects(self):
		assert_validate_clean(LeavePlanningCycleMember)
