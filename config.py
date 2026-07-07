#!/usr/bin/env python3
"""Configuration constants and column type rules."""

import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BAHAN_DIR = os.path.join(BASE_DIR, "BAHAN")
BIP_DIR = os.path.join(BASE_DIR, "BIP")
TEMPLATES_DIR = os.path.join(BASE_DIR, "TEMPLATES")
OUTPUT_DIR = os.path.join(BASE_DIR, "OUTPUT")

TEMPLATE_INDIVIDU = os.path.join(TEMPLATES_DIR, "TEMPLATE_DATA_INDIVIDU.xlsx")
TEMPLATE_KELUARGA = os.path.join(TEMPLATES_DIR, "TEMPLATE_DATA_KELUARGA.xlsx")

OUTPUT_ISSUES = os.path.join(OUTPUT_DIR, "DATA_ISSUES.xlsx")

TODAY = datetime.date.today()

BIP_HEADERS = [
    "NO", "NO KK", "NAMA LENGKAP", "NIK", "JK",
    "TEMPAT LAHIR", "TANGGAL LAHIR", "GOL. DRH", "AGAMA",
    "STATUS", "SHDK", "PENDIDIKAN", "PEKERJAAN",
    "NAMA IBU", "NAMA AYAH", "ALAMAT", "NO RT", "NO RW",
]

TEXT_COLUMNS_INDIVIDU = {"KK", "NIK", "No. Hp", "No. Wa", "Email"}
DATE_COLUMNS_INDIVIDU = {"Tanggal_lahir"}
INT_COLUMNS_INDIVIDU = {
    "No", "Usia", "Usia Saat pertama kali menikah",
    "Berapa Tahun mengenyam pendidikan dasar (SD,SMP,SMA)",
    "RUMAH SAKIT BERSALIN",
    "PUSKESMAS TANPA RAWAT INAP",
    "PUSKEMAS PEMBANTU", "POLIKLINIK",
    "RUMAH BERSALIN", "POSKESDES", "POLINDES",
    "TOKO KHUSUS OBAT / JAMU", "POSBINDU",
    "TEMPAT PRAKTIK DUKUN BAYI / BERSALIN",
}
NUM_COLUMNS_INDIVIDU = {
    "Penghasilan Setahun Terakhir", "PENGHASILAN SETAHUN",
}

TEXT_COLUMNS_KELUARGA = {"NO KK", "NIK", "NO. HP", "NO. Telpon Rumah", "NIK Kepala Keluarga"}
NUM_COLUMNS_KELUARGA = {
    "LUAS LANTAI TEMPAT TINGGAL (m2)",
    "LUAS TANAH TEMPAT TINGGAL (m2)",
    "RATA-RATA PENGELUARAN / BULAN (Rp)",
}

PENDIDIKAN_YEARS = {
    "SD / SEDERAJAT": 6,
    "SLTP / SEDERAJAT": 9,
    "SLTA / SEDERAJAT": 12,
    "DIPLOMA I - III": 13,
    "DIPLOMA IV / S-1 / SEDERAJAT": 16,
    "S-1 / SEDERAJAT": 16,
    "S-2 / SEDERAJAT": 18,
    "S-3 / SEDERAJAT": 21,
}
