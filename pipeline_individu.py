#!/usr/bin/env python3
"""INDIVIDU pipeline: survey + BIP -> template-formatted records."""

import os

from survey_loader import load_individu_survey
from utils import (
    clean_id, to_upper, to_int, normalize_jk, parse_date,
    calculate_age, clean_phone, clean_email, clean_income,
    clean_health_value, normalize_jamkes, normalize_yes_no,
    normalize_pendidikan, derive_pendidikan_years, is_sentinel,
)


def process_individu(survey_files, bip_by_nik, logger):
    """Process INDIVIDU survey files into template-formatted records.

    For each survey respondent, looks up their NIK in the BIP pool to
    fill demographic gaps. Removes duplicate NIKs, normalizes values,
    and sorts by KK (A-Z) with empty KK/NIK at bottom.

    Returns:
        List of output record dicts keyed by template column name.
    """
    all_survey = []
    for fpath in survey_files:
        fname = os.path.basename(fpath)
        records = load_individu_survey(fpath)
        logger.log("SURVEY_LOAD", "INFO",
                   f"Loaded {len(records)} records from {fname}")
        all_survey.extend(records)

    seen_nik = set()
    deduped = []
    no_nik_rows = []

    for rec in all_survey:
        nik = clean_id(rec.get("NIK"))

        if not nik:
            rec["NIK"] = ""
            no_nik_rows.append(rec)
            continue

        if nik in seen_nik:
            logger.log("DUPLICATE_NIK", "WARNING",
                       f"NIK {nik} appears in multiple survey responses; "
                       f"removing duplicate (keeping first)",
                       nik=nik,
                       nama=str(rec.get("Nama", "")).strip())
            continue

        seen_nik.add(nik)
        rec["NIK"] = nik
        deduped.append(rec)

    all_records = deduped + no_nik_rows

    output_records = []
    for rec in all_records:
        nik = rec["NIK"]
        nama = to_upper(rec.get("Nama")) or ""

        bip = bip_by_nik.get(nik) if nik else None
        if nik and not bip:
            logger.log("BIP_NOT_FOUND", "INFO",
                       f"NIK {nik} not found in BIP (possible newborn/recent migrant)",
                       nik=nik, nama=nama)

        out = {}

        if bip and bip.get("NO KK"):
            out["KK"] = bip["NO KK"]
        else:
            out["KK"] = ""

        out["NIK"] = nik
        out["Gelar awal"] = "-"
        out["Nama"] = nama
        out["Gelar akhir"] = "-"

        if bip:
            out["Jenis kelamin"] = normalize_jk(bip.get("JK"))
        else:
            out["Jenis kelamin"] = None

        if bip:
            out["Tempat lahir"] = to_upper(bip.get("TEMPAT LAHIR"))
        else:
            out["Tempat lahir"] = None

        if bip:
            birth_date = parse_date(bip.get("TANGGAL LAHIR"))
            out["Tanggal_lahir"] = birth_date
            out["Usia"] = calculate_age(birth_date)
        else:
            out["Tanggal_lahir"] = None
            out["Usia"] = None

        status_survey = to_upper(rec.get("Status"))
        if status_survey:
            out["Status"] = status_survey
        elif bip:
            out["Status"] = to_upper(bip.get("STATUS"))
        else:
            out["Status"] = None

        out["Usia Saat pertama kali menikah"] = to_int(rec.get("Usia Pertama Kali Menikah"))

        if bip:
            out["Agama"] = to_upper(bip.get("AGAMA"))
        else:
            out["Agama"] = None

        out["Suku Bangsa"] = "JAWA"
        out["Warga Negara"] = "INDONESIA"

        phone_raw = rec.get("Nomor HP/Wa")
        phone = clean_phone(phone_raw)
        if phone_raw is not None and is_sentinel(phone_raw):
            logger.log("SENTINEL_PHONE", "INFO",
                       f"Phone field had sentinel value {repr(phone_raw)}; "
                       f"treated as empty",
                       nik=nik, nama=nama)
        out["No. Hp"] = phone
        out["No. Wa"] = phone

        email_raw = rec.get("Email")
        email = clean_email(email_raw)
        if email_raw is not None and is_sentinel(email_raw):
            logger.log("SENTINEL_EMAIL", "INFO",
                       f"Email field had sentinel value {repr(email_raw)}; "
                       f"treated as empty",
                       nik=nik, nama=nama)
        out["Email"] = email

        out["Facebook"] = "-"
        out["Twitter"] = "-"
        out["Instagram"] = "-"

        out["Kondisi pekerjaan"] = to_upper(rec.get("Kondisi Pekerjaan"))
        out["Pekerjaan Utama"] = to_upper(rec.get("Pekerjaan Saat Ini"))

        jamkes_val = normalize_jamkes(rec.get("Jamkes ?"))
        out["Jaminan Sosial Ketenagakerjaan"] = jamkes_val if jamkes_val else "-"

        penghasilan_raw = rec.get("Penghasilan Setahun Terahir")
        penghasilan = clean_income(penghasilan_raw)
        if penghasilan_raw is not None and is_sentinel(penghasilan_raw):
            logger.log("SENTINEL_INCOME", "INFO",
                       f"Income field had sentinel value {repr(penghasilan_raw)}; "
                       f"treated as empty (no income)",
                       nik=nik, nama=nama)
        elif penghasilan and penghasilan < 1000:
            logger.log("LOW_INCOME", "INFO",
                       f"Annual income {penghasilan} is suspiciously low for NIK {nik}",
                       nik=nik, nama=nama)
        out["Penghasilan Setahun Terakhir"] = penghasilan
        out["SUMBER PENGHASILAN"] = to_upper(rec.get("Pekerjaan Saat Ini"))
        out["JUMLAH ASET DARI SUMBER PENGHASILAN"] = "-"
        out["SATUAN"] = "-"
        out["PENGHASILAN SETAHUN"] = penghasilan
        out["DI EKSPOR"] = "TIDAK"

        if penghasilan and penghasilan > 1000000000:
            logger.log("SUSPICIOUS_INCOME", "WARNING",
                       f"Annual income {penghasilan:,} seems unusually high for NIK {nik}",
                       nik=nik, nama=nama)

        out["PENYAKIT YANG DIDERITA SETAHUN TERAKHIR"] = to_upper(
            rec.get("Penyakit Yang Diderita Setahun Terahir"))

        out["RUMAH SAKIT"] = clean_health_value(
            rec.get("Akses Kesehatan [RUMAH SAKIT]"))
        out["RUMAH SAKIT BERSALIN"] = 0
        out["PUSKESMAS DENGAN RAWAT INAP"] = clean_health_value(
            rec.get("Akses Kesehatan [PUKESMAS DENGAN RAWAT INAP]"))
        out["PUSKESMAS TANPA RAWAT INAP"] = 0
        out["PUSKEMAS PEMBANTU"] = 0
        out["POLIKLINIK"] = 0
        out["TEMPAT PRAKTEK DOKTER"] = clean_health_value(
            rec.get("Akses Kesehatan [TEMPAT PRAKTEK DOKTER]"))
        out["RUMAH BERSALIN"] = 0
        out["TEMPAT PRAKTEK BIDAN"] = clean_health_value(
            rec.get("Akses Kesehatan [TEMPAT PRAKTEK BIDAN]"))
        out["POSKESDES"] = 0
        out["POLINDES"] = 0
        out["APOTIK"] = clean_health_value(
            rec.get("Akses Kesehatan [APOTEK]"))
        out["TOKO KHUSUS OBAT / JAMU"] = 0
        out["POSYANDU"] = clean_health_value(
            rec.get("Akses Kesehatan [POSYANDU ILP]"))
        out["POSBINDU"] = 0
        out["TEMPAT PRAKTIK DUKUN BAYI / BERSALIN"] = 0

        out["JAMKES"] = jamkes_val

        out["BAYI Usia 1-6 bulan Konsumsi ASI"] = normalize_yes_no(
            rec.get("Bayi Usia 1 - 6 Bulan Konsumsi Asi"))

        out["JENIS DISABILITAS"] = to_upper(rec.get("Disabilitas ?"))

        pendidikan = normalize_pendidikan(rec.get("Pendidikan ?"))
        if not pendidikan and bip:
            pendidikan = normalize_pendidikan(bip.get("PENDIDIKAN"))
        out["Pendidikan Tertinggi"] = pendidikan

        pendidikan_years = derive_pendidikan_years(pendidikan)
        out["Berapa Tahun mengenyam pendidikan dasar (SD,SMP,SMA)"] = (
            pendidikan_years if pendidikan_years is not None else 0)
        out["Pendidikan yang sedang di ikuti"] = "-"

        out["Bahasa yang digunakan di Rumah dan Pemukiman"] = "JAWA"
        out["Bahasa yang digunakan di Lembaga Formal"] = "INDONESIA"

        out["Jumlah kerja bakti 1 tahun terakhir"] = "-"
        out["Siskamling 1 tahun terakhir"] = "-"
        out["Pesta Rakyat (Adat) 1 tahun terakhir"] = "-"
        out["Frekuensi Melayat 1 tahun terakhir"] = "-"
        out["Frekuensi besuk orang sakit 1 tahun terakhir"] = "-"
        out["Frekuensi menolong kecelakaan 1 tahun terakhir"] = "-"

        out["Mendapatkan Pelayanan Desa 1 tahun terakhir"] = normalize_yes_no(
            rec.get("Mendapat Pelayanan Desa 1 Tahun Terahir ?"))
        out["Bagaimana pelayanan desa yang diperoleh?"] = "-"
        out["Pernah menyampaikan masukan/saran kepada pihak Desa?"] = "-"
        out["Bagaimana keterbukaan desa terhadap masukan?"] = "-"

        out["Terjadi Bencana 1 tahun terakhir"] = "-"
        out["Apakah anda terkena dampak bencana"] = "-"
        out["Apakah menerima pemenuhan Kebutuhan Dasar saat Bencana (makanan,pakaian, tempat tinggal)?"] = "-"
        out["Apakah ada penanganan psikososial keluarga terdampak bencana (penyuluhan/konseling/terapi)?"] = "-"

        out["_nik"] = nik
        out["_kk"] = out["KK"]
        output_records.append(out)

    def sort_key(r):
        kk = r.get("_kk", "")
        nik = r.get("_nik", "")
        has_kk = bool(kk)
        has_nik = bool(nik)
        return (not has_nik, not has_kk, kk if has_kk else "zzz", nik if has_nik else "zzz")

    output_records.sort(key=sort_key)

    for idx, rec in enumerate(output_records, 1):
        rec["No"] = idx
        rec["Action"] = "-"

    return output_records

