"""Command-line interface for the enhanced Mana Hearth experience."""
from __future__ import annotations

import argparse
import random
import sys
import textwrap
from pathlib import Path
from typing import Callable, List, Sequence

from .ai.engine import AIEngine
from .ai.policy import UtilityPolicy
from .data_loader import GameData
from .systems.actions import (
    ActionOption,
    CommandResult,
    WorldState,
    equip_item,
    list_inventory,
    list_skills,
    look_around,
    move_to,
    quest_action,
    rest,
    show_hud,
    simulate_round,
    suggest_actions,
    trigger_event,
    use_item,
)
from .systems.character import DEFAULT_ROLES, generate_character
from .systems.save import load_world, save_world

HELP_TEXT = textwrap.dedent(
    """
    Perintah yang tersedia:
      help                Tampilkan bantuan ini
      hud                 Lihat status tim
      look                Lihat keadaan sekitar lokasi saat ini
      move <lokasi>       Bergerak ke lokasi lain (contoh: move Arkhaven/Valmoria)
      event               Picu pertemuan di lokasi aktif
      rest                Istirahat untuk memulihkan HP
      inv                 Lihat inventaris
      equip <item>        Mengenakan item dari inventaris
      use <item>          Menggunakan item dari inventaris
      skills              Lihat daftar skill saat ini
      quest <perintah>    Kelola quest (list | take | turnin)
      sim <n>             Simulasikan sejumlah ronde otomatis
      save [file]         Simpan permainan (default: save.json)
      load [file]         Muat permainan dari berkas
      quit                Keluar dari permainan
    """
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jelajahi dunia Mana Hearth secara interaktif")
    parser.add_argument("--seed", type=int, help="Seed RNG untuk determinisme")
    parser.add_argument("--interactive", action="store_true", help="Paksa mode interaktif")
    parser.add_argument("--auto", action="store_true", help="Mode otomatis berdasarkan menu")
    parser.add_argument("--script", nargs="*", help="Urutan pilihan/command untuk mode otomatis")
    parser.add_argument("--rounds", type=int, help="Jumlah ronde pada mode otomatis", default=5)
    parser.add_argument("--ai", action="store_true", help="Aktifkan policy AI untuk simulasi panjang")
    parser.add_argument("--ticks", type=int, default=100, help="Jumlah tick AI (gunakan -1 untuk tanpa batas)")
    parser.add_argument("--rate", type=float, default=4.0, help="Tick per detik untuk AI")
    parser.add_argument("--save-every", type=int, help="Frekuensi autosave dalam tick")
    parser.add_argument("--headless", action="store_true", help="Suppress output saat AI berjalan")
    parser.add_argument("--reroll-limit", type=int, default=5, help="Batas reroll saat membuat karakter")
    return parser


def print_world_overview(data: GameData, output: Callable[[str], None] = print) -> None:
    world = data.world
    overview = textwrap.fill(world["summary"], width=80)
    output(f"Dunia {world['world_name']} di planet {world['planet']}")
    output(overview)
    output(
        f"Durasi hari: {world['day_length_hours']} jam | Tahun: {world['year_length_days']} hari | Jumlah bulan: {world['moon_count']}"
    )
    output("Musim pasang ikonik:")
    for season in world["tidal_seasons"]:
        output(f"- {season['name']}: {season['description']}")


def render_menu(world: WorldState) -> List[ActionOption]:
    return suggest_actions(world)


def execute_command(world: WorldState, command: str) -> CommandResult:
    tokens = command.strip().split()
    if not tokens:
        return CommandResult("Perintah kosong. Ketik 'help' untuk bantuan.")
    verb = tokens[0].lower()
    args = tokens[1:]

    if verb in {"quit", "exit"}:
        return CommandResult("Petualangan selesai. Sampai jumpa lagi!", exit_game=True)
    if verb == "help":
        return CommandResult(HELP_TEXT)
    if verb == "hud":
        return CommandResult(show_hud(world))
    if verb == "look":
        return CommandResult(look_around(world))
    if verb == "move":
        if not args:
            return CommandResult("Sebutkan tujuan, contoh: move Hutan Sylveth/Valmoria")
        destination = " ".join(args)
        return CommandResult(move_to(world, destination))
    if verb == "event":
        return CommandResult(trigger_event(world))
    if verb == "rest":
        return CommandResult(rest(world))
    if verb == "inv":
        return CommandResult(list_inventory(world))
    if verb == "equip":
        if not args:
            return CommandResult("Sebutkan item yang ingin dipakai.")
        return CommandResult(equip_item(world, " ".join(args)))
    if verb == "use":
        if not args:
            return CommandResult("Sebutkan item yang ingin digunakan.")
        return CommandResult(use_item(world, " ".join(args)))
    if verb == "skills":
        return CommandResult(list_skills(world))
    if verb == "quest":
        action = args[0].lower() if args else "list"
        return CommandResult(quest_action(world, action))
    if verb == "sim":
        try:
            count = int(args[0]) if args else 1
        except ValueError:
            return CommandResult("Gunakan angka untuk jumlah simulasi.")
        return CommandResult(simulate_round(world, count))
    if verb == "save":
        path = Path(args[0]) if args else Path("save.json")
        save_world(world, path)
        return CommandResult(f"Permainan disimpan ke {path}")
    if verb == "load":
        path = Path(args[0]) if args else Path("save.json")
        loaded = load_world(path, world.data)
        world.player = loaded.player
        world.rng = loaded.rng
        world.tick = loaded.tick
        world.seed = loaded.seed
        return CommandResult(f"Permainan dimuat dari {path}")
    return CommandResult("Perintah tidak dikenali. Ketik 'help' untuk daftar perintah.")


def interactive_loop(
    world: WorldState,
    *,
    input_func: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> None:
    output(HELP_TEXT)
    while True:
        options = render_menu(world)
        output("\nPilihan hari ini:")
        for idx, option in enumerate(options, start=1):
            output(f"[{idx}] {option.label}")
        raw = input_func("> ").strip()
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(options):
                command = options[index - 1].command
            else:
                output("Pilihan di luar jangkauan.")
                continue
        else:
            command = raw

        result = execute_command(world, command)
        output(result.message)
        if result.exit_game:
            break


def _character_summary(world: WorldState) -> str:
    return show_hud(world)


def character_creation(
    data: GameData,
    rng: random.Random,
    *,
    reroll_limit: int,
    input_func: Callable[[str], str],
    output: Callable[[str], None],
) -> WorldState:
    rerolls = 0
    seed = rng.randint(1, 999999)
    overrides = {}
    while True:
        player = generate_character(seed, data, overrides=overrides)
        world = WorldState(data=data, player=player, rng=random.Random(seed), seed=seed)
        output("\n== Kandidat Karakter ==")
        output(_character_summary(world))
        output(
            "Pilihan: [1] Terima | [2] Reroll | [3] Customize | [4] Randomize penuh | [5] Load save"
        )
        choice = input_func("Pilih opsi: ").strip() or "1"
        if choice == "1":
            return world
        if choice == "2":
            if reroll_limit and rerolls >= reroll_limit:
                output("Reroll mencapai batas. Menggunakan kandidat terakhir.")
                return world
            rerolls += 1
            seed = rng.randint(1, 999999)
            overrides = {}
            continue
        if choice == "3":
            name = input_func("Nama kustom (kosong untuk pertahankan): ").strip()
            race = input_func("Ras (Manusia/Elf Sylveth/Kurcaci Torrak): ").strip()
            role = input_func(f"Peran ({', '.join(DEFAULT_ROLES)}): ").strip()
            overrides = {
                key: value
                for key, value in {
                    "name": name or overrides.get("name"),
                    "race": race or overrides.get("race"),
                    "role": role or overrides.get("role"),
                }.items()
                if value
            }
            continue
        if choice == "4":
            seed = rng.randint(1, 999999)
            overrides = {}
            continue
        if choice == "5":
            path = input_func("Berkas save (default save.json): ").strip() or "save.json"
            try:
                loaded = load_world(Path(path), data)
                return loaded
            except FileNotFoundError:
                output("Berkas tidak ditemukan.")
                continue
        output("Opsi tidak dikenali.")


def auto_run(world: WorldState, rounds: int, script: Sequence[str] | None) -> None:
    script_iter = iter(script or [])
    for _ in range(max(1, rounds)):
        options = render_menu(world)
        try:
            token = next(script_iter)
        except StopIteration:
            token = None
        if token is not None:
            if token.isdigit():
                index = int(token)
                command = options[(index - 1) % len(options)].command
            else:
                command = token
        else:
            command = options[0].command
        result = execute_command(world, command)
        print(result.message)
        if result.exit_game:
            break


def run_ai(world: WorldState, args: argparse.Namespace) -> None:
    policy = UtilityPolicy(world.rng)
    engine = AIEngine(
        world,
        policy=policy,
        executor=lambda command: execute_command(world, command),
        rate=args.rate,
        save_every=args.save_every,
        headless=args.headless,
    )
    engine.run(args.ticks)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data = GameData.load()
    rng = random.Random(args.seed)

    print_world_overview(data)

    interactive = args.interactive or (not args.auto and not args.ai)

    if interactive:
        world = character_creation(
            data,
            rng,
            reroll_limit=args.reroll_limit,
            input_func=input,
            output=print,
        )
        print(show_hud(world))
        interactive_loop(world)
        return 0

    # Non-interactive modes
    player = generate_character(rng.randint(1, 999999), data)
    world = WorldState(data=data, player=player, rng=rng, seed=args.seed)
    if args.auto:
        auto_run(world, args.rounds or 3, args.script)
    elif args.ai:
        run_ai(world, args)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
