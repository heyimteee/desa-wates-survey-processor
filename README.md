# Desa Wates — Alat Pemroses Data Survei

Program ini mengolah data survei Desa Wates (INDIVIDU + KELUARGA) dengan bantuan data BIP (kependudukan) untuk mengisi data yang kosong, lalu menghasilkan file Excel sesuai template per kelompok RT/RW/Dusun.

## Prasyarat

- Python 3.8+
- `openpyxl` (install: `pip install openpyxl`)

## Cara Penggunaan

1. **Buat folder `BAHAN/`** — masukkan file survei (Excel) ke folder ini. Program akan mencari secara otomatis file yang mengandung kata `INDIVIDU` atau `Keluarga` di namanya. Boleh diorganisir dalam subfolder.

2. **Buat folder `BIP/`** — masukkan file data kependudukan (Excel) ke folder ini. Program akan membaca semua file `.xlsx` (kecuali file sementara `~$`) dan mengindeksnya berdasarkan NIK dan KK. File BIP harus memiliki baris header yang diawali dengan `NO` (terdeteksi otomatis di baris 1 atau 3).

3. **Folder `TEMPLATES/`** — harus berisi dua file template:
   - `TEMPLATE_DATA_INDIVIDU.xlsx` — template 70 kolom untuk output per individu
   - `TEMPLATE_DATA_KELUARGA.xlsx` — template 135 kolom untuk output per keluarga

4. **Jalankan:**
   ```bash
   python3 process.py
   ```

5. **Hasil** — file `.xlsx` akan muncul di folder `OUTPUT/`, diberi nama sesuai lokasi:
   ```
   DATA_INDIVIDU_RT_01_RW_01_DUSUN_SIDOMULYO_DESA_WATES.xlsx
   DATA_KELUARGA_RT_01_RW_05_DUSUN_WATES_DESA_WATES.xlsx
   ```

   File `DATA_ISSUES.xlsx` mencatat peringatan kualitas data.

## Cara Kerja

1. **Pemuatan BIP** — membaca semua file kependudukan, menghapus NIK ganda, mengindeks berdasarkan NIK dan KK.
2. **Penemuan survei** — mencari file survei INDIVIDU dan KELUARGA di folder `BAHAN/`.
3. **Proses INDIVIDU** — mencocokkan NIK responden dengan data BIP untuk mengisi data kosong (nama, jenis kelamin, tempat lahir, tanggal lahir, usia, agama, KK). Data survei diutamakan; BIP sebagai cadangan.
4. **Proses KELUARGA** — untuk setiap KK yang disurvei, program mengambil seluruh anggota keluarga dari BIP dan melampirkan data rumah tangga (perumahan, fasilitas, program bantuan) ke setiap individu.
5. **Output** — menulis satu file per input survei, dengan tipe kolom yang benar (TEXT untuk NIK/KK, DATE untuk tanggal lahir, NUMBER untuk uang, dll).

## Aturan Data

- Survei adalah data utama; BIP hanya mengisi celah.
- NIK/KK ganda: hanya yang pertama disimpan.
- Semua teks menggunakan HURUF BESAR, kecuali alamat email.
- NIK, KK, nomor HP disimpan sebagai tipe TEXT.
- Kolom teks kosong → `-` (strip). Kolom angka kosong → `0`.
- Isian default: Suku Bangsa → JAWA, Warga Negara → INDONESIA, DI EKSPOR → TIDAK.
- Urutan: KK A→Z, lalu KK kosong, lalu NIK kosong di bagian paling bawah.
