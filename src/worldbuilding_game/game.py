"""Command-line interface for the Mana Hearth worldbuilding adventure."""
from __future__ import annotations

import argparse
import random
import sys
import textwrap
from typing import Iterable, List, Sequence, Tuple

from .data_loader import GameData
from .entities import Player
from .rules import (
    apply_rewards,
    build_locations,
    build_monsters,
    build_quests,
    build_races,
    describe_monster,
    format_objectives,
    quests_for_region,
    resolve_combat,
    roll_event,
    roll_global_event,
    roll_regional_event,
    select_monster,
)

DEFAULT_ROLES = [
    "Navigator Ley",
    "Spellblade",
    "Diplomat Court",
    "Artisan Rune",
]


class DecisionProvider:
    """Abstract the difference between interactive and automated runs."""

    def choose(self, prompt: str, options: Sequence[str]) -> Tuple[str, str]:
        raise NotImplementedError

    def ask_text(self, prompt: str, default: str = "") -> str:
        raise NotImplementedError


class InteractiveDecisionProvider(DecisionProvider):
    def choose(self, prompt: str, options: Sequence[str]) -> Tuple[str, str]:
        print(prompt)
        for idx, option in enumerate(options, start=1):
            print(f"  {idx}. {option}")
        while True:
            try:
                selection = int(input("Pilih angka: "))
                if 1 <= selection <= len(options):
                    choice = options[selection - 1]
                    return choice, f"Memilih {choice}"
            except ValueError:
                pass
            print("Input tidak valid, coba lagi.")

    def ask_text(self, prompt: str, default: str = "") -> str:
        value = input(f"{prompt} ")
        return value.strip() or default


class AutoDecisionProvider(DecisionProvider):
    """Return deterministic choices for demonstration or testing."""

    def __init__(self, script: Iterable[str] | None = None):
        self._script = list(script or [])

    def choose(self, prompt: str, options: Sequence[str]) -> Tuple[str, str]:
        if self._script:
            index = int(self._script.pop(0)) % len(options)
            choice = options[index]
            return choice, f"Auto memilih {choice}"
        return options[0], f"Auto memilih {options[0]}"

    def ask_text(self, prompt: str, default: str = "") -> str:
        if self._script:
            return self._script.pop(0)
        return default or "Penjelajah"


def print_header(title: str) -> None:
    print("\n" + "=" * len(title))
    print(title)
    print("=" * len(title))


def format_mapping(mapping: dict[str, int]) -> str:
    if not mapping:
        return "-"
    return ", ".join(f"{key}: {value}" for key, value in mapping.items())


def format_list(values: Sequence[str]) -> str:
    if not values:
        return "-"
    return ", ".join(values)


def display_hud(player: Player) -> None:
    print_header("Status Tim")
    print(f"Nama: {player.name} | Ras: {player.race.name} | Rank: {player.rank}")
    print(f"Peran: {player.role} | Lokasi: {player.location} | Waktu: {player.time_label}")
    print(f"Quest Aktif: {player.active_quest or '-'}")
    print(f"Affinitas: {format_mapping(player.affinities)}")
    print(f"Reputasi: {format_mapping(player.reputation)}")
    print(f"Kondisi Dunia: {player.world_event}")
    print(
        "Stat: "
        f"Vitality {player.vitality} | Finesse {player.finesse} | Focus {player.focus} | HP {player.current_health}/{player.max_health}"
    )
    print(f"Skill: {format_list(player.skills)}")
    print(f"Buff: {format_list(player.buffs)}")
    print(f"Equipment: {format_list(player.equipment)}")
    print(f"Inventory: {format_list(player.inventory)}")
    print(f"Emas: {player.gold}")


def generate_team_events(location, world_data, rng: random.Random) -> dict[str, str]:
    local_event = roll_event(location, "travel", rng)
    regional_event = roll_regional_event(world_data, location.region, rng)
    category, global_event = roll_global_event(world_data, rng)
    return {
        "Lokal": local_event,
        "Regional": regional_event,
        "Global": f"{category.title()}: {global_event}",
    }


def describe_world(data: GameData) -> None:
    world = data.world
    summary = textwrap.fill(world["summary"], width=80)
    print_header(f"Dunia {world['world_name']} di planet {world['planet']}")
    print(summary)
    print(
        f"\nDurasi hari: {world['day_length_hours']} jam | Tahun: {world['year_length_days']} hari | Jumlah bulan: {world['moon_count']}"
    )
    print("\nMusim pasang ikonik:")
    for season in world["tidal_seasons"]:
        print(f"- {season['name']}: {season['description']}")


def create_player(decider: DecisionProvider, data: GameData, rng: random.Random) -> Player:
    races = build_races(data.races)
    name = decider.ask_text("Siapa nama penjelajah Anda?", default=f"Arkhaven-{rng.randint(100, 999)}")
    race_choice, note = decider.choose("Pilih ras awal:", [race.name for race in races])
    print(note)
    race = next(r for r in races if r.name == race_choice)

    role_choice, note = decider.choose("Pilih peran awal:", DEFAULT_ROLES)
    print(note)

    player = Player(name=name, race=race, role=role_choice)
    player.apply_race_modifiers()
    player.rank = "Inisiat Arkhaven"
    player.inventory.extend(["Kit perjalanan ringan", "Kristal penyeimbang kecil"])
    player.equipment.extend(["Mantel ley", "Kompas bintang portabel"])

    role_skills = {
        "Navigator Ley": ["Navigasi bintang", "Pembacaan ley"],
        "Spellblade": ["Pedang aura", "Teknik fokus"],
        "Diplomat Court": ["Etiket kerajaan", "Negosiasi multiras"],
        "Artisan Rune": ["Ukir rune", "Sintesis alkimia"],
    }
    for skill in role_skills.get(role_choice, []):
        player.add_skill(skill)

    role_affinities = {
        "Navigator Ley": {"Arcana": 2, "Navigasi": 3},
        "Spellblade": {"Tempur": 3, "Arcana": 1},
        "Diplomat Court": {"Diplomasi": 3, "Intel": 1},
        "Artisan Rune": {"Kerajinan": 3, "Arcana": 2},
    }
    for affinity, value in role_affinities.get(role_choice, {}).items():
        player.add_affinity(affinity, value)

    race_affinity = {
        "Elf Sylveth": {"Naturae": 3},
        "Kurcaci Torrak": {"Ketahanan": 2, "Logam": 1},
        "Manusia": {"Adaptif": 2},
    }
    for affinity, value in race_affinity.get(race.name, {}).items():
        player.add_affinity(affinity, value)

    player.reputation = {
        faction["name"]: (2 if faction.get("region") == race.region else 0)
        for faction in data.world.get("factions", [])
    }
    player.gold += 25
    player.location = "Arkhaven (Valmoria)"
    player.update_world_event("Tenang: Arus informasi belum berubah")

    print(
        f"\n{name} memulai sebagai {race.name} ({race.region}) dengan peran {role_choice}."
    )
    print(textwrap.fill(race.description, width=80))
    print("Kemampuan ras:")
    for ability in race.abilities:
        print(f"- {ability}")
    print(
        f"Stat awal -> Vitality: {player.vitality}, Finesse: {player.finesse}, Focus: {player.focus}, HP: {player.max_health}"
    )
    display_hud(player)
    return player


class GameSession:
    """Stateful loop that lets players explore the world with menu commands."""

    def __init__(
        self,
        player: Player,
        decider: DecisionProvider,
        data: GameData,
        rng: random.Random,
        max_rounds: int | None = None,
    ) -> None:
        self.player = player
        self.decider = decider
        self.data = data
        self.rng = rng
        self.max_rounds = max_rounds
        self.travel_count = 0
        self.locations = build_locations(data.world["locations"])
        self.quests = build_quests(data.quests)
        self.monsters = build_monsters(data.monsters)

    def run(self) -> None:
        while True:
            options = [
                "Lanjutkan perjalanan",
                "Lihat status tim",
                "Tampilkan informasi dunia",
                "Istirahat dan pulihkan diri",
                "Keluar petualangan",
            ]
            choice, note = self.decider.choose("Apa yang ingin Anda lakukan selanjutnya?", options)
            print(note)

            if choice.startswith("Lanjutkan"):
                if self.perform_travel_round():
                    self.travel_count += 1
                    if self.max_rounds is not None and self.travel_count >= self.max_rounds:
                        print("\nSimulasi otomatis telah mencapai batas ronde.")
                        break
            elif choice.startswith("Lihat status"):
                display_hud(self.player)
            elif choice.startswith("Tampilkan informasi dunia"):
                describe_world(self.data)
            elif choice.startswith("Istirahat"):
                self.rest()
            else:
                print("\nSampai jumpa pada petualangan berikutnya!")
                break

            if self.player.is_defeated:
                print("\nPetualangan berakhir lebih cepat dari yang diharapkan.")
                break

    def perform_travel_round(self) -> bool:
        round_number = self.travel_count + 1
        print_header(f"Ronde Perjalanan {round_number}")
        location_labels = [f"{loc.name} ({loc.region})" for loc in self.locations]
        location_labels.append("Batalkan perjalanan")
        location_choice, note = self.decider.choose(
            "Ke mana Anda akan pergi?",
            location_labels,
        )
        print(note)
        if location_choice == "Batalkan perjalanan":
            print("Anda memutuskan menunda perjalanan dan tetap bersiaga.")
            return False

        selected_location = next(
            loc for loc in self.locations if f"{loc.name} ({loc.region})" == location_choice
        )

        self.player.set_location(selected_location.name, selected_location.region)
        self.player.advance_time(3)
        self.player.clear_temporary_buffs()

        print(f"\nAnda mencapai {selected_location.name}, {selected_location.description}")
        if selected_location.factions:
            print("Faksi berpengaruh: " + ", ".join(selected_location.factions))
        print("Rumor lokal: " + roll_event(selected_location, "rumor", self.rng))

        team_events = generate_team_events(selected_location, self.data.world, self.rng)
        for scale, description in team_events.items():
            print(f"{scale}: {description}")
            if scale == "Global":
                self.player.update_world_event(description)

        region_quests = quests_for_region(self.quests, selected_location.region)
        if not region_quests:
            print("Tidak ada quest utama di wilayah ini saat ini.")
            return True

        quest_options = [quest.name for quest in region_quests]
        quest_options.append("Lewati quest ini")
        quest_choice, note = self.decider.choose(
            "Quest mana yang ingin Anda tangani?",
            quest_options,
        )
        print(note)
        if quest_choice == "Lewati quest ini":
            print("Anda memilih untuk mengamati situasi tanpa campur tangan langsung.")
            self.player.set_active_quest(None)
            self.player.advance_time(1)
            display_hud(self.player)
            return True

        quest = next(q for q in region_quests if q.name == quest_choice)
        print(f"\n{quest.giver} menawarkan misi '{quest.name}'.")
        print(textwrap.fill(quest.summary, width=80))
        print("Langkah-langkah:")
        print(format_objectives(quest.objectives))

        self.player.set_active_quest(quest.name)
        display_hud(self.player)

        monster = select_monster(self.monsters, quest.region, self.rng)
        print("\nAncaman utama yang menghadang:")
        print(describe_monster(monster))

        approach_options = [
            "Serangan Langsung (bonus damage)",
            "Diplomasi dan Perlindungan (pengurangan damage)",
            "Riset Arcana (bonus terhadap monster sihir)",
            "Strategi Kustom",
        ]
        approach_choice, note = self.decider.choose("Bagaimana pendekatan tim Anda?", approach_options)
        print(note)
        attack_bonus = 0
        defense_bonus = 0
        if approach_choice.startswith("Serangan Langsung"):
            attack_bonus = 2
            self.player.add_buff("Momentum Serangan (sementara)")
        elif approach_choice.startswith("Diplomasi"):
            defense_bonus = 2
            self.player.add_buff("Aura Kedamaian (sementara)")
            for faction in selected_location.factions:
                self.player.adjust_reputation(faction, 1)
        elif approach_choice.startswith("Riset Arcana"):
            attack_bonus = 1
            defense_bonus = 1
            self.player.add_buff("Runic Insight (sementara)")
            self.player.add_skill("Analisis ley cepat")
        else:
            custom_plan = self.decider.ask_text(
                "Jelaskan strategi kustom tim Anda:", default="Manuver ley adaptif"
            )
            self.player.add_buff(f"Strategi: {custom_plan} (sementara)")
            if "perdagangan" in custom_plan.lower():
                self.player.gain_gold(10)
            attack_bonus = 1

        combat_log = resolve_combat(
            self.player,
            monster,
            self.rng,
            attack_bonus=attack_bonus,
            defense_bonus=defense_bonus,
        )
        print("\nHasil pertempuran:")
        for entry in combat_log.rounds:
            print("- " + entry)
        if combat_log.player_won:
            print(f"\n{self.player.name} menang! HP tersisa {combat_log.remaining_health}.")
            apply_rewards(self.player, quest)
            self.player.set_active_quest(None)
            print(
                "Pengalaman total: "
                f"{self.player.xp} | Inventaris: "
                f"{', '.join(self.player.inventory) if self.player.inventory else 'Kosong'}"
            )
        else:
            print(
                f"\n{self.player.name} tumbang! Anda terpaksa mundur dan memulihkan diri di Arkhaven."
            )
            self.player.heal_to_full()

        self.player.advance_time(3)
        display_hud(self.player)
        return True

    def rest(self) -> None:
        print("\nTim mengambil waktu untuk beristirahat dan memulihkan energi.")
        self.player.heal_to_full()
        self.player.advance_time(6)
        self.player.clear_temporary_buffs()
        self.player.add_buff("Kesiapan Baru (sementara)")
        display_hud(self.player)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Petualangan teks Mana Hearth")
    parser.add_argument("--seed", type=int, help="Seed RNG untuk determinisme.")
    parser.add_argument("--auto", action="store_true", help="Gunakan mode otomatis untuk demo cepat.")
    parser.add_argument(
        "--script",
        nargs="*",
        help="Urutan pilihan untuk mode otomatis (misal: 1 0 2).",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Jumlah ronde perjalanan untuk mode otomatis.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    rng = random.Random(args.seed)
    data = GameData.load()

    decider: DecisionProvider
    if args.auto:
        decider = AutoDecisionProvider(args.script)
    else:
        decider = InteractiveDecisionProvider()

    describe_world(data)
    player = create_player(decider, data, rng)

    session = GameSession(
        player,
        decider,
        data,
        rng,
        max_rounds=args.rounds if args.auto else None,
    )
    session.run()

    print("\nTerima kasih telah menjelajah Mana Hearth!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
