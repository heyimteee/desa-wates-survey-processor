# Desa Wates Micro Data — Survey Processing Tool

Processes Desa Wates survey data (INDIVIDU + KELUARGA) using BIP civil registry data to fill demographic gaps, outputting template-formatted Excel files per RT/RW/Dusun group.

## Prerequisites

- Python 3.8+
- `openpyxl` (`pip install openpyxl`)

## Setup

1. **Create `BAHAN/`** — place survey Excel files here. The program recursively searches this folder for files containing `INDIVIDU` or `Keluarga` in the filename. Organize into subfolders as desired.

2. **Create `BIP/`** — place civil registry Excel files here. The program reads all `.xlsx` files (skipping `~$` temp files) and indexes them by NIK and KK. The BIP files should have a header row starting with `NO` (auto-detected as row 1 or row 3).

3. **`TEMPLATES/`** — must contain two template files:
   - `TEMPLATE_DATA_INDIVIDU.xlsx` — 70-column template for individual output
   - `TEMPLATE_DATA_KELUARGA.xlsx` — 135-column template for household output

4. **Run:**
   ```bash
   python3 process.py
   ```

5. **Output** — generated `.xlsx` files appear in `OUTPUT/`, named by location:
   ```
   DATA_INDIVIDU_RT_01_RW_01_DUSUN_SIDOMULYO_DESA_WATES.xlsx
   DATA_KELUARGA_RT_01_RW_05_DUSUN_WATES_DESA_WATES.xlsx
   ```

   A `DATA_ISSUES.xlsx` log records data quality warnings.

## How It Works

1. **BIP loading** — loads all civil registry files, deduplicates by NIK, indexes by NIK and KK.
2. **Survey discovery** — finds INDIVIDU and KELUARGA survey files in `BAHAN/`.
3. **INDIVIDU pipeline** — looks up each respondent's NIK in BIP to fill demographic gaps (name, gender, birthplace, birthdate, age, religion, KK). Survey data takes priority; BIP is fallback.
4. **KELUARGA pipeline** — for each surveyed KK, expands to all BIP family members of that KK, attaching the household survey data (housing, facilities, assistance programs) to each individual.
5. **Output** — writes one file per survey input, enforcing column types (TEXT for IDs, DATE for birthdates, NUMBER for currency, etc.).

## Data Rules

- Survey is primary; BIP fills gaps only.
- Duplicate NIKs/KKs: first occurrence kept.
- All text is UPPERCASE except email addresses.
- NIK, KK, phone stored as TEXT type.
- Empty text fields → `-` (dash). Empty numeric fields → `0`.
- Default fills: Suku Bangsa → JAWA, Warga Negara → INDONESIA, DI EKSPOR → TIDAK.
- Sort: KK A→Z, then empty KK, then empty NIK at bottom.
