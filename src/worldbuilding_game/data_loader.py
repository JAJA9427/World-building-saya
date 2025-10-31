"""Utilities for loading structured worldbuilding data from JSON resources."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

_DATA_DIR = Path(__file__).resolve().parent / "data"


def _read_json(name: str) -> Any:
    path = _DATA_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_world() -> Dict[str, Any]:
    """Return world metadata including locations and factions."""
    return _read_json("world.json")


def load_races() -> List[Dict[str, Any]]:
    """Return available playable races."""
    return _read_json("races.json")


def load_monsters() -> List[Dict[str, Any]]:
    """Return encounterable monsters."""
    return _read_json("monsters.json")


def load_quests() -> List[Dict[str, Any]]:
    """Return quest templates."""
    return _read_json("quests.json")


@dataclass(frozen=True)
class GameData:
    """Bundle of frequently used worldbuilding datasets."""

    world: Dict[str, Any]
    races: List[Dict[str, Any]]
    monsters: List[Dict[str, Any]]
    quests: List[Dict[str, Any]]

    @classmethod
    def load(cls) -> "GameData":
        """Load all data files eagerly to simplify the rest of the engine."""
        return cls(
            world=load_world(),
            races=load_races(),
            monsters=load_monsters(),
            quests=load_quests(),
        )
