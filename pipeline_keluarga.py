#!/usr/bin/env python3
"""KELUARGA pipeline: survey + BIP -> template-formatted records."""

import os

from survey_loader import load_keluarga_survey
from utils import (
    clean_id, to_upper, to_int, to_text, normalize_yes_no,
    is_valid_nik, repair_nik_kk_from_bip, normalize_bantuan, name_key,
)


KELUARGA_SURVEY_MAP = {
    "Nomor KK": "NO KK",
    "Nomor NIK Kepala Keluarga": "NIK_KK_HEAD",
    "Nama": "NAMA Responden".upper(),
    "RT": "RT",
    "RW": "RW",
    "Tempat Tinggal Yang Ditempati": "TEMPAT TINGGAL YANG DITEMPATI",
    "Luas Tempat Tinggal ?": "LUAS LANTAI TEMPAT TINGGAL (m2)",
    "Jenis Lantai tempat tinggal": "JENIS LANTAI TEMPAT TINGGAL TERLUAS",
    "Jenis Dinding Rumah": "DINDING SEBAGIAN BESAR RUMAH",
    "Energi Untuk Memasak": "ENERGI UNTUK MEMASAK",
    "Fasilitas MCK": "FASILITAS MCK",
    "Sumber Air Mandi terbanyak": "SUMBER AIR MANDI TERBANYAK DARI",
    "Sumber Air Minum terbanyak": "SUMBER AIR MINUM TERBANYAK",
    "Jarak dari rumah ke PAUD": "PAUD_JARAK",
    "Waktu yang dibutuhkan dari rumah ke PAUD": "PAUD_WAKTU",
    "Jarak dari rumah ke TK/RA": "TK_JARAK",
    "Waktu yang dibutuhkan dari rumah ke TK/RA": "TK_WAKTU",
    "Jarak dari rumah ke SD/MI atau Sederajat": "SD_JARAK",
    "Waktu yang dibutuhkan dari rumah ke SD/MI atau Sederajat": "SD_WAKTU",
    "Jarak dari rumah ke SMP/MTs atau Sederajat": "SMP_JARAK",
    "Waktu yang dibutuhkan dari rumah ke SMP/MTs atau Sederajat": "SMP_WAKTU",
    "Jarak dari rumah ke SMA/MA atau Sederajat": "SMA_JARAK",
    "Waktu yang dibutuhkan dari rumah ke  SMA/MA atau Sederajat": "SMA_WAKTU",
    "Jarak dari rumah ke Perguruan Tinggi": "PT_JARAK",
    "Waktu yang dibutuhkan dari rumah ke Perguruan Tinggi": "PT_WAKTU",
    "Jarak dari rumah ke Rumah Sakit": "RS_JARAK",
    "Waktu yang dibutuhkan dari rumah ke Rumah Sakit": "RS_WAKTU",
    "Jarak dari rumah ke Rumah Bersalin": "RB_JARAK",
    "Waktu yang dibutuhkan dari rumah ke Rumah Bersalin": "RB_WAKTU",
    "Jarak dari rumah ke Pukesmas": "PUSKESMAS_JARAK",
    "Waktu yang dibutuhkan dari rumah ke Pukesmas": "PUSKESMAS_WAKTU",
    "Jarak dari rumah ke Posyandu": "POSYANDU_JARAK",
    "Waktu yang dibutuhkan dari rumah ke Posyandu": "POSYANDU_WAKTU",
    "Jarak dari rumah ke Apotek": "APOTIK_JARAK",
    "Waktu yang dibutuhkan dari rumah ke  Apotek": "APOTIK_WAKTU",
    "Pemanfaat/Penerima Program pemerintah [BLT]": "BLT",
    "Pemanfaat/Penerima Program pemerintah [PKH]": "PKH",
    "Pemanfaat/Penerima Program pemerintah [BPNT]": "BPNT",
    "Pemanfaat/Penerima Program pemerintah [BST]": "BST",
    "Pemanfaat/Penerima Program pemerintah [Sembako]": "SEMBAKO",
    "Pemanfaat/Penerima Program pemerintah [BSU]": "BSU",
    "Pemanfaat/Penerima Program pemerintah [Bantuan UMKM]": "BANTUAN_UMKM",
    "Pemanfaat/Penerima Program pemerintah [Bantuan Untuk Pekerja]": "BANTUAN_PEKERJA",
    "Pemanfaat/Penerima Program pemerintah [Bantuan untuk Pendidikan Anak]": "BANTUAN_ANAK",
    "Pemanfaat/Penerima Program pemerintah [Bantuan Lain dari Pemerintah ]": "BANTUAN_LAIN",
    "Rata rata pengeluaran satu keluarga dalam satu bulan": "RATA_RATA_PENGELUARAN",
}


DISTANCE_MAX_KM = 200


def _try_parse_numeric(val):
    """Try to parse a value as float, returning None if non-numeric."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def _clean_distance(raw_dist, raw_time, label):
    """Parse distance, detecting units from time/speed ratio.

    Strategy:
      - raw >= 100: assume meters → convert ÷1000
      - raw < 100: check speed. If meters→km gives absurd speed
        but keeping-as-km gives reasonable speed, use KM assumption.
    """
    val = _try_parse_numeric(raw_dist)
    if val is None:
        s = str(raw_dist).strip() if raw_dist else ""
        return s if s else "-", ""

    time_h = None
    t = _try_parse_numeric(raw_time)
    if t is not None and t > 0:
        time_h = t / 60.0

    km_m = val / 1000.0

    if time_h is None or time_h == 0:
        if km_m > DISTANCE_MAX_KM:
            return "-", f"{label}: ekstrem ({km_m:,.0f} km — kemungkinan salah input)"
        if km_m > 100:
            return km_m, f"{label}: jauh ({km_m:,.0f} km — periksa manual)"
        return km_m, ""

    if val >= 100:
        if km_m > DISTANCE_MAX_KM:
            return "-", f"{label}: ekstrem ({km_m:,.0f} km — kemungkinan salah input)"
        if km_m > 100:
            return km_m, f"{label}: jauh ({km_m:,.0f} km — periksa manual)"
        if km_m < 0.01:
            return km_m, f"{label}: sangat dekat ({km_m:.3f} km — periksa satuan)"
        return km_m, ""

    speed_m = km_m / time_h
    speed_km = val / time_h

    if speed_m >= 2.0:
        if km_m < 0.01:
            return km_m, f"{label}: sangat dekat ({km_m:.3f} km — periksa satuan)"
        return km_m, ""

    if 2.0 <= speed_km <= 80.0:
        return val, f"{label}: data kemungkinan sudah dalam KM"

    if speed_m < 2.0:
        return km_m, f"{label}: sangat dekat ({km_m:.3f} km — periksa satuan)"

    return km_m, ""


def _parse_time(val):
    """Parse time value, converting assumed minutes to hours."""
    if val is None:
        return "-"
    if isinstance(val, (int, float)):
        return val / 60.0
    s = str(val).strip()
    if s == "":
        return "-"
    try:
        return float(s.replace(",", ".")) / 60.0
    except ValueError:
        return s


TIME_MAX_JAM = 12
SPEED_MIN_KMH = 1.0


def _clean_time(km, jam, label):
    """Validate time value against distance. Returns (cleaned_jam, note)."""
    if not isinstance(jam, (int, float)):
        return jam, ""

    if jam > TIME_MAX_JAM:
        return "-", f"{label}: waktu ekstrem ({jam:,.0f} jam — kemungkinan salah input)"

    if isinstance(km, (int, float)) and km > 0 and jam > 0:
        speed = km / jam
        if speed < SPEED_MIN_KMH:
            return "-", f"{label}: kecepatan tidak wajar ({speed:.1f} km/jam)"

    return jam, ""


def _detect_swapped(km, jam, label):
    """Detect if distance and time appear to be swapped."""
    if not isinstance(km, (int, float)) or not isinstance(jam, (int, float)):
        return False, ""
    if km == 0 or jam == 0:
        return False, ""
    speed = km / jam
    if speed < 1 and jam > 0.5:
        swapped_speed = jam / km
        if 2 <= swapped_speed <= 80:
            return True, f"{label}: jarak & waktu kemungkinan tertukar"
    return False, ""


def _is_corrupt_row(survey_rec):
    """Check if a survey row is garbage/placeholder data."""
    kk = clean_id(survey_rec.get("Nomor KK"))
    nik_kk = clean_id(survey_rec.get("Nomor NIK Kepala Keluarga"))
    nama = str(survey_rec.get("Nama", "")).strip()
    return kk == "1" and nik_kk == "1" and nama in ("1", "1.0", "0", "0.0")


def _build_keluarga_record(member, survey_rec, logger):
    """Build a single KELUARGA output record from BIP member + survey data.

    Args:
        member: BIP record dict for this individual.
        survey_rec: Keluarga survey record dict for the household.
        logger: IssueLogger.

    Returns:
        Output record dict keyed by template column names.
    """
    out = {}

    out["NO KK"] = clean_id(member.get("NO KK"))
    out["NIK"] = clean_id(member.get("NIK"))
    out["NAMA"] = to_upper(member.get("NAMA LENGKAP"))
    out["ALAMAT"] = to_upper(member.get("ALAMAT"))

    out["NO. HP"] = "-"
    out["NO. Telpon Rumah"] = "-"
    out["NIK Kepala Keluarga"] = clean_id(survey_rec.get("Nomor NIK Kepala Keluarga"))

    out["TEMPAT TINGGAL YANG DITEMPATI"] = to_upper(
        survey_rec.get("Tempat Tinggal Yang Ditempati"))
    out["STATUS LAHAN"] = "-"

    luas = survey_rec.get("Luas Tempat Tinggal ?")
    luas_lantai = to_int(luas)
    if isinstance(luas_lantai, int) and luas_lantai > 500:
        survey_rec.setdefault("_notes", []).append(
            "Luas Lantai {} m2 mencurigakan — kemungkinan Luas Tanah".format(luas_lantai))
    out["LUAS LANTAI TEMPAT TINGGAL (m2)"] = luas_lantai
    out["LUAS TANAH TEMPAT TINGGAL (m2)"] = "-"

    out["JENIS LANTAI TEMPAT TINGGAL TERLUAS"] = to_upper(
        survey_rec.get("Jenis Lantai tempat tinggal"))
    out["DINDING SEBAGIAN BESAR RUMAH"] = to_upper(
        survey_rec.get("Jenis Dinding Rumah"))

    out["JENDELA"] = "-"
    out["ATAP"] = "-"
    out["PENERANGAN RUMAH"] = "-"

    out["ENERGI UNTUK MEMASAK"] = to_upper(survey_rec.get("Energi Untuk Memasak"))
    out["JIKA MENGGUNAKAN KAYU BAKAR, SUMBER KAYU BAKAR"] = "-"
    out["TEMPAT PEMBUANGAN SAMPAH"] = "-"

    out["FASILITAS MCK"] = to_upper(survey_rec.get("Fasilitas MCK"))
    out["SUMBER AIR MANDI TERBANYAK DARI"] = to_upper(
        survey_rec.get("Sumber Air Mandi terbanyak"))
    out["FASILITAS BUANG AIR BESAR"] = "-"
    out["SUMBER AIR MINUM TERBANYAK"] = to_upper(
        survey_rec.get("Sumber Air Minum terbanyak"))
    out["TEMPAT PEMBUANGAN AIR LIMBAH"] = "-"

    out["RUMAH DILEWATI SUTET"] = "-"
    out["RUMAH DIPANTARAN SUNGAI"] = "-"
    out["RUMAH DI LERENG GUNUNG / BUKIT"] = "-"
    out["KONDISI RUMAH KUMUH / TIDAK"] = "-"

    fasilitas_jw = [
        ("Jarak dari rumah ke PAUD", "Waktu yang dibutuhkan dari rumah ke PAUD",
         "PAUD - JARAK (KM)", "PAUD - WAKTU (JAM)", "PAUD - KEMUDAHAN", "PAUD"),
        ("Jarak dari rumah ke TK/RA", "Waktu yang dibutuhkan dari rumah ke TK/RA",
         "TK/RA - JARAK (KM)", "TK/RA - WAKTU (JAM)", "TK/RA - KEMUDAHAN", "TK"),
        ("Jarak dari rumah ke SD/MI atau Sederajat", "Waktu yang dibutuhkan dari rumah ke SD/MI atau Sederajat",
         "SD/MI - JARAK (KM)", "SD/MI - WAKTU (JAM)", "SD/MI - KEMUDAHAN", "SD"),
        ("Jarak dari rumah ke SMP/MTs atau Sederajat", "Waktu yang dibutuhkan dari rumah ke SMP/MTs atau Sederajat",
         "SMP/MTs - JARAK (KM)", "SMP/MTs - WAKTU (JAM)", "SMP/MTs - KEMUDAHAN", "SMP"),
        ("Jarak dari rumah ke SMA/MA atau Sederajat", "Waktu yang dibutuhkan dari rumah ke  SMA/MA atau Sederajat",
         "SMA/MA - JARAK (KM)", "SMA/MA - WAKTU (JAM)", "SMA/MA - KEMUDAHAN", "SMA"),
        ("Jarak dari rumah ke Perguruan Tinggi", "Waktu yang dibutuhkan dari rumah ke Perguruan Tinggi",
         "PERGURUAN TINGGI - JARAK (KM)", "PERGURUAN TINGGI - WAKTU (JAM)", "PERGURUAN TINGGI - KEMUDAHAN", "PT"),
        ("Jarak dari rumah ke Rumah Sakit", "Waktu yang dibutuhkan dari rumah ke Rumah Sakit",
         "RUMAH SAKIT - JARAK (KM)", "RUMAH SAKIT - WAKTU (JAM)", "RUMAH SAKIT - KEMUDAHAN", "RS"),
        ("Jarak dari rumah ke Rumah Bersalin", "Waktu yang dibutuhkan dari rumah ke Rumah Bersalin",
         "RS BERSALIN - JARAK (KM)", "RS BERSALIN - WAKTU (JAM)", "RS BERSALIN - KEMUDAHAN", "RB"),
        ("Jarak dari rumah ke Pukesmas", "Waktu yang dibutuhkan dari rumah ke Pukesmas",
         "PUSKESMAS - JARAK (KM)", "PUSKESMAS - WAKTU (JAM)", "PUSKESMAS - KEMUDAHAN", "PUSKESMAS"),
        ("Jarak dari rumah ke Posyandu", "Waktu yang dibutuhkan dari rumah ke Posyandu",
         "POSYANDU - JARAK (KM)", "POSYANDU - WAKTU (JAM)", "POSYANDU - KEMUDAHAN", "POSYANDU"),
        ("Jarak dari rumah ke Apotek", "Waktu yang dibutuhkan dari rumah ke  Apotek",
         "APOTIK - JARAK (KM)", "APOTIK - WAKTU (JAM)", "APOTIK - KEMUDAHAN", "APOTIK"),
    ]

    distances = []
    for jcol, tcol, jout, tout, kout, label in fasilitas_jw:
        raw_dist = survey_rec.get(jcol)
        raw_time = survey_rec.get(tcol)
        km, dist_note = _clean_distance(raw_dist, raw_time, label)
        jam_raw = _parse_time(raw_time)
        jam, time_note = _clean_time(
            km if isinstance(km, (int, float)) else None, jam_raw, label)
        out[jout] = km
        out[tout] = jam
        out[kout] = "-"

        if dist_note:
            survey_rec.setdefault("_notes", []).append(dist_note)
        if time_note:
            survey_rec.setdefault("_notes", []).append(time_note)
        if isinstance(km, (int, float)):
            distances.append(km)

        swapped, swap_note = _detect_swapped(km, jam, label)
        if swapped:
            survey_rec.setdefault("_notes", []).append(swap_note)

    uniform_ones = [d for d in distances if d == 0.001]
    if len(uniform_ones) >= 7:
        survey_rec.setdefault("_notes", []).append(
            "jarak disamaratakan (semua bernilai 1m)")

    out["PESANTREN - JARAK (KM)"] = "-"
    out["PESANTREN - WAKTU (JAM)"] = "-"
    out["PESANTREN - KEMUDAHAN"] = "-"

    out["SEMINARI - JARAK (KM)"] = "-"
    out["SEMINARI - WAKTU (JAM)"] = "-"
    out["SEMINARI - KEMUDAHAN"] = "-"

    out["PEND. KEAGAMAAN LAIN - JARAK (KM)"] = "-"
    out["PEND. KEAGAMAAN LAIN - WAKTU (JAM)"] = "-"
    out["PEND. KEAGAMAAN LAIN - KEMUDAHAN"] = "-"

    out["TOKO OBAT - JARAK (KM)"] = "-"
    out["TOKO OBAT - WAKTU (JAM)"] = "-"
    out["TOKO OBAT - KEMUDAHAN"] = "-"

    for prefix in ["DOKTER SPESIALIS", "DOKTER UMUM", "BIDAN",
                   "TENAGA KESEHATAN", "DUKUN"]:
        out[f"{prefix} - JARAK (KM)"] = "-"
        out[f"{prefix} - WAKTU (JAM)"] = "-"
        out[f"{prefix} - KEMUDAHAN"] = "-"

    for prefix in ["LOKASI PEKERJAAN", "LAHAN PERTANIAN", "SEKOLAH",
                   "BEROBAT", "BERIBADAH", "REKREASI"]:
        out[f"{prefix} - JENIS TRANS"] = "-"
        out[f"{prefix} - TRANS UMUM"] = "-"
        out[f"{prefix} - WAKTU (JAM)"] = "-"
        out[f"{prefix} - BIAYA (Rp)"] = "-"
        out[f"{prefix} - KEMUDAHAN"] = "-"

    out["TRANSPORT SEBELUMNYA"] = "-"
    out["TRANSPORT SEKARANG"] = "-"

    out["BLT"] = normalize_bantuan(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BLT]"))
    out["PKH"] = normalize_bantuan(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [PKH]"))
    out["BST"] = normalize_bantuan(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BST]"))
    out["BANTUAN PRESIDEN"] = normalize_bantuan(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BPNT]"))
    out["BANTUAN UMKM"] = normalize_bantuan(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan UMKM]"))

    bantuan_pekerja = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan Untuk Pekerja]")
    bsu = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BSU]")
    bp_val = normalize_bantuan(bantuan_pekerja)
    bsu_val = normalize_bantuan(bsu)
    if bp_val == "YA" or bsu_val == "YA":
        out["BANTUAN PEKERJA"] = "YA"
    else:
        out["BANTUAN PEKERJA"] = "TIDAK"

    out["BANTUAN ANAK"] = normalize_bantuan(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan untuk Pendidikan Anak]"))

    lainnya = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan Lain dari Pemerintah ]")
    sembako = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Sembako]")
    lain_val = normalize_bantuan(lainnya)
    sem_val = normalize_bantuan(sembako)
    if lain_val == "YA" or sem_val == "YA":
        out["LAINNYA"] = "YA"
    else:
        out["LAINNYA"] = "TIDAK"

    pengeluaran = survey_rec.get("Rata rata pengeluaran satu keluarga dalam satu bulan")
    out["RATA-RATA PENGELUARAN / BULAN (Rp)"] = to_text(pengeluaran)

    return out


def _build_keluarga_output(member, survey_rec, logger):
    """Build output and attach validation notes."""
    out = _build_keluarga_record(member, survey_rec, logger)
    notes = survey_rec.get("_notes", [])
    nikk_note = survey_rec.get("_nik_kk_note")
    if nikk_note:
        notes.append(nikk_note)
    kk_note = survey_rec.get("_kk_note")
    if kk_note:
        notes.append(kk_note)
    out["_notes"] = notes
    return out


def process_keluarga(survey_files, bip_by_kk, bip_all, logger):
    """Process KELUARGA survey files into template-formatted records.

    Expands household-level survey data to individual-level output:
    for each surveyed KK, finds all family members in BIP and attaches
    the household survey data to each member.

    Returns:
        List of output record dicts keyed by template column name.
    """
    all_survey = []
    for fpath in survey_files:
        fname = os.path.basename(fpath)
        records = load_keluarga_survey(fpath)
        logger.log("SURVEY_LOAD", "INFO",
                   f"Loaded {len(records)} keluarga records from {fname}")
        all_survey.extend(records)

    seen_kk = set()
    deduped_survey = []
    corrupt_count = 0
    for rec in all_survey:
        if _is_corrupt_row(rec):
            corrupt_count += 1
            logger.log("CORRUPT_ROW", "WARNING",
                       "Corrupt survey row — KK=1, NIK KK=1, Nama=1.0 (skipping)",
                       kk=clean_id(rec.get("Nomor KK")))
            continue

        kk = clean_id(rec.get("Nomor KK"))
        if not kk:
            continue
        if kk in seen_kk:
            logger.log("DUPLICATE_KK", "WARNING",
                       f"KK {kk} appears in multiple keluarga survey responses; "
                       f"keeping first",
                       kk=kk)
            continue
        seen_kk.add(kk)
        rec["Nomor KK"] = kk
        deduped_survey.append(rec)

    if corrupt_count:
        logger.log("CORRUPT_ROW", "WARNING",
                   f"Skipped {corrupt_count} corrupt survey rows")

    survey_by_kk = {}
    for rec in deduped_survey:
        kk = rec["Nomor KK"]
        survey_by_kk[kk] = rec

    for kk, survey_rec in survey_by_kk.items():
        survey_rec.setdefault("_notes", [])

        if not is_valid_nik(kk):
            survey_rec["_kk_note"] = "NO KK tidak valid ({} digit)".format(len(kk))

        raw_nik_kk = survey_rec.get("Nomor NIK Kepala Keluarga")
        cleaned_nik_kk = clean_id(raw_nik_kk)
        if not is_valid_nik(cleaned_nik_kk):
            repaired, note = repair_nik_kk_from_bip(kk, bip_by_kk)
            if repaired:
                survey_rec["_nik_kk_repaired"] = True
                survey_rec["_nik_kk_note"] = "NIK KK: {}".format(note)
                survey_rec["Nomor NIK Kepala Keluarga"] = repaired
            else:
                survey_rec["_nik_kk_note"] = "NIK KK tidak valid ({} digit) — {}".format(
                    len(cleaned_nik_kk) if cleaned_nik_kk else 0, note)

    output_records = []
    matched_kk_count = 0
    unmatched_kk_count = 0

    for kk, survey_rec in survey_by_kk.items():
        family_members = bip_by_kk.get(str(kk), [])
        if not family_members:
            logger.log("BIP_KK_NOT_FOUND", "INFO",
                       f"KK {kk} not found in BIP; "
                       f"outputting survey data without BIP individual info",
                       kk=kk)
            unmatched_kk_count += 1
            member = {
                "NO KK": kk,
                "NIK": "",
                "NAMA LENGKAP": to_upper(survey_rec.get("Nama")),
                "ALAMAT": "",
            }
            output_records.append(_build_keluarga_output(member, survey_rec, logger))
        else:
            matched_kk_count += 1
            for member in family_members:
                output_records.append(
                    _build_keluarga_output(member, survey_rec, logger))

    logger.log("KELUARGA_MATCH", "INFO",
               f"Matched {matched_kk_count} KKs to BIP, "
               f"{unmatched_kk_count} KKs not in BIP, "
               f"{len(output_records)} total individual rows")

    def sort_key(r):
        kk = r.get("NO KK", "")
        return (not bool(kk), kk if kk else "zzz")

    output_records.sort(key=sort_key)

    for rec in output_records:
        notes = rec.get("_notes", [])
        if notes:
            rec["Action"] = "Periksa"
        else:
            rec["Action"] = "Auto"

    return output_records
