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

Pastikan modul dapat ditemukan dengan menambahkan direktori `src` ke
`PYTHONPATH` atau memasang paket secara editable.

```bash
PYTHONPATH=src python -m worldbuilding_game.game
```

Perintah di atas menjalankan mode interaktif dengan menu komando. Setelah
menciptakan karakter Anda dapat memilih aksi berikut kapan pun:

- **Lanjutkan perjalanan** untuk memilih tujuan, menyimak peristiwa lokal hingga
  global, serta menyelesaikan quest yang tersedia.
- **Lihat status tim** guna menampilkan HUD lengkap.
- **Tampilkan informasi dunia** untuk membaca ringkasan lore tanpa meninggalkan
  sesi permainan.
- **Istirahat dan pulihkan diri** yang memulihkan HP dan mengganti buff
  sementara sebelum aksi berikutnya.
- **Keluar petualangan** jika ingin mengakhiri sesi.

Untuk demo otomatis (tanpa input) pakai:

```bash
PYTHONPATH=src python -m worldbuilding_game.game --auto --seed 42 --rounds 2
```

Anda juga dapat menyediakan skrip pilihan:

```bash
PYTHONPATH=src python -m worldbuilding_game.game --auto --script 0 1 2 1
```

Setiap angka merepresentasikan indeks pilihan yang diambil secara berurutan.

## Struktur

- `src/worldbuilding_game/data/` menyimpan ringkasan JSON dari dokumen
  worldbuilding asli.
- `src/worldbuilding_game/entities.py` mendefinisikan model domain (ras,
  lokasi, quest, monster, dan pemain).
- `src/worldbuilding_game/rules.py` berisi logika permainan seperti generator
  peristiwa, pertempuran sederhana, dan pemberian hadiah.
- `src/worldbuilding_game/game.py` menyediakan antarmuka command line dengan
  mode interaktif dan otomatis.

## Pengujian

Gunakan `pytest` untuk menjalankan pengujian otomatis:

```bash
pytest
```
