# Desa Wates — Alat Pemroses Data Survei

Program ini mengolah data survei Desa Wates (INDIVIDU + KELUARGA) dengan bantuan data BIP (kependudukan) untuk mengisi data yang kosong, mendeteksi anomali, dan menghasilkan file Excel sesuai template per kelompok RT/RW/Dusun.

## Prasyarat

- Python 3.8+
- `openpyxl` (install: `pip install openpyxl`)
- Untuk menjalankan tes: `pip install pytest`

## Struktur Proyek

```
├── process.py              Entry point — jalankan program
├── config.py               Konfigurasi path, aturan kolom, konstanta
├── utils.py                Fungsi bantu: format, normalisasi, validasi
├── logger.py               Pencatat isu kualitas data
├── bip_loader.py           Pembaca file BIP (kependudukan)
├── survey_loader.py        Pembaca file survei (Google Forms)
├── pipeline_individu.py    Pipeline pemrosesan INDIVIDU
├── pipeline_keluarga.py    Pipeline pemrosesan KELUARGA
├── excel_writer.py         Penulis output Excel sesuai template
├── tests/                  Tes unit
│   ├── conftest.py         Fixtures bersama
│   ├── test_utils.py       131 tes — fungsi bantu
│   ├── test_pipeline_individu.py    14 tes — pipeline INDIVIDU
│   ├── test_pipeline_keluarga.py    22 tes — pipeline KELUARGA
│   ├── test_bip_loader.py           6 tes — pembacaan BIP
│   ├── test_survey_loader.py       11 tes — pembacaan survei
│   ├── test_logger.py               8 tes — pencatatan isu
│   └── test_excel_writer.py         6 tes — penulisan Excel
├── BAHAN/                  Folder untuk file survei (buat sendiri)
├── BIP/                    Folder untuk file BIP (buat sendiri)
├── TEMPLATES/              Template output Excel
│   ├── TEMPLATE_DATA_INDIVIDU.xlsx
│   └── TEMPLATE_DATA_KELUARGA.xlsx
└── OUTPUT/                 Folder hasil pemrosesan (dibuat otomatis)
```

## Cara Penggunaan

1. **Buat folder `BAHAN/`** — masukkan file survei (Excel) ke folder ini. Program akan mencari file yang mengandung kata `INDIVIDU` atau `Keluarga` di namanya (rekursif ke subfolder).

2. **Buat folder `BIP/`** — masukkan file data kependudukan (Excel). Program membaca semua file `.xlsx` (kecuali file sementara `~$`), mengindeks berdasarkan NIK dan KK.

3. **`TEMPLATES/`** — harus berisi dua file template:
   - `TEMPLATE_DATA_INDIVIDU.xlsx` — 70 kolom
   - `TEMPLATE_DATA_KELUARGA.xlsx` — 135 kolom

4. **Jalankan:**
   ```bash
   python3 process.py
   ```

5. **Hasil** — file `.xlsx` di `OUTPUT/`, diberi nama sesuai lokasi:
   ```
   DATA_INDIVIDU_RT_01_RW_01_DUSUN_SIDOMULYO_DESA_WATES.xlsx
   DATA_KELUARGA_RT_01_RW_05_DUSUN_WATES_DESA_WATES.xlsx
   ```

6. **Laporan kualitas data:**
   - `DATA_ISSUES.xlsx` → Sheet `DATA ISSUES`: daftar semua isu (peringatan, info)
   - `DATA_VALIDASI` → Sheet per-baris: No, KK, NIK, Nama, Kategori, Catatan

## Menjalankan Tes

```bash
python3 -m pytest tests/ -v
```

## Cara Kerja

1. **Pemuatan BIP** — membaca semua file kependudukan, mendeteksi baris header secara otomatis (baris 1 atau 3), menghapus NIK ganda, mengindeks berdasarkan NIK, KK, dan nama.
2. **Penemuan survei** — mencari file survei INDIVIDU dan KELUARGA di `BAHAN/`.
3. **Validasi & perbaikan NIK** — jika NIK tidak 16 digit, program mencoba memperbaiki dengan mencocokkan nama + RT/RW di BIP. Jika gagal, baris ditandai sebagai "NIK TIDAK VALID".
4. **Penanganan NIK ganda** — nama sama → otomatis hapus duplikat; nama beda → cek BIP, jika tidak cocok → tandai "PERLU DICEK" untuk review manual.
5. **Proses INDIVIDU** — mencocokkan NIK responden dengan data BIP untuk mengisi data kosong (KK, JK, tempat/tanggal lahir, usia, agama). Data survei diutamakan.
6. **Proses KELUARGA** — untuk setiap KK yang disurvei, ambil seluruh anggota keluarga dari BIP dan lampirkan data rumah tangga ke setiap individu.
7. **Output** — menulis satu file per input survei, dengan tipe kolom yang benar, kolom `Action` berisi rekomendasi (Auto/Periksa/Perbaiki/dll).

## Validasi & Deteksi Anomali

| Anomali | Deteksi | Tindakan |
|---|---|---|
| NIK tidak 16 digit | `is_valid_nik()` | Perbaiki otomatis jika nama+cocok RT/RW; jika gagal → NIK TIDAK VALID |
| NIK ganda nama sama | `classify_nik_duplicate()` | Hapus otomatis (INFO), simpan 1 |
| NIK ganda nama beda | `classify_nik_duplicate()` | Simpan kedua baris, tandai "PERLU DICEK" |
| No. HP +62... | Regex | Konversi ke 08... |
| No. HP aneh (koma, 1 digit, 05xx) | `clean_and_validate_phone()` | Ganti `-` / flag "tidak diawali 08" |
| Pendidikan kosong | Fallback BIP | Isi "TIDAK / BELUM SEKOLAH" |
| Pekerjaan kosong | Fallback BIP | Isi "TIDAK BEKERJA" |
| Kesehatan kontradiksi (TIDAK PERNAH,1) | `detect_health_anomaly()` | Flag "mixed" |
| Kesehatan multi-select (2,3) | `detect_health_anomaly()` | Flag "multi_numeric" |
| Jarak terlalu besar (>200km) | `_clean_distance()` | Ganti `-`, flag "ekstrem" |
| Waktu >12 jam | `_clean_time()` | Ganti `-`, flag "ekstrem" |
| Kecepatan tidak wajar (<1 km/jam) | `_clean_time()` | Ganti `-`, flag "kecepatan tidak wajar" |
| Jarak & waktu tertukar | `_detect_swapped()` | Flag "kemungkinan tertukar" |
| Jarak disamaratakan (semua 1) | Deteksi uniform | Flag "disamaratakan" |
| Row korup (KK=1, NIK=1, Nama=1.0) | `_is_corrupt_row()` | Hapus otomatis (WARNING) |
| NIK KK tidak 16 digit | `repair_nik_kk_from_bip()` | Perbaiki dari BIP (via SHDK) jika ada |
| KK tidak ditemukan di BIP | — | Flag, data survey tetap dioutput |
| Luas lantai >500m² | Integer check | Flag "kemungkinan Luas Tanah" |
| Bantuan "YA,TIDAK" | `normalize_bantuan()` | Normalisasi ke "YA" |
| Penghasilan >1M | Integer check | SUSPICIOUS_INCOME (WARNING) |
| Penghasilan <1000 | Integer check | LOW_INCOME (INFO) |

## Aturan Data

- Survei adalah data utama; BIP hanya mengisi celah.
- NIK/KK ganda: hanya yang pertama disimpan.
- Semua teks menggunakan HURUF BESAR, kecuali alamat email.
- NIK, KK, nomor HP disimpan sebagai tipe TEXT.
- Kolom teks kosong → `-` (strip). Kolom angka kosong → `0`.
- Jarak: input dalam meter → otomatis dikonversi ke kilometer.
- Waktu: input dalam menit → otomatis dikonversi ke jam.
- Isian default: Suku Bangsa → JAWA, Warga Negara → INDONESIA, DI EKSPOR → TIDAK.
- Urutan: KK A→Z, lalu PERLU DICEK, lalu NIK tidak valid, lalu NIK kosong.
- Kolom `Action`: Auto (valid), Periksa (ada catatan), Cek Manual (duplikat), Perbaiki (NIK invalid), Lengkapi (NIK kosong).
- Filter baris korup: KK=1, NIK KK=1, Nama="1.0" → dilewati otomatis.
