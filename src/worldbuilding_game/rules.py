"""Game rules and helper utilities for the Mana Hearth narrative adventure."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .entities import Location, Monster, Player, Quest, Race


@dataclass
class CombatLog:
    """Record of a combat simulation."""

    rounds: List[str]
    player_won: bool
    remaining_health: int
    monster_remaining: int


def build_races(data: Sequence[dict]) -> List[Race]:
    return [Race.from_dict(entry) for entry in data]


def build_locations(data: Sequence[dict]) -> List[Location]:
    return [Location.from_dict(entry) for entry in data]


def build_monsters(data: Sequence[dict]) -> List[Monster]:
    return [Monster.from_dict(entry) for entry in data]


def build_quests(data: Sequence[dict]) -> List[Quest]:
    return [Quest.from_dict(entry) for entry in data]


def quests_for_region(quests: Iterable[Quest], region: str) -> List[Quest]:
    return [quest for quest in quests if quest.region == region]


def pick_random(items: Sequence[str], rng: random.Random) -> str:
    return rng.choice(list(items))


def roll_event(location: Location, table: str, rng: random.Random) -> str:
    entries = location.encounter_tables.get(table, ())
    if not entries:
        return "Tidak ada peristiwa khusus."
    return pick_random(entries, rng)


def select_monster(monsters: Sequence[Monster], region: str, rng: random.Random) -> Monster:
    candidates = [monster for monster in monsters if monster.region == region]
    pool = candidates or list(monsters)
    return rng.choice(pool)


def roll_regional_event(world_data: dict, region: str, rng: random.Random) -> str:
    regional = world_data.get("regional_events", {})
    entries = regional.get(region, ())
    if not entries:
        return "Wilayah tampak stabil tanpa kabar besar."
    return pick_random(tuple(entries), rng)


def roll_global_event(world_data: dict, rng: random.Random) -> Tuple[str, str]:
    catalog = world_data.get("global_events", {})
    if not catalog:
        return ("Global", "Tidak ada kabar global yang berarti.")
    category = rng.choice(list(catalog.keys()))
    entries = catalog.get(category, ())
    if not entries:
        return category, "Tidak ada kabar global yang berarti."
    description = pick_random(tuple(entries), rng)
    return category, description


def monster_damage(monster: Monster, rng: random.Random) -> int:
    swing = rng.randint(-2, 2)
    return max(0, monster.attack + swing)


def player_damage(player: Player, rng: random.Random) -> int:
    base = player.finesse // 2 + player.focus // 2
    swing = rng.randint(0, 6)
    return max(1, base + swing)


def resolve_combat(
    player: Player,
    monster: Monster,
    rng: random.Random,
    attack_bonus: int = 0,
    defense_bonus: int = 0,
) -> CombatLog:
    player_hp = player.max_health
    monster_hp = monster.hit_points
    rounds: List[str] = []
    round_counter = 1

    while player_hp > 0 and monster_hp > 0:
        player_roll = max(1, player_damage(player, rng) + attack_bonus)
        monster_hp = max(0, monster_hp - player_roll)
        rounds.append(
            f"Ronde {round_counter}: {player.name} menyerang {monster.name} untuk {player_roll} damage (HP monster {monster_hp})."
        )
        if monster_hp <= 0:
            break
        monster_roll = monster_damage(monster, rng)
        mitigation = 2 if player.race.id == "dwarf" else 0
        mitigated = max(0, monster_roll - mitigation - defense_bonus)
        player_hp = max(0, player_hp - mitigated)
        rounds.append(
            f"Ronde {round_counter}: {monster.name} membalas untuk {mitigated} damage (HP {player.name} {player_hp})."
        )
        round_counter += 1

    player.current_health = player_hp
    return CombatLog(
        rounds=rounds,
        player_won=player_hp > 0,
        remaining_health=player_hp,
        monster_remaining=monster_hp,
    )


def apply_rewards(player: Player, quest: Quest) -> None:
    player.xp += int(quest.rewards.get("xp", 0))
    items = quest.rewards.get("items", [])
    for item in items:
        player.inventory.append(str(item))

    for equipment in quest.rewards.get("equipment", []):
        player.add_equipment(str(equipment))

    for skill in quest.rewards.get("skills", []):
        player.add_skill(str(skill))

    player.gain_gold(int(quest.rewards.get("gold", 0)))

    for affinity, value in quest.rewards.get("affinities", {}).items():
        player.add_affinity(str(affinity), int(value))

    for faction, delta in quest.rewards.get("reputation", {}).items():
        player.adjust_reputation(str(faction), int(delta))

    player.record_quest_completion(quest.name)


def format_objectives(objectives: Sequence[str]) -> str:
    return "\n".join(f"  • {objective}" for objective in objectives)


def describe_monster(monster: Monster) -> str:
    traits = ", ".join(monster.traits)
    loot = ", ".join(monster.loot)
    return (
        f"{monster.name} (Tier {monster.tier})\n"
        f"  Ciri: {traits}\n"
        f"  Lore: {monster.lore}\n"
        f"  Loot: {loot}"
    )

