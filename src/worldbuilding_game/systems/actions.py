"""Core gameplay actions for the Mana Hearth CLI."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence

from ..data_loader import GameData
from ..entities import Player
from ..rules import (
    apply_rewards,
    build_locations,
    build_monsters,
    build_quests,
    describe_monster,
    format_objectives,
    quests_for_region,
    resolve_combat,
    roll_event,
    roll_global_event,
    roll_regional_event,
    select_monster,
)
from .rules import check, contest


@dataclass
class ActionOption:
    command: str
    label: str
    score: float = 0.0
    hint: str | None = None


@dataclass
class CommandResult:
    message: str
    exit_game: bool = False


@dataclass
class WorldState:
    data: GameData
    player: Player
    rng: random.Random
    seed: int | None = None
    tick: int = 0
    log: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.locations = build_locations(self.data.world["locations"])
        self.quests = build_quests(self.data.quests)
        self.monsters = build_monsters(self.data.monsters)
        self._location_lookup = {
            location.name.lower(): location for location in self.locations
        }
        self._location_lookup.update(
            {f"{loc.name.lower()} ({loc.region.lower()})": loc for loc in self.locations}
        )
        self._location_lookup.update(
            {f"{loc.name.lower()}/{loc.region.lower()}": loc for loc in self.locations}
        )

    def add_log(self, text: str) -> None:
        self.log.append(text)

    def find_location(self, name: str):
        return self._location_lookup.get(name.lower())


def _format_affinities(affinities: Dict[str, int]) -> str:
    if not affinities:
        return "-"
    return ", ".join(f"{key}: {value}" for key, value in sorted(affinities.items()))


def _format_mapping(mapping: Dict[str, int]) -> str:
    if not mapping:
        return "-"
    return ", ".join(f"{key}: {value}" for key, value in sorted(mapping.items()))


def show_hud(world: WorldState) -> str:
    player = world.player
    lines = [
        f"Nama: {player.name} | Ras: {player.race.name} | Rank: {player.rank}",
        f"Peran: {player.role} | Lokasi: {player.location} | Waktu: {player.time_label}",
        f"Quest Aktif: {player.active_quest or '-'}",
        f"Affinitas: {_format_affinities(player.affinities)}",
        f"Reputasi: {_format_mapping(player.reputation)}",
        f"Kondisi Dunia: {player.world_event}",
        (
            "Stats: "
            f"STR {player.strength} | DEX {player.dexterity} | INT {player.intellect} | "
            f"CHA {player.charisma} | VIT {player.vitality} | WIS {player.wisdom} | "
            f"Finesse {player.finesse} | Focus {player.focus} | HP {player.current_health}/{player.max_health}"
        ),
        f"Skills: {', '.join(player.skills) if player.skills else '-'}",
        f"Traits: {', '.join(player.traits) if player.traits else '-'}",
        f"Buffs: {', '.join(player.buffs) if player.buffs else '-'}",
        f"Equipment: {', '.join(player.equipment) if player.equipment else '-'}",
        f"Inventory: {', '.join(player.inventory) if player.inventory else '-'}",
        f"Emas: {player.gold}",
    ]
    return "\n".join(lines)


def look_around(world: WorldState) -> str:
    location = world.player.location
    target = world.find_location(location)
    if not target:
        return "Lokasi tidak dikenal."
    local = roll_event(target, "travel", world.rng)
    regional = roll_regional_event(world.data.world, target.region, world.rng)
    category, global_event = roll_global_event(world.data.world, world.rng)
    world.player.update_world_event(f"{category.title()}: {global_event}")
    world.player.advance_time(1)
    world.tick += 1
    return (
        f"Mengamati {target.name}: {local}\n"
        f"Regional: {regional}\nGlobal: {category.title()}: {global_event}"
    )


def move_to(world: WorldState, destination: str) -> str:
    location = world.find_location(destination)
    if not location:
        return "Tujuan tidak ditemukan. Gunakan 'look' untuk melihat lokasi tersedia."

    player = world.player
    current_location = world.find_location(player.location) or location
    dc = 12 if location.region != current_location.region else 10
    advantage = player.role == "Navigator Ley"
    result = check(
        world.rng,
        player.dexterity,
        dc,
        advantage=advantage,
        modifiers=[1 if "Adaptive" in player.traits else 0],
    )
    player.set_location(location.name, location.region)
    player.advance_time(2)
    world.tick += 1
    description = [
        f"Bergerak menuju {location.name} ({location.region})",
        f"Hasil navigasi: total {result.total} {'sukses' if result.success else 'gagal'} (DC {result.dc}).",
        f"Rumor lokal: {roll_event(location, 'rumor', world.rng)}",
    ]
    if not result.success:
        damage = max(1, 3 - (1 if "Stone Endurance" in player.traits else 0))
        player.receive_damage(damage)
        description.append(f"Anda tersandung selama perjalanan dan kehilangan {damage} HP.")
    world.add_log(description[0])
    return "\n".join(description)


def rest(world: WorldState) -> str:
    player = world.player
    healed = player.max_health - player.current_health
    player.heal_to_full()
    player.advance_time(6)
    world.tick += 1
    player.clear_temporary_buffs()
    player.add_buff("Kesiapan Baru (sementara)")
    return f"Tim beristirahat. HP pulih {healed}."


def trigger_event(world: WorldState) -> str:
    player = world.player
    current_location = world.find_location(player.location)
    if not current_location:
        return "Lokasi saat ini tidak dikenali."

    quest_candidates = quests_for_region(world.quests, current_location.region)
    quest = quest_candidates[0] if quest_candidates else None
    monster = select_monster(world.monsters, current_location.region, world.rng)

    contest_result = contest(
        world.rng,
        player.strength + (1 if "Blade Dancer" in player.traits else 0),
        monster.tier * 2 + 10,
    )
    attack_bonus = 1 if contest_result.winner == "attacker" else 0
    defense_bonus = 1 if "Stone Endurance" in player.traits else 0

    combat = resolve_combat(
        player,
        monster,
        world.rng,
        attack_bonus=attack_bonus,
        defense_bonus=defense_bonus,
    )
    player.advance_time(3)
    world.tick += 1

    lines = [
        f"Terlibat dengan {monster.name}.",
        describe_monster(monster),
        "Hasil pertempuran:",
        *[f"- {entry}" for entry in combat.rounds],
    ]
    if combat.player_won:
        lines.append(f"{player.name} menang dengan {combat.remaining_health} HP tersisa.")
        if quest and player.active_quest is None:
            player.set_active_quest(quest.name)
            lines.append(f"Quest baru diambil: {quest.name}")
        if quest and quest.name not in player.completed_quests:
            apply_rewards(player, quest)
    else:
        lines.append(f"{player.name} kalah dan mundur ke posisi aman.")
        player.heal_to_full()

    return "\n".join(lines)


def use_item(world: WorldState, item: str) -> str:
    player = world.player
    for idx, entry in enumerate(player.inventory):
        if entry.lower() == item.lower():
            player.inventory.pop(idx)
            heal = 5
            player.current_health = min(player.max_health, player.current_health + heal)
            return f"Menggunakan {entry}. HP pulih {heal}."
    return f"Item '{item}' tidak ada di inventaris."


def equip_item(world: WorldState, item: str) -> str:
    player = world.player
    for idx, entry in enumerate(player.inventory):
        if entry.lower() == item.lower():
            if entry not in player.equipment:
                player.equipment.append(entry)
            player.inventory.pop(idx)
            return f"Mengenakan {entry}."
    return f"Item '{item}' tidak ada di inventaris."


def list_inventory(world: WorldState) -> str:
    player = world.player
    return "Inventaris: " + (", ".join(player.inventory) if player.inventory else "Kosong")


def list_skills(world: WorldState) -> str:
    player = world.player
    return "Skill: " + (", ".join(player.skills) if player.skills else "Belum ada skill khusus")


def quest_action(world: WorldState, action: str) -> str:
    player = world.player
    location = world.find_location(player.location)
    if not location:
        return "Lokasi saat ini tidak dikenali."
    quests = quests_for_region(world.quests, location.region)

    if action == "list":
        if not quests:
            return "Tidak ada quest yang tersedia di wilayah ini."
        entries = [f"- {quest.name}: {quest.summary}" for quest in quests]
        return "Quest tersedia:\n" + "\n".join(entries)
    if action == "take":
        if player.active_quest:
            return f"Sudah menjalankan quest '{player.active_quest}'."
        if not quests:
            return "Belum ada quest untuk diambil."
        quest = quests[0]
        player.set_active_quest(quest.name)
        return f"Mengambil quest '{quest.name}'.\nLangkah-langkah:\n{format_objectives(quest.objectives)}"
    if action == "turnin":
        if not player.active_quest:
            return "Tidak ada quest aktif untuk diserahkan."
        player.completed_quests.append(player.active_quest)
        player.set_active_quest(None)
        player.gain_gold(15)
        return "Quest diserahkan. Reputasi meningkat."
    return "Perintah quest tidak dikenali."


def simulate_round(world: WorldState, steps: int = 1) -> str:
    summaries: List[str] = []
    for _ in range(max(1, steps)):
        summaries.append(look_around(world))
        summaries.append(trigger_event(world))
    return "\n\n".join(summaries)


def suggest_actions(world: WorldState, limit: int = 6) -> List[ActionOption]:
    player = world.player
    options: List[ActionOption] = []
    health_ratio = player.current_health / player.max_health

    options.append(ActionOption(command="look", label="look         (intip peluang event)", score=0.6))

    if health_ratio < 0.6:
        options.append(ActionOption(command="rest", label="rest         (pulihkan VIT)", score=1.0))
    else:
        options.append(ActionOption(command="event", label="event        (tantang ancaman)", score=0.8))

    location_names = [f"{loc.name}/{loc.region}" for loc in world.locations[:4]]
    for idx, name in enumerate(location_names):
        weight = 0.5 - idx * 0.1
        options.append(
            ActionOption(command=f"move {name}", label=f"move {name} (perjalanan)", score=weight)
        )

    if not player.active_quest:
        options.append(ActionOption(command="quest take", label="quest take  (ambil quest)", score=0.7))
    else:
        options.append(ActionOption(command="quest turnin", label="quest turnin (serahkan quest)", score=0.65))

    options.append(ActionOption(command="hud", label="hud          (lihat status)", score=0.4))

    options.sort(key=lambda opt: opt.score, reverse=True)
    return options[: limit or len(options)]
