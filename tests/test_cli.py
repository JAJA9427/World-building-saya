from __future__ import annotations

import random

from worldbuilding_game import cli
from worldbuilding_game.data_loader import GameData
from worldbuilding_game.systems.actions import WorldState
from worldbuilding_game.systems.character import generate_character


def make_world(seed: int = 42) -> WorldState:
    data = GameData.load()
    player = generate_character(seed, data)
    return WorldState(data=data, player=player, rng=random.Random(seed), seed=seed)


def test_numeric_parser_executes_second_option():
    world = make_world()
    outputs: list[str] = []
    inputs = iter(["2", "quit"])

    cli.interactive_loop(
        world,
        input_func=lambda _: next(inputs),
        output=outputs.append,
    )

    assert any("Mengambil quest" in line for line in outputs)
    assert world.player.active_quest is not None


def test_text_parser_move_command_updates_location():
    world = make_world(99)
    target = next(loc for loc in world.locations if loc.name not in world.player.location)
    result = cli.execute_command(world, f"move {target.name}/{target.region}")
    assert target.name in world.player.location
    assert "Bergerak menuju" in result.message
