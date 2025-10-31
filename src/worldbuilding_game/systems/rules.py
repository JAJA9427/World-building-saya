"""Core resolution systems such as skill checks and contests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import random


@dataclass(frozen=True)
class CheckResult:
    """Outcome of a skill check."""

    success: bool
    total: int
    rolls: Sequence[int]
    dc: int


def _roll_d20(rng: random.Random) -> int:
    return rng.randint(1, 20)


def check(
    rng: random.Random,
    stat_value: int,
    dc: int,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
    modifiers: Iterable[int] | None = None,
) -> CheckResult:
    """Resolve a d20 style skill check.

    The function is deterministic given a ``random.Random`` instance and is
    therefore easy to test.  The return value includes the rolled numbers so the
    caller can describe the outcome in the narrative layer.
    """

    base_rolls = [_roll_d20(rng)]
    if advantage or disadvantage:
        base_rolls.append(_roll_d20(rng))

    if advantage and not disadvantage:
        roll = max(base_rolls)
    elif disadvantage and not advantage:
        roll = min(base_rolls)
    else:
        roll = base_rolls[0]

    modifier_total = sum(modifiers or [])
    total = roll + stat_value + modifier_total
    return CheckResult(success=total >= dc, total=total, rolls=tuple(base_rolls), dc=dc)


@dataclass(frozen=True)
class ContestResult:
    """Outcome of a contested roll between two participants."""

    attacker_total: int
    defender_total: int
    winner: str | None


def contest(
    rng: random.Random,
    attacker_stat: int,
    defender_stat: int,
    *,
    attacker_mods: Iterable[int] | None = None,
    defender_mods: Iterable[int] | None = None,
) -> ContestResult:
    """Resolve a contested roll.

    Returns the totals for both parties and the string identifier of the
    winner (``"attacker"``/``"defender"``) or ``None`` if tied.
    """

    attacker_roll = _roll_d20(rng) + attacker_stat + sum(attacker_mods or [])
    defender_roll = _roll_d20(rng) + defender_stat + sum(defender_mods or [])

    if attacker_roll > defender_roll:
        winner = "attacker"
    elif defender_roll > attacker_roll:
        winner = "defender"
    else:
        winner = None
    return ContestResult(attacker_total=attacker_roll, defender_total=defender_roll, winner=winner)
