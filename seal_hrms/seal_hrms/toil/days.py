# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""How extra hours become days of time off. Pure: no Frappe, so it is tested directly.

Each line's hours are capped (the daily cap applies to hours worked, before the
rate), multiplied by the rate for that kind of day, and the claim's total is
divided by the hours in a working day.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

WORKING = "Working day"
REST = "Rest day"
PUBLIC = "Public holiday"


@dataclass(frozen=True)
class Counting:
	hours_per_day: float
	after_hours_rate: float = 1.0
	rest_day_rate: float = 1.0
	public_holiday_rate: float = 1.0
	minimum_hours: float = 0.0
	daily_cap: float = 0.0  # 0 = no limit

	@classmethod
	def from_policy(cls, policy) -> "Counting":
		return cls(**{name: float(policy.get(name) or 0) for name in cls.__dataclass_fields__})


def round2(value: float) -> float:
	"""Half-up to two places, so 0.125 days shows as 0.13 rather than 0.12."""
	return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def rate_for(kind: str, counting: Counting) -> float:
	return {
		WORKING: counting.after_hours_rate,
		REST: counting.rest_day_rate,
		PUBLIC: counting.public_holiday_rate,
	}[kind]


def below_minimum(hours: float, counting: Counting) -> bool:
	return hours < counting.minimum_hours


def count_line(hours: float, kind: str, counting: Counting) -> tuple[float, float]:
	"""(rate, hours it counts as) for one day's extra hours."""
	counted = min(hours, counting.daily_cap) if counting.daily_cap else hours
	rate = rate_for(kind, counting)
	return rate, round2(counted * rate)


def to_days(credited_hours: float, hours_per_day: float) -> float:
	if hours_per_day <= 0:
		raise ValueError("hours_per_day must be positive")
	return round2(credited_hours / hours_per_day)


def within_cap(days: float, held: float, cap: float) -> tuple[float, float]:
	"""(days added, days over the limit) when the person already holds `held` days."""
	if not cap:
		return round2(days), 0.0
	room = max(cap - held, 0.0)
	added = min(days, room)
	return round2(added), round2(days - added)
