"""Domain models for Mana Hearth narrative game."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class Race:
    id: str
    name: str
    region: str
    description: str
    stat_modifiers: Dict[str, int]
    abilities: Sequence[str]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Race":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            region=str(data.get("region", "")),
            description=str(data.get("description", "")),
            stat_modifiers=dict(data.get("stat_modifiers", {})),
            abilities=tuple(data.get("abilities", [])),
        )


@dataclass(frozen=True)
class Location:
    name: str
    region: str
    type: str
    description: str
    factions: Sequence[str]
    encounter_tables: Dict[str, Sequence[str]]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Location":
        return cls(
            name=str(data["name"]),
            region=str(data.get("region", "")),
            type=str(data.get("type", "")),
            description=str(data.get("description", "")),
            factions=tuple(data.get("factions", [])),
            encounter_tables={key: tuple(value) for key, value in data.get("encounter_tables", {}).items()},
        )


@dataclass(frozen=True)
class Quest:
    id: str
    name: str
    region: str
    giver: str
    summary: str
    objectives: Sequence[str]
    rewards: Dict[str, object]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Quest":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            region=str(data.get("region", "")),
            giver=str(data.get("giver", "")),
            summary=str(data.get("summary", "")),
            objectives=tuple(data.get("objectives", [])),
            rewards=dict(data.get("rewards", {})),
        )


@dataclass(frozen=True)
class Monster:
    name: str
    tier: int
    region: str
    hit_points: int
    attack: int
    traits: Sequence[str]
    lore: str
    loot: Sequence[str]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Monster":
        return cls(
            name=str(data["name"]),
            tier=int(data.get("tier", 1)),
            region=str(data.get("region", "")),
            hit_points=int(data.get("hit_points", 1)),
            attack=int(data.get("attack", 0)),
            traits=tuple(data.get("traits", [])),
            lore=str(data.get("lore", "")),
            loot=tuple(data.get("loot", [])),
        )


@dataclass
class Player:
    name: str
    race: Race
    role: str
    vitality: int = 5
    finesse: int = 5
    focus: int = 5
    xp: int = 0
    inventory: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    buffs: List[str] = field(default_factory=list)
    affinities: Dict[str, int] = field(default_factory=dict)
    reputation: Dict[str, int] = field(default_factory=dict)
    gold: int = 75
    rank: str = "Inisiat Bebas"
    active_quest: str | None = None
    completed_quests: List[str] = field(default_factory=list)
    location: str = "Arkhaven"
    current_day: int = 1
    current_hour: int = 6
    world_event: str = "Tenang"
    current_health: int = field(init=False)

    def __post_init__(self) -> None:
        self.current_health = self.max_health

    def apply_race_modifiers(self) -> None:
        """Apply racial stat modifiers to the base attributes."""
        for key, delta in self.race.stat_modifiers.items():
            if hasattr(self, key):
                setattr(self, key, getattr(self, key) + delta)
        self.current_health = self.max_health

    @property
    def max_health(self) -> int:
        return self.vitality * 2 + 5

    def heal_to_full(self) -> None:
        self.current_health = self.max_health

    def receive_damage(self, amount: int) -> None:
        self.current_health = max(0, self.current_health - amount)

    @property
    def is_defeated(self) -> bool:
        return self.current_health <= 0

    @property
    def time_label(self) -> str:
        period = "Malam"
        if 5 <= self.current_hour < 12:
            period = "Pagi"
        elif 12 <= self.current_hour < 17:
            period = "Siang"
        elif 17 <= self.current_hour < 21:
            period = "Senja"
        return f"Hari {self.current_day}, {period} ({self.current_hour:02d}:00)"

    def advance_time(self, hours: int) -> None:
        self.current_hour += hours
        while self.current_hour >= 24:
            self.current_hour -= 24
            self.current_day += 1

    def set_location(self, name: str, region: str) -> None:
        self.location = f"{name} ({region})"

    def set_active_quest(self, quest_name: str | None) -> None:
        self.active_quest = quest_name

    def update_world_event(self, description: str) -> None:
        self.world_event = description

    def gain_gold(self, amount: int) -> None:
        self.gold += amount

    def spend_gold(self, amount: int) -> None:
        self.gold = max(0, self.gold - amount)

    def add_skill(self, skill: str) -> None:
        if skill not in self.skills:
            self.skills.append(skill)

    def add_equipment(self, item: str) -> None:
        if item not in self.equipment:
            self.equipment.append(item)

    def add_buff(self, buff: str) -> None:
        if buff not in self.buffs:
            self.buffs.append(buff)

    def clear_temporary_buffs(self) -> None:
        self.buffs = [buff for buff in self.buffs if "(sementara)" not in buff]

    def add_affinity(self, name: str, value: int) -> None:
        self.affinities[name] = self.affinities.get(name, 0) + value

    def adjust_reputation(self, faction: str, delta: int) -> None:
        self.reputation[faction] = self.reputation.get(faction, 0) + delta

    def record_quest_completion(self, quest_name: str) -> None:
        if quest_name not in self.completed_quests:
            self.completed_quests.append(quest_name)



