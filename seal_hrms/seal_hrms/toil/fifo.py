# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Which banked time each leave uses, and what has lapsed. Pure: no Frappe, tested directly.

A lot is one approved claim's time: usable from the day it was added through
the day it lapses (never past the end of its leave year). A use is one leave
application's days, counted on the day the leave starts: time can be used for
leave that starts on or before the day it lapses (decision D10b).

Leave takes from the lot that lapses soonest, so nothing lapses that could have
been used. Leave no lot can cover is reported as unfunded rather than hidden.
"""

from dataclasses import dataclass, field
from datetime import date

EPS = 0.005


@dataclass
class Lot:
	key: str
	days: float
	available_from: date
	valid_through: date
	used: float = 0.0
	lapsed: float = 0.0

	@property
	def left(self) -> float:
		return max(round(self.days - self.used - self.lapsed, 2), 0.0)


@dataclass
class Use:
	key: str
	on: date
	days: float


@dataclass
class Outcome:
	lots: list[Lot]
	unfunded: list[tuple[Use, float]] = field(default_factory=list)


def simulate(lots: list[Lot], uses: list[Use], today: date) -> Outcome:
	"""Fund each use from the lots, oldest leave first; then lapse what was left of any lot past its date."""
	lots = [Lot(lot.key, lot.days, lot.available_from, lot.valid_through) for lot in lots if lot.days > EPS]
	lots.sort(key=lambda lot: (lot.valid_through, lot.available_from, lot.key))
	unfunded = []
	for use in sorted(uses, key=lambda u: (u.on, u.key)):
		need = use.days
		for lot in lots:
			if need <= EPS:
				break
			if lot.available_from <= use.on <= lot.valid_through:
				take = min(lot.days - lot.used, need)
				if take > 0:
					lot.used = round(lot.used + take, 4)
					need = round(need - take, 4)
		if need > EPS:
			unfunded.append((use, round(need, 2)))
	for lot in lots:
		lot.lapsed = round(lot.days - lot.used, 2) if lot.valid_through < today else 0.0
	return Outcome(lots=lots, unfunded=unfunded)


def newly_unfunded(before: Outcome, after: Outcome) -> list[tuple[Use, float]]:
	"""Uses that `after` leaves short but `before` covered: what a change would break."""
	already = {use.key for use, _ in before.unfunded}
	return [(use, short) for use, short in after.unfunded if use.key not in already]
