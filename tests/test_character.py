from __future__ import annotations

from worldbuilding_game.data_loader import GameData
from worldbuilding_game.systems.character import apply_level, generate_character, trait_modifiers


def test_generate_character_produces_reasonable_stats():
    data = GameData.load()
    player = generate_character(555, data)

    for stat in ["strength", "dexterity", "intellect", "charisma", "wisdom", "vitality", "finesse", "focus"]:
        value = getattr(player, stat)
        assert 3 <= value <= 15

    assert player.traits
    assert trait_modifiers(player, player.traits[0]) >= 0

    base_health = player.max_health
    apply_level(player, 3)
    assert player.max_health >= base_health
