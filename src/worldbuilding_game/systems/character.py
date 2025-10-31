"""Character generation helpers."""
from __future__ import annotations

import random
from typing import Dict, Iterable, Mapping

from ..data_loader import GameData
from ..entities import Player, Race
from ..rules import build_races

DEFAULT_ROLES = [
    "Navigator Ley",
    "Spellblade",
    "Diplomat Court",
    "Artisan Rune",
]

ROLE_SKILLS: Mapping[str, Iterable[str]] = {
    "Navigator Ley": ("Navigasi bintang", "Pembacaan ley"),
    "Spellblade": ("Pedang aura", "Teknik fokus"),
    "Diplomat Court": ("Etiket kerajaan", "Negosiasi multiras"),
    "Artisan Rune": ("Ukir rune", "Sintesis alkimia"),
}

ROLE_TRAITS: Mapping[str, Iterable[str]] = {
    "Navigator Ley": ("Keen Senses", "Ley Attuned"),
    "Spellblade": ("Blade Dancer", "Mana Channeler"),
    "Diplomat Court": ("Silver Tongue", "Calming Presence"),
    "Artisan Rune": ("Runic Scholar", "Tireless Crafter"),
}

ROLE_AFFINITIES: Mapping[str, Mapping[str, int]] = {
    "Navigator Ley": {"Arcana": 2, "Navigasi": 3},
    "Spellblade": {"Tempur": 3, "Arcana": 1},
    "Diplomat Court": {"Diplomasi": 3, "Intel": 1},
    "Artisan Rune": {"Kerajinan": 3, "Arcana": 2},
}

RACE_TRAITS: Mapping[str, Iterable[str]] = {
    "human": ("Adaptive", "Resourceful"),
    "elf": ("Keen Senses", "Nature Bond"),
    "dwarf": ("Stone Endurance", "Forge Born"),
}

RACE_STARTING_ITEMS: Mapping[str, Iterable[str]] = {
    "human": ("Kit perjalanan ringan",),
    "elf": ("Ampoule embun Sylveth",),
    "dwarf": ("Ransel besi Torrak",),
}

ROLE_STARTING_EQUIPMENT: Mapping[str, Iterable[str]] = {
    "Navigator Ley": ("Mantel ley", "Kompas bintang portabel"),
    "Spellblade": ("Pedang fokus", "Pelindung energi"),
    "Diplomat Court": ("Stola diplomasi", "Segel rekomendasi"),
    "Artisan Rune": ("Sarung tangan rune", "Toolkit arcanum"),
}


def _choose_race(rng: random.Random, races: Iterable[Race], override: str | None) -> Race:
    if override:
        normalized = override.lower()
        for race in races:
            if race.id == normalized or race.name.lower() == normalized:
                return race
    return rng.choice(list(races))


def _choose_role(rng: random.Random, override: str | None) -> str:
    if override:
        normalized = override.lower()
        for role in DEFAULT_ROLES:
            if role.lower() == normalized:
                return role
    return rng.choice(DEFAULT_ROLES)


def _generate_name(rng: random.Random, race: Race, override: str | None) -> str:
    if override:
        return override
    pools = {
        "human": ("Arkhaven", "Leyden", "Serana", "Kaleth"),
        "elf": ("Sylveth", "Neralei", "Faelar", "Ilyana"),
        "dwarf": ("Torrak", "Brumgar", "Nalda", "Gorrim"),
    }
    pool = pools.get(race.id, (race.name,))
    suffix = rng.randint(10, 999)
    return f"{rng.choice(pool)}-{suffix}"


def _apply_traits(player: Player, traits: Iterable[str]) -> None:
    for trait in traits:
        player.add_trait(trait)


def _apply_affinities(player: Player, affinities: Mapping[str, int]) -> None:
    for name, value in affinities.items():
        player.add_affinity(name, value)


def _apply_skills(player: Player, skills: Iterable[str]) -> None:
    for skill in skills:
        player.add_skill(skill)


def _apply_equipment(player: Player, gear: Iterable[str]) -> None:
    for item in gear:
        player.add_equipment(item)


def _apply_inventory(player: Player, items: Iterable[str]) -> None:
    for item in items:
        if item not in player.inventory:
            player.inventory.append(item)


def _roll_stats(rng: random.Random, overrides: Mapping[str, int] | None = None) -> Dict[str, int]:
    stats = {
        "vitality": rng.randint(5, 9),
        "finesse": rng.randint(5, 9),
        "focus": rng.randint(5, 9),
        "strength": rng.randint(4, 9),
        "dexterity": rng.randint(4, 9),
        "intellect": rng.randint(4, 9),
        "charisma": rng.randint(4, 9),
        "wisdom": rng.randint(4, 9),
    }
    stats.update({k: v for k, v in (overrides or {}).items() if k in stats})
    return stats


def generate_character(
    seed: int,
    data: GameData,
    *,
    allow_customize: bool = True,
    overrides: Mapping[str, object] | None = None,
) -> Player:
    """Generate a Player using the configured worldbuilding data."""

    rng = random.Random(seed)
    races = build_races(data.races)
    def _override(key: str) -> str | None:
        if not overrides:
            return None
        value = overrides.get(key)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    race = _choose_race(rng, races, _override("race"))
    role = _choose_role(rng, _override("role"))

    stats = _roll_stats(rng, overrides={k: v for k, v in (overrides or {}).items() if isinstance(v, int)})
    name = _generate_name(rng, race, _override("name"))

    player = Player(
        name=name,
        race=race,
        role=role,
        vitality=stats["vitality"],
        finesse=stats["finesse"],
        focus=stats["focus"],
        strength=stats["strength"],
        dexterity=stats["dexterity"],
        intellect=stats["intellect"],
        charisma=stats["charisma"],
        wisdom=stats["wisdom"],
    )
    player.apply_race_modifiers()

    _apply_skills(player, ROLE_SKILLS.get(role, ()))
    _apply_traits(player, ROLE_TRAITS.get(role, ()))
    _apply_affinities(player, ROLE_AFFINITIES.get(role, {}))
    _apply_traits(player, RACE_TRAITS.get(race.id, ()))
    _apply_inventory(player, RACE_STARTING_ITEMS.get(race.id, ()))
    _apply_equipment(player, ROLE_STARTING_EQUIPMENT.get(role, ()))

    player.rank = "Inisiat Arkhaven"
    player.location = "Arkhaven (Valmoria)"
    player.update_world_event("Tenang: Arus informasi belum berubah")
    player.heal_to_full()

    if allow_customize and overrides and overrides.get("affinities"):
        for name, value in overrides["affinities"].items():
            player.add_affinity(str(name), int(value))

    return player


def apply_level(player: Player, level: int) -> None:
    """Basic level scaling that buffs stats and health."""

    if level <= 1:
        return
    bonus = level - 1
    player.vitality += bonus
    player.strength += bonus // 2
    player.dexterity += bonus // 2
    player.wisdom += bonus // 2
    player.focus += bonus
    player.current_health = player.max_health


def trait_modifiers(player: Player, trait: str) -> int:
    """Return modifier bonuses granted by traits."""

    mapping = {
        "Keen Senses": 2,
        "Ley Attuned": 1,
        "Blade Dancer": 1,
        "Silver Tongue": 2,
        "Stone Endurance": 1,
        "Adaptive": 1,
    }
    if trait in player.traits:
        return mapping.get(trait, 0)
    return 0
