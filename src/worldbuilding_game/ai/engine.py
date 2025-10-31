"""Autonomous engine that drives the Mana Hearth world without user input."""
from __future__ import annotations

import time
from typing import Callable

from ..systems.actions import CommandResult, WorldState
from .policy import Policy, UtilityPolicy
from ..systems.save import save_world


class AIEngine:
    def __init__(
        self,
        world: WorldState,
        *,
        policy: Policy | None = None,
        executor: Callable[[str], CommandResult] | None = None,
        rate: float = 1.0,
        save_every: int | None = None,
        headless: bool = False,
        save_path: str = "autosave.json",
    ) -> None:
        self.world = world
        self.policy = policy or UtilityPolicy(world.rng)
        self.executor = executor
        self.rate = rate
        self.save_every = save_every
        self.headless = headless
        self.save_path = save_path
        self._ticks_executed = 0

    def run(self, ticks: int) -> int:
        """Run the engine for ``ticks`` iterations (``-1`` for unlimited)."""

        executed = 0
        while ticks < 0 or executed < ticks:
            command = self.policy.act(self.world)
            if self.executor is None:
                raise RuntimeError("AIEngine requires an executor callable")
            result = self.executor(command)
            executed += 1
            self._ticks_executed += 1

            if self.save_every and executed % self.save_every == 0:
                save_world(self.world, self.save_path)

            if result.exit_game:
                break

            if self.rate > 0 and not self.headless:
                time.sleep(max(0.0, 1.0 / self.rate))
        return executed

    @property
    def ticks_executed(self) -> int:
        return self._ticks_executed
