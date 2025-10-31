"""AI policies for autonomous exploration."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from ..entities import Player
from ..systems.actions import ActionOption, WorldState, suggest_actions


@dataclass
class PolicyContext:
    options: List[ActionOption]


class Policy:
    """Interface for policies that decide commands for the AI engine."""

    def __init__(self) -> None:
        self._context: Optional[PolicyContext] = None

    def perceive(self, world: WorldState) -> PolicyContext:
        options = suggest_actions(world)
        self._context = PolicyContext(options)
        return self._context

    def decide(self, world: WorldState) -> ActionOption:
        context = self._context or self.perceive(world)
        if not context.options:
            raise RuntimeError("No actions available for policy to decide")
        return context.options[0]

    def act(self, world: WorldState) -> str:
        option = self.decide(world)
        return option.command


class UtilityPolicy(Policy):
    """Heuristic policy using simple utility scoring."""

    def __init__(self, rng: random.Random | None = None) -> None:
        super().__init__()
        self.rng = rng or random.Random()

    def _need_hp(self, player: Player) -> float:
        return 1.0 - (player.current_health / max(1, player.max_health))

    def _quest_value(self, command: str, player: Player) -> float:
        if "quest take" in command and not player.active_quest:
            return 1.0
        if "quest turnin" in command and player.active_quest:
            return 0.8
        return 0.2 if "quest" in command else 0.0

    def _loot_opportunity(self, command: str) -> float:
        if command.startswith("event"):
            return 0.9
        if command.startswith("move"):
            return 0.4
        return 0.2 if command.startswith("look") else 0.0

    def _threat_gap(self, player: Player) -> float:
        offense = player.strength + player.focus + len(player.skills)
        defense = player.vitality + player.wisdom
        return (offense - defense) / 20.0

    def _distance_cost(self, command: str) -> float:
        if command.startswith("move"):
            return 1.0
        return 0.0

    def decide(self, world: WorldState) -> ActionOption:
        context = self.perceive(world)
        player = world.player
        best_option = None
        best_score = float("-inf")
        for option in context.options:
            jitter = self.rng.uniform(-0.05, 0.05)
            score = (
                2.5 * self._need_hp(player)
                + 1.5 * self._quest_value(option.command, player)
                + 1.5 * self._loot_opportunity(option.command)
                + 1.0 * self._threat_gap(player)
                - 0.5 * self._distance_cost(option.command)
                + option.score
                + jitter
            )
            if option.command == "rest":
                score += 1.0 + 2.0 * self._need_hp(player)
            if best_option is None or score > best_score:
                best_option = option
                best_score = score
        return best_option or context.options[0]


class LLMPolicy(Policy):
    """Placeholder for future LLM-driven policies."""

    def act(self, world: WorldState) -> str:  # pragma: no cover - placeholder
        raise NotImplementedError("LLMPolicy is a stub and requires integration")
