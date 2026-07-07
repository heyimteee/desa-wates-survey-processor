#!/usr/bin/env python3
"""KELUARGA pipeline: survey + BIP -> template-formatted records."""

import os

from survey_loader import load_keluarga_survey
from utils import clean_id, to_upper, to_int, to_text, normalize_yes_no


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


def _parse_distance(val):
    """Parse distance value from survey (could be number or text)."""
    if val is None:
        return "-"
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if s == "":
        return "-"
    return s


def _parse_time(val):
    """Parse time value from survey."""
    if val is None:
        return "-"
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if s == "":
        return "-"
    return s


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
    out["LUAS LANTAI TEMPAT TINGGAL (m2)"] = to_int(luas)
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

    out["PAUD - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke PAUD"))
    out["PAUD - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke PAUD"))
    out["PAUD - KEMUDAHAN"] = "-"

    out["TK/RA - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke TK/RA"))
    out["TK/RA - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke TK/RA"))
    out["TK/RA - KEMUDAHAN"] = "-"

    out["SD/MI - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke SD/MI atau Sederajat"))
    out["SD/MI - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke SD/MI atau Sederajat"))
    out["SD/MI - KEMUDAHAN"] = "-"

    out["SMP/MTs - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke SMP/MTs atau Sederajat"))
    out["SMP/MTs - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke SMP/MTs atau Sederajat"))
    out["SMP/MTs - KEMUDAHAN"] = "-"

    out["SMA/MA - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke SMA/MA atau Sederajat"))
    out["SMA/MA - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke  SMA/MA atau Sederajat"))
    out["SMA/MA - KEMUDAHAN"] = "-"

    out["PERGURUAN TINGGI - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke Perguruan Tinggi"))
    out["PERGURUAN TINGGI - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke Perguruan Tinggi"))
    out["PERGURUAN TINGGI - KEMUDAHAN"] = "-"

    out["PESANTREN - JARAK (KM)"] = "-"
    out["PESANTREN - WAKTU (JAM)"] = "-"
    out["PESANTREN - KEMUDAHAN"] = "-"

    out["SEMINARI - JARAK (KM)"] = "-"
    out["SEMINARI - WAKTU (JAM)"] = "-"
    out["SEMINARI - KEMUDAHAN"] = "-"

    out["PEND. KEAGAMAAN LAIN - JARAK (KM)"] = "-"
    out["PEND. KEAGAMAAN LAIN - WAKTU (JAM)"] = "-"
    out["PEND. KEAGAMAAN LAIN - KEMUDAHAN"] = "-"

    out["RUMAH SAKIT - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke Rumah Sakit"))
    out["RUMAH SAKIT - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke Rumah Sakit"))
    out["RUMAH SAKIT - KEMUDAHAN"] = "-"

    out["RS BERSALIN - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke Rumah Bersalin"))
    out["RS BERSALIN - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke Rumah Bersalin"))
    out["RS BERSALIN - KEMUDAHAN"] = "-"

    out["POLIKLINIK - JARAK (KM)"] = "-"
    out["POLIKLINIK - WAKTU (JAM)"] = "-"
    out["POLIKLINIK - KEMUDAHAN"] = "-"

    out["PUSKESMAS - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke Pukesmas"))
    out["PUSKESMAS - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke Pukesmas"))
    out["PUSKESMAS - KEMUDAHAN"] = "-"

    out["POSKESDES - JARAK (KM)"] = "-"
    out["POSKESDES - WAKTU (JAM)"] = "-"
    out["POSKESDES - KEMUDAHAN"] = "-"

    out["POSYANDU - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke Posyandu"))
    out["POSYANDU - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke Posyandu"))
    out["POSYANDU - KEMUDAHAN"] = "-"

    out["APOTIK - JARAK (KM)"] = _parse_distance(survey_rec.get("Jarak dari rumah ke Apotek"))
    out["APOTIK - WAKTU (JAM)"] = _parse_time(survey_rec.get("Waktu yang dibutuhkan dari rumah ke  Apotek"))
    out["APOTIK - KEMUDAHAN"] = "-"

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

    out["BLT"] = normalize_yes_no(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BLT]"))
    out["PKH"] = normalize_yes_no(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [PKH]"))
    out["BST"] = normalize_yes_no(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BST]"))
    out["BANTUAN PRESIDEN"] = normalize_yes_no(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BPNT]"))
    out["BANTUAN UMKM"] = normalize_yes_no(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan UMKM]"))

    bantuan_pekerja = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan Untuk Pekerja]")
    bsu = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [BSU]")
    if bantuan_pekerja and normalize_yes_no(bantuan_pekerja) == "YA":
        out["BANTUAN PEKERJA"] = "YA"
    elif bsu and normalize_yes_no(bsu) == "YA":
        out["BANTUAN PEKERJA"] = "YA"
    else:
        out["BANTUAN PEKERJA"] = normalize_yes_no(bantuan_pekerja) or "TIDAK"

    out["BANTUAN ANAK"] = normalize_yes_no(survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan untuk Pendidikan Anak]"))

    lainnya = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Bantuan Lain dari Pemerintah ]")
    sembako = survey_rec.get(
        "Pemanfaat/Penerima Program pemerintah [Sembako]")
    if lainnya and normalize_yes_no(lainnya) == "YA":
        out["LAINNYA"] = "YA"
    elif sembako and normalize_yes_no(sembako) == "YA":
        out["LAINNYA"] = "YA"
    else:
        out["LAINNYA"] = normalize_yes_no(lainnya) or "TIDAK"

    pengeluaran = survey_rec.get("Rata rata pengeluaran satu keluarga dalam satu bulan")
    out["RATA-RATA PENGELUARAN / BULAN (Rp)"] = to_text(pengeluaran)

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
    for rec in all_survey:
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

    survey_by_kk = {}
    for rec in deduped_survey:
        kk = rec["Nomor KK"]
        survey_by_kk[kk] = rec

    output_records = []
    matched_kk_count = 0
    unmatched_kk_count = 0

    for kk, survey_rec in survey_by_kk.items():
        family_members = bip_by_kk.get(kk, [])
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
            output_records.append(_build_keluarga_record(member, survey_rec, logger))
        else:
            matched_kk_count += 1
            for member in family_members:
                output_records.append(
                    _build_keluarga_record(member, survey_rec, logger))

    logger.log("KELUARGA_MATCH", "INFO",
               f"Matched {matched_kk_count} KKs to BIP, "
               f"{unmatched_kk_count} KKs not in BIP, "
               f"{len(output_records)} total individual rows")

    def sort_key(r):
        kk = r.get("NO KK", "")
        return (not bool(kk), kk if kk else "zzz")

    output_records.sort(key=sort_key)

    return output_records
