# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""How extra hours become days of time off (toil/days.py). Pure: no site needed."""

import unittest

from seal_hrms.seal_hrms.toil.days import (
	PUBLIC,
	REST,
	WORKING,
	Counting,
	below_minimum,
	count_line,
	round2,
	to_days,
	within_cap,
)

RULES = Counting(
	hours_per_day=8, after_hours_rate=1, rest_day_rate=1.5, public_holiday_rate=2, minimum_hours=1
)


class TestCountingHours(unittest.TestCase):
	def test_each_kind_of_day_takes_its_own_rate(self):
		self.assertEqual(count_line(3, WORKING, RULES), (1, 3))
		self.assertEqual(count_line(4, REST, RULES), (1.5, 6))
		self.assertEqual(count_line(4, PUBLIC, RULES), (2, 8))

	def test_the_daily_cap_applies_to_hours_worked_before_the_rate(self):
		capped = Counting(hours_per_day=8, rest_day_rate=1.5, daily_cap=4)
		self.assertEqual(count_line(10, REST, capped), (1.5, 6))

	def test_no_cap_means_no_limit(self):
		self.assertEqual(count_line(14, WORKING, RULES), (1, 14))

	def test_under_the_minimum_does_not_count(self):
		self.assertTrue(below_minimum(0.5, RULES))
		self.assertFalse(below_minimum(1, RULES))

	def test_hours_become_days_at_the_working_day(self):
		self.assertEqual(to_days(12, 8), 1.5)
		self.assertEqual(to_days(1, 8), 0.13)  # 0.125 rounds half up

	def test_a_working_day_of_no_hours_is_refused(self):
		with self.assertRaises(ValueError):
			to_days(4, 0)

	def test_rounding_is_half_up(self):
		self.assertEqual(round2(0.125), 0.13)
		self.assertEqual(round2(2.675), 2.68)


class TestBalanceCap(unittest.TestCase):
	def test_no_cap_adds_everything(self):
		self.assertEqual(within_cap(3, 20, 0), (3, 0))

	def test_adds_what_fits_and_shows_the_rest(self):
		self.assertEqual(within_cap(3, 8.5, 10), (1.5, 1.5))

	def test_at_the_cap_nothing_is_added(self):
		self.assertEqual(within_cap(2, 10, 10), (0, 2))
		self.assertEqual(within_cap(2, 11, 10), (0, 2))


class TestFromPolicy(unittest.TestCase):
	def test_blank_rules_read_as_zero(self):
		rules = Counting.from_policy({"hours_per_day": 7.5, "daily_cap": None})
		self.assertEqual(rules.hours_per_day, 7.5)
		self.assertEqual(rules.daily_cap, 0)
