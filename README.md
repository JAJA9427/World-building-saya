# Mana Hearth Narrative Adventure

Proyek ini mengubah dokumen worldbuilding menjadi sebuah permainan naratif teks
berbasis node. Pemain membuat karakter dari ras-ras utama dunia Mana Hearth,
menjelajah lokasi penting, menangani quest faksi, dan menghadapi monster
legendaris.

## Fitur Utama

- **HUD Tim Dinamis** — menampilkan nama, ras, rank, quest aktif, affinitas,
  reputasi, kondisi dunia, statistik inti, skill, buff, perlengkapan, inventaris,
  emas, serta penanda waktu setiap ronde.
- **Jelajah Multi-Skala** — setiap perjalanan memunculkan rangkaian peristiwa
  lokal, regional, dan global seperti embargo ekonomi, badai ley, atau konflik
  faksi yang memengaruhi strategi tim.
- **Pendekatan Quest Fleksibel** — pilih serangan langsung, diplomasi,
  riset arcana, atau tulis strategi kustom untuk memodifikasi hasil pertempuran
  dan hubungan faksi.

## Menjalankan Gim

Pasang dependensi secara editable agar entry point CLI tersedia:

```bash
python -m pip install -e .
```

### Mode interaktif

Mulai petualangan dengan perintah:

```bash
mana
# atau
python -m worldbuilding_game.game --interactive
```

Anda akan melalui fase pembuatan karakter dengan opsi menerima hasil roll,
reroll terbatas, kustomisasi nama/ras/peran, hingga memuat save lama. Di dalam
loop permainan gunakan perintah numerik `1/2/3/...` untuk memilih opsi yang
disarankan atau ketik perintah bebas. Daftar perintah utama:

```
help                Tampilkan ringkasan perintah
hud                 Lihat status tim lengkap
look                Pantau peristiwa lokal/regional/global
move <lokasi>       Bergerak (contoh: move Hutan Sylveth/Valmoria)
event               Picu encounter berbasis stat & kondisi
rest                Pulihkan HP dan buff sementara
inv / equip / use   Kelola inventaris dan perlengkapan
skills              Tampilkan daftar skill
quest list/take/turnin  Manajemen quest aktif
sim <n>             Simulasikan beberapa ronde otomatis
save [file] / load [file]
quit                Akhiri sesi
```

### Mode otomatis

Gunakan penentu pilihan otomatis dengan urutan menu numerik atau perintah bebas:

```bash
python -m worldbuilding_game.game --auto --seed 42 --rounds 3
python -m worldbuilding_game.game --auto --script 2 move Arkhaven/Valmoria rest
```

### Engine AI

Untuk simulasi panjang yang memilih aksi berdasarkan heuristik utilitas:

```bash
python -m worldbuilding_game.game --ai --ticks 300 --rate 8
python -m worldbuilding_game.game --ai --ticks -1 --rate 5 --headless --save-every 50
```

Mode AI akan menggunakan autosave sesuai interval dan dapat dijalankan tanpa
output (`--headless`).

### Simpan & Lanjutkan

Perintah `save` menulis state ke `save.json` (atau berkas pilihan), sedangkan
`load` memuat kembali state tersebut, termasuk posisi, inventaris, dan RNG.

## Struktur

- `src/worldbuilding_game/data/` menyimpan ringkasan JSON dari dokumen
  worldbuilding asli.
- `src/worldbuilding_game/entities.py` mendefinisikan model domain (ras,
  lokasi, quest, monster, dan pemain).
- `src/worldbuilding_game/rules.py` berisi generator peristiwa dan resolusi
  pertempuran klasik.
- `src/worldbuilding_game/cli.py` menjalankan menu interaktif, parser perintah,
  serta integrasi mode otomatis dan AI.
- `src/worldbuilding_game/ai/` memuat engine dan policy utilitas untuk
  simulasi tanpa input pemain.
- `src/worldbuilding_game/systems/` berisi modul aksi, karakter, resolusi
  skill check, dan helper penyimpanan game.

## Pengujian

Gunakan `pytest` untuk menjalankan pengujian otomatis:

```bash
pytest
```
