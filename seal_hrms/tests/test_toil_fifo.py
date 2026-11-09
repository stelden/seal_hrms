# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Which banked time each leave uses, and what lapses (toil/fifo.py). Pure: no site needed."""

import unittest
from datetime import date

from seal_hrms.seal_hrms.toil.fifo import Lot, Use, newly_unfunded, simulate

TODAY = date(2026, 6, 15)


def lot(key, days, available_from, valid_through):
	return Lot(key, days, date(*available_from), date(*valid_through))


class TestWhichTimeIsUsed(unittest.TestCase):
	def test_leave_takes_from_the_time_that_lapses_soonest(self):
		lots = [lot("late", 1, (2026, 5, 1), (2026, 9, 1)), lot("soon", 1, (2026, 5, 10), (2026, 7, 1))]
		result = simulate(lots, [Use("LA-1", date(2026, 6, 20), 1)], TODAY)
		used = {l.key: l.used for l in result.lots}
		self.assertEqual(used, {"soon": 1, "late": 0})

	def test_leave_cannot_use_time_that_lapses_before_it_starts(self):
		lots = [lot("A", 2, (2026, 5, 1), (2026, 6, 30))]
		result = simulate(lots, [Use("LA-1", date(2026, 7, 2), 1)], TODAY)
		self.assertEqual(result.unfunded[0][1], 1)

	def test_leave_on_the_last_usable_day_counts(self):
		lots = [lot("A", 1, (2026, 5, 1), (2026, 6, 30))]
		self.assertEqual(simulate(lots, [Use("LA-1", date(2026, 6, 30), 1)], TODAY).unfunded, [])

	def test_leave_cannot_use_time_not_yet_earned(self):
		lots = [lot("A", 1, (2026, 6, 20), (2026, 9, 1))]
		self.assertEqual(simulate(lots, [Use("LA-1", date(2026, 6, 18), 1)], TODAY).unfunded[0][1], 1)

	def test_one_leave_spans_two_claims(self):
		lots = [lot("A", 0.5, (2026, 5, 1), (2026, 7, 1)), lot("B", 1, (2026, 5, 1), (2026, 8, 1))]
		result = simulate(lots, [Use("LA-1", date(2026, 6, 20), 1)], TODAY)
		self.assertEqual({l.key: l.used for l in result.lots}, {"A": 0.5, "B": 0.5})
		self.assertEqual(result.unfunded, [])

	def test_cancelled_claims_net_to_nothing_and_are_ignored(self):
		result = simulate([lot("A", 0, (2026, 5, 1), (2026, 7, 1))], [], TODAY)
		self.assertEqual(result.lots, [])


class TestWhatLapses(unittest.TestCase):
	def test_only_unused_time_past_its_date_lapses(self):
		lots = [lot("past", 2, (2026, 4, 1), (2026, 6, 10)), lot("live", 2, (2026, 5, 1), (2026, 8, 1))]
		result = simulate(lots, [Use("LA-1", date(2026, 5, 20), 0.5)], TODAY)
		by_key = {l.key: l for l in result.lots}
		self.assertEqual((by_key["past"].used, by_key["past"].lapsed, by_key["past"].left), (0.5, 1.5, 0))
		self.assertEqual((by_key["live"].lapsed, by_key["live"].left), (0, 2))

	def test_nothing_lapses_on_its_last_day(self):
		result = simulate([lot("A", 1, (2026, 5, 1), TODAY.timetuple()[:3])], [], TODAY)
		self.assertEqual(result.lots[0].lapsed, 0)


class TestWhatAChangeBreaks(unittest.TestCase):
	def test_taking_a_claim_away_breaks_the_leave_it_funded(self):
		lots = [lot("A", 1, (2026, 5, 1), (2026, 9, 1))]
		uses = [Use("LA-1", date(2026, 6, 20), 1)]
		before = simulate(lots, uses, TODAY)
		after = simulate([], uses, TODAY)
		self.assertEqual([u.key for u, _ in newly_unfunded(before, after)], ["LA-1"])

	def test_leave_already_short_is_not_blamed_on_the_change(self):
		uses = [Use("LA-1", date(2026, 6, 20), 1)]
		before = simulate([], uses, TODAY)
		after = simulate([], uses, TODAY)
		self.assertEqual(newly_unfunded(before, after), [])
