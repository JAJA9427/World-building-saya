from __future__ import annotations

import random

from worldbuilding_game.ai.engine import AIEngine
from worldbuilding_game.ai.policy import UtilityPolicy
from worldbuilding_game.data_loader import GameData
from worldbuilding_game.systems.actions import CommandResult, WorldState
from worldbuilding_game.systems.character import generate_character
from worldbuilding_game import cli


def make_world(seed: int = 101) -> WorldState:
    data = GameData.load()
    player = generate_character(seed, data)
    return WorldState(data=data, player=player, rng=random.Random(seed), seed=seed)


def test_policy_prefers_rest_when_health_low():
    world = make_world()
    world.player.current_health = 1
    policy = UtilityPolicy(random.Random(0))
    option = policy.decide(world)
    assert option.command == "rest"


class CountingPolicy(UtilityPolicy):
    def __init__(self, rng: random.Random | None = None) -> None:
        super().__init__(rng)
        self.decisions = 0

    def decide(self, world: WorldState):
        self.decisions += 1
        return super().decide(world)


def test_ai_engine_runs_requested_ticks():
    world = make_world(202)
    policy = CountingPolicy(random.Random(4))
    engine = AIEngine(
        world,
        policy=policy,
        executor=lambda command: CommandResult(f"executed {command}"),
        rate=0.0,
        headless=True,
    )
    executed = engine.run(20)
    assert executed == 20
    assert policy.decisions >= 20
    assert engine.ticks_executed >= 20


def test_policy_sequence_reproducible_with_seed():
    world_one = make_world(333)
    world_two = make_world(333)
    policy_one = UtilityPolicy(random.Random(12))
    policy_two = UtilityPolicy(random.Random(12))

    commands_one: list[str] = []
    commands_two: list[str] = []
    for _ in range(5):
        command_one = policy_one.act(world_one)
        commands_one.append(command_one)
        cli.execute_command(world_one, command_one)

        command_two = policy_two.act(world_two)
        commands_two.append(command_two)
        cli.execute_command(world_two, command_two)

    assert commands_one == commands_two
