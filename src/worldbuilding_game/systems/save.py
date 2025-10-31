"""Persistence helpers for Mana Hearth."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict

from ..data_loader import GameData
from ..entities import Player, Race
from ..rules import build_races
from .actions import WorldState


def _serialize_rng(rng: random.Random) -> Dict[str, Any]:
    state = rng.getstate()
    return {
        "algorithm": state[0],
        "state": list(state[1]),
        "gauss": state[2],
    }


def _deserialize_rng(payload: Dict[str, Any]) -> random.Random:
    rng = random.Random()
    rng.setstate((payload["algorithm"], tuple(payload["state"]), payload["gauss"]))
    return rng


def save_world(world: WorldState, path: str | Path = "save.json") -> Path:
    """Persist the current world state to disk."""

    payload = {
        "player": world.player.to_dict(),
        "rng": _serialize_rng(world.rng),
        "tick": world.tick,
        "seed": world.seed,
    }
    destination = Path(path)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def load_world(path: str | Path, data: GameData | None = None) -> WorldState:
    """Load a world state from disk."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    data = data or GameData.load()
    rng = _deserialize_rng(payload["rng"])

    races = build_races(data.races)
    race_catalog: Dict[str, Race] = {race.id: race for race in races}
    player = Player.from_dict(payload["player"], race_catalog)

    world = WorldState(data=data, player=player, rng=rng, seed=payload.get("seed"))
    world.tick = int(payload.get("tick", 0))
    return world
