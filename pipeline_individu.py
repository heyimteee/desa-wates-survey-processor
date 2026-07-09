#!/usr/bin/env python3
"""INDIVIDU pipeline: survey + BIP -> template-formatted records."""

import os

from survey_loader import load_individu_survey, parse_survey_filename
from utils import (
    clean_id, to_upper, to_int, normalize_jk, parse_date,
    calculate_age, clean_and_validate_phone, clean_email, clean_income,
    clean_health_value, normalize_jamkes, normalize_yes_no,
    normalize_pendidikan, derive_pendidikan_years, is_sentinel,
    is_valid_nik, repair_nik_by_name, classify_nik_duplicate,
    detect_health_anomaly, name_key,
)


def process_individu(survey_files, bip_by_nik, bip_by_name, logger):
    """Process INDIVIDU survey files into template-formatted records.

    For each survey respondent, looks up their NIK in the BIP pool to
    fill demographic gaps. Repairs invalid NIKs by name matching scoped
    to RT/RW. Handles duplicate NIKs with classification into safe
    auto-dedup vs manual review.

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

    # ==================================================================
    # Phase A: NIK validation and repair
    # ==================================================================
    all_valid_nik = []
    no_nik_rows = []

    for rec in all_survey:
        nik = clean_id(rec.get("NIK"))
        rec.setdefault("_validation_notes", [])
        rec.setdefault("_sort_priority", 0)
        rec.setdefault("_nik_category", "")

        filename = rec.get("_source_file", "")
        info = parse_survey_filename(filename)
        rt = info.get("rt")
        rw = info.get("rw")

        repaired, note = repair_nik_by_name(
            nik, to_upper(rec.get("Nama")), rt, rw, bip_by_name, logger)

        if repaired and repaired != nik:
            rec["_original_nik"] = nik
            rec["_nik_repaired"] = True
            rec["_validation_notes"].append("NIK: " + note)
            nik = repaired

        if not is_valid_nik(nik):
            rec["NIK"] = ""
            rec["_sort_priority"] = 3 if not nik else 2
            if nik:
                rec["_nik_category"] = "NIK TIDAK VALID"
                rec["_validation_notes"].append(
                    "NIK tidak valid ({} digit)".format(len(str(nik))))
            else:
                rec["_nik_category"] = "NIK KOSONG"
                rec["_validation_notes"].append("NIK kosong")
            no_nik_rows.append(rec)
            continue

        rec["NIK"] = nik
        all_valid_nik.append(rec)

    # ==================================================================
    # Phase B: Smart NIK deduplication
    # ==================================================================
    kept = []
    perlu_dicek = []
    seen_nik = {}

    for rec in all_valid_nik:
        nik = rec["NIK"]
        nama = to_upper(rec.get("Nama")) or ""

        if nik not in seen_nik:
            seen_nik[nik] = (rec, nama)
            kept.append(rec)
            continue

        other_rec, other_name = seen_nik[nik]

        if name_key(nama) == name_key(other_name):
            logger.log("DUPLICATE_NIK_SAFE", "INFO",
                       "NIK {} duplicate — same name '{}', auto-dedup (keeping first)".format(
                           nik, nama),
                       nik=nik, nama=nama)
            continue

        result = classify_nik_duplicate(nik, other_name, nama, bip_by_nik)

        if result in ("same", "a_owns"):
            rec["_nik_category"] = "PERLU DICEK"
            rec["_sort_priority"] = 1
            rec["_validation_notes"].append(
                "NIK duplikat: nama berbeda dengan BIP")
            perlu_dicek.append(rec)
        elif result == "b_owns":
            other_rec["_nik_category"] = "PERLU DICEK"
            other_rec["_sort_priority"] = 1
            other_rec["_validation_notes"].append(
                "NIK duplikat: nama berbeda dengan BIP")
            kept.remove(other_rec)
            perlu_dicek.append(other_rec)
            seen_nik[nik] = (rec, nama)
            kept.append(rec)
        else:
            rec["_nik_category"] = "PERLU DICEK"
            rec["_sort_priority"] = 1
            rec["_validation_notes"].append(
                "NIK duplikat: nama berbeda, NIK tidak di BIP")
            perlu_dicek.append(rec)

    all_records = kept + no_nik_rows + perlu_dicek

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
        phone, phone_note = clean_and_validate_phone(phone_raw)
        if phone_note:
            rec["_validation_notes"].append(f"HP: {phone_note}")
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

        pekerjaan_survey = to_upper(rec.get("Pekerjaan Saat Ini"))
        pekerjaan_bip = to_upper(bip.get("PEKERJAAN")) if bip else None
        pekerjaan = pekerjaan_survey or pekerjaan_bip
        if not pekerjaan:
            pekerjaan = "TIDAK BEKERJA"
            rec["_validation_notes"].append("Pekerjaan kosong, diisi TIDAK BEKERJA")
        out["Pekerjaan Utama"] = pekerjaan

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
        out["SUMBER PENGHASILAN"] = to_upper(pekerjaan)
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

        health_facilities = [
            ("Akses Kesehatan [RUMAH SAKIT]", "RUMAH SAKIT"),
            ("Akses Kesehatan [PUKESMAS DENGAN RAWAT INAP]", "PUSKESMAS DENGAN RAWAT INAP"),
            ("Akses Kesehatan [TEMPAT PRAKTEK DOKTER]", "TEMPAT PRAKTEK DOKTER"),
            ("Akses Kesehatan [TEMPAT PRAKTEK BIDAN]", "TEMPAT PRAKTEK BIDAN"),
            ("Akses Kesehatan [APOTEK]", "APOTIK"),
            ("Akses Kesehatan [POSYANDU ILP]", "POSYANDU"),
        ]

        for survey_col, output_col in health_facilities:
            raw_val = rec.get(survey_col)
            cleaned = clean_health_value(raw_val)
            is_anom, atype, msg = detect_health_anomaly(raw_val)
            if is_anom:
                rec["_validation_notes"].append("{}: {}".format(output_col, msg))
            out[output_col] = cleaned

        out["RUMAH SAKIT BERSALIN"] = 0
        out["PUSKESMAS TANPA RAWAT INAP"] = 0
        out["PUSKEMAS PEMBANTU"] = 0
        out["POLIKLINIK"] = 0
        out["RUMAH BERSALIN"] = 0
        out["POSKESDES"] = 0
        out["POLINDES"] = 0
        out["TOKO KHUSUS OBAT / JAMU"] = 0
        out["POSBINDU"] = 0
        out["TEMPAT PRAKTIK DUKUN BAYI / BERSALIN"] = 0

        out["JAMKES"] = jamkes_val

        out["BAYI Usia 1-6 bulan Konsumsi ASI"] = normalize_yes_no(
            rec.get("Bayi Usia 1 - 6 Bulan Konsumsi Asi"))

        out["JENIS DISABILITAS"] = to_upper(rec.get("Disabilitas ?"))

        pendidikan = normalize_pendidikan(rec.get("Pendidikan ?"))
        if not pendidikan and bip:
            pendidikan = normalize_pendidikan(bip.get("PENDIDIKAN"))
        if not pendidikan:
            pendidikan = "TIDAK / BELUM SEKOLAH"
            rec["_validation_notes"].append(
                "Pendidikan kosong, diisi TIDAK/BELUM SEKOLAH")
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
        out["_validation_notes"] = rec.get("_validation_notes", [])
        out["_nik_category"] = rec.get("_nik_category", "")
        out["_sort_priority"] = rec.get("_sort_priority", 0)
        output_records.append(out)

    def sort_key(r):
        priority = r.get("_sort_priority", 0)
        kk = r.get("_kk", "") or "zzz"
        return (priority, kk)

    output_records.sort(key=sort_key)

    for idx, rec in enumerate(output_records, 1):
        rec["No"] = idx
        category = rec.get("_nik_category", "")
        notes = rec.get("_validation_notes", [])
        if category == "PERLU DICEK":
            rec["Action"] = "Cek Manual"
        elif category == "NIK TIDAK VALID":
            rec["Action"] = "Perbaiki"
        elif category == "NIK KOSONG":
            rec["Action"] = "Lengkapi"
        elif notes:
            rec["Action"] = "Periksa"
        else:
            rec["Action"] = "Auto"

    for rec in output_records:
        notes = rec.get("_validation_notes", [])
        category = rec.get("_nik_category", "")
        note_str = "; ".join(notes) if notes else "-"
        if notes or category:
            logger.log_validation(
                str(rec.get("No", "")),
                rec.get("KK", ""),
                rec.get("NIK", ""),
                rec.get("Nama", ""),
                category or "Data Valid",
                note_str,
            )

    return output_records

