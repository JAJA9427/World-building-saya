from __future__ import annotations

import random

from worldbuilding_game.systems.rules import check


class FakeRandom(random.Random):
    def __init__(self, values: list[int]):
        super().__init__()
        self._values = iter(values)

    def randint(self, a: int, b: int) -> int:  # type: ignore[override]
        return next(self._values)


def test_check_with_advantage_outperforms_normal():
    plain = FakeRandom([10])
    advantaged = FakeRandom([10, 18])

    base = check(plain, stat_value=0, dc=15)
    adv = check(advantaged, stat_value=0, dc=15, advantage=True)

    assert not base.success
    assert adv.success
