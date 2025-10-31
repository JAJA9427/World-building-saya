from __future__ import annotations

import random

from worldbuilding_game.data_loader import GameData
from worldbuilding_game.entities import Player
from worldbuilding_game.rules import (
    build_locations,
    build_monsters,
    build_quests,
    build_races,
    describe_monster,
    quests_for_region,
    resolve_combat,
)


def test_world_core_metadata():
    data = GameData.load()
    assert data.world["world_name"] == "Mana Hearth"
    assert data.world["planet"] == "Gaion"
    assert len(data.world["tidal_seasons"]) == 4
    assert set(data.world["global_events"].keys()) >= {"economy", "weather", "faction", "mystic"}


def test_races_and_locations():
    data = GameData.load()
    races = build_races(data.races)
    assert {race.name for race in races} >= {"Manusia", "Elf Sylveth", "Kurcaci Torrak"}

    locations = build_locations(data.world["locations"])
    regions = {loc.region for loc in locations}
    assert {"Valmoria", "Sylveth", "Orontes", "Torrak"}.issubset(regions)


def test_combat_resolution_deterministic():
    data = GameData.load()
    races = build_races(data.races)
    player_race = next(race for race in races if race.id == "human")
    hero = Player(name="Tester", race=player_race, role="Navigator Ley")
    hero.apply_race_modifiers()

    monsters = build_monsters(data.monsters)
    target = next(monster for monster in monsters if monster.name == "Slime Entropik")

    rng = random.Random(123)
    combat_log = resolve_combat(hero, target, rng)
    assert combat_log.player_won
    assert combat_log.remaining_health > 0
    assert "Slime Entropik" in " ".join(combat_log.rounds)


def test_combat_strategy_bonus_affects_result():
    data = GameData.load()
    races = build_races(data.races)
    player_race = next(race for race in races if race.id == "human")
    hero = Player(name="Strategist", race=player_race, role="Navigator Ley")
    hero.apply_race_modifiers()

    monsters = build_monsters(data.monsters)
    target = next(monster for monster in monsters if monster.name == "Slime Entropik")

    rng = random.Random(321)
    combat_log = resolve_combat(hero, target, rng, attack_bonus=3, defense_bonus=1)
    assert combat_log.player_won
    assert combat_log.remaining_health >= 0


def test_quests_have_regions():
    data = GameData.load()
    quests = build_quests(data.quests)
    region_map = {quest.region for quest in quests}
    assert {"Valmoria", "Sylveth", "Orontes", "Torrak"}.issubset(region_map)
    valmoria_quests = quests_for_region(quests, "Valmoria")
    assert any("Slime" in quest.name for quest in valmoria_quests)


def test_monster_description_includes_traits():
    data = GameData.load()
    monsters = build_monsters(data.monsters)
    magma = next(monster for monster in monsters if monster.name == "Naga Magma")
    description = describe_monster(magma)
    assert "Tier" in description and "Muntahan lava" in description


def test_player_hud_fields_progress():
    data = GameData.load()
    races = build_races(data.races)
    player_race = next(race for race in races if race.id == "human")
    adventurer = Player(name="HUD", race=player_race, role="Navigator Ley")
    adventurer.apply_race_modifiers()
    assert adventurer.gold >= 0
    adventurer.add_skill("Tes taktik")
    adventurer.add_buff("Momentum (sementara)")
    adventurer.advance_time(20)
    assert "Hari" in adventurer.time_label

