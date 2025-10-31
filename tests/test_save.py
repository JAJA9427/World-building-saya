from __future__ import annotations

import random

from worldbuilding_game.data_loader import GameData
from worldbuilding_game.systems.actions import WorldState, move_to
from worldbuilding_game.systems.character import generate_character
from worldbuilding_game.systems.save import load_world, save_world


def test_save_load_roundtrip(tmp_path):
    data = GameData.load()
    player = generate_character(77, data)
    world = WorldState(data=data, player=player, rng=random.Random(77), seed=77)

    target = next(loc for loc in world.locations if loc.name not in world.player.location)
    move_to(world, f"{target.name}/{target.region}")
    expected_location = world.player.location
    expected_hp = world.player.current_health
    expected_inventory = len(world.player.inventory)

    path = tmp_path / "save.json"
    save_world(world, path)

    world.player.receive_damage(5)
    world.player.inventory.append("Kerikil")

    loaded = load_world(path, data)
    assert loaded.player.location == expected_location
    assert loaded.player.current_health == expected_hp
    assert len(loaded.player.inventory) == expected_inventory
