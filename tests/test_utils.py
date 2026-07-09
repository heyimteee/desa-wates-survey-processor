"""Tests for utils.py — all pure functions."""

import datetime

import pytest

from utils import (
    clean_id, is_valid_nik, name_key,
    to_upper, to_text, to_int,
    clean_health_value, clean_and_validate_phone,
    clean_email, clean_income,
    is_sentinel, dash_if_empty, format_currency,
    normalize_jamkes, normalize_yes_no, normalize_jk,
    normalize_pendidikan, normalize_bantuan,
    derive_pendidikan_years, parse_date, calculate_age,
    detect_health_anomaly,
    build_bip_name_index, classify_nik_duplicate,
    repair_nik_by_name, repair_nik_kk_from_bip,
)


# ======================================================================
# clean_id
# ======================================================================

class TestCleanId:
    def test_none_returns_empty(self):
        assert clean_id(None) == ""

    def test_float_strips_decimal(self):
        assert clean_id(3505204107580130.0) == "3505204107580130"

    def test_int_to_string(self):
        assert clean_id(3505204107580130) == "3505204107580130"

    def test_string_preserved(self):
        assert clean_id("3505204107580130") == "3505204107580130"

    def test_string_dot_zero_stripped(self):
        assert clean_id("3505204107580130.0") == "3505204107580130"

    def test_empty_string(self):
        assert clean_id("") == ""

    def test_whitespace_string(self):
        assert clean_id("  ") == ""


# ======================================================================
# is_valid_nik
# ======================================================================

class TestIsValidNik:
    def test_valid_16_digits(self):
        assert is_valid_nik("3505200107570071") is True

    def test_15_digits_invalid(self):
        assert is_valid_nik("350520010757001") is False

    def test_17_digits_invalid(self):
        assert is_valid_nik("35052001075700717") is False

    def test_empty_invalid(self):
        assert is_valid_nik("") is False

    def test_none_invalid(self):
        assert is_valid_nik(None) is False

    def test_letters_invalid(self):
        assert is_valid_nik("3505abc123456789") is False

    def test_int_input(self):
        assert is_valid_nik(3505200107570071) is True


# ======================================================================
# name_key
# ======================================================================

class TestNameKey:
    def test_normal(self):
        assert name_key("GITO") == "gito"

    def test_uppercase_input(self):
        assert name_key("SUPRIYANTO") == "supriyanto"

    def test_mixed_case(self):
        assert name_key("Sri Wahyuni") == "sri wahyuni"

    def test_none_returns_empty(self):
        assert name_key(None) == ""

    def test_strips_whitespace(self):
        assert name_key("  BUDI  ") == "budi"

    def test_collapses_multi_space(self):
        assert name_key("SRI   WAHYUNI") == "sri wahyuni"


# ======================================================================
# to_upper
# ======================================================================

class TestToUpper:
    def test_lower_to_upper(self):
        assert to_upper("gito") == "GITO"

    def test_none_returns_none(self):
        assert to_upper(None) is None

    def test_empty_string_returns_none(self):
        assert to_upper("") is None

    def test_float_converts_to_string(self):
        assert to_upper(5.0) == "5.0"

    def test_strips_whitespace(self):
        assert to_upper("  gito  ") == "GITO"


# ======================================================================
# to_text
# ======================================================================

class TestToText:
    def test_normal(self):
        assert to_text("Hello") == "Hello"

    def test_none_returns_none(self):
        assert to_text(None) is None

    def test_empty_returns_none(self):
        assert to_text("") is None

    def test_number_to_string(self):
        assert to_text(123) == "123"


# ======================================================================
# to_int
# ======================================================================

class TestToInt:
    def test_int_preserved(self):
        assert to_int(25) == 25

    def test_float_truncated(self):
        assert to_int(25.7) == 25

    def test_string_number(self):
        assert to_int("25") == 25

    def test_none_returns_none(self):
        assert to_int(None) is None

    def test_empty_returns_none(self):
        assert to_int("") is None

    def test_dash_returns_none(self):
        assert to_int("-") is None

    def test_non_numeric_returns_none(self):
        assert to_int("abc") is None


# ======================================================================
# clean_health_value
# ======================================================================

class TestCleanHealthValue:
    def test_none_returns_zero(self):
        assert clean_health_value(None) == 0

    def test_int_preserved(self):
        assert clean_health_value(4) == 4

    def test_float_to_int(self):
        assert clean_health_value(4.0) == 4

    def test_tidak_pernah_preserved(self):
        assert clean_health_value("TIDAK PERNAH") == "TIDAK PERNAH"

    def test_lebih_dari_5_preserved(self):
        assert clean_health_value("Lebih dari 5 kali") == "Lebih dari 5 kali"

    def test_empty_returns_zero(self):
        assert clean_health_value("") == 0

    def test_contradictory_preserved(self):
        assert clean_health_value("TIDAK PERNAH, 1") == "TIDAK PERNAH, 1"


# ======================================================================
# clean_and_validate_phone
# ======================================================================

class TestCleanAndValidatePhone:
    def test_none_returns_dash(self):
        r, n = clean_and_validate_phone(None)
        assert r == "-"
        assert n is None

    def test_int_zero_sentinel(self):
        r, n = clean_and_validate_phone(0)
        assert r == "-"

    def test_int_one_sentinel(self):
        r, n = clean_and_validate_phone(1)
        assert r == "-"

    def test_float_zero_sentinel(self):
        r, n = clean_and_validate_phone(0.0)
        assert r == "-"

    def test_float_one_sentinel(self):
        r, n = clean_and_validate_phone(1.0)
        assert r == "-"

    def test_empty_string(self):
        r, n = clean_and_validate_phone("")
        assert r == "-"

    def test_single_digit(self):
        r, n = clean_and_validate_phone("2")
        assert r == "-"
        assert n == "hanya 1 digit"

    def test_plus62_conversion(self):
        r, n = clean_and_validate_phone("+628123456789")
        assert r == "08123456789"
        assert "dikonversi dari +62" in n

    def test_62_no_plus_conversion(self):
        r, n = clean_and_validate_phone("628123456789")
        assert r == "08123456789"
        assert "dikonversi dari 62" in n

    def test_valid_08_number(self):
        r, n = clean_and_validate_phone("085731939503")
        assert r == "085731939503"
        assert n is None

    def test_spaces_stripped(self):
        r, n = clean_and_validate_phone("+62 812 3456 789")
        assert r == "08123456789"

    def test_commas_stripped_valid(self):
        r, n = clean_and_validate_phone("0812,3456,789")
        assert r == "08123456789"

    def test_comma_separated_short(self):
        r, n = clean_and_validate_phone("1,2")
        assert r == "-"
        assert n == "terlalu pendek"

    def test_pure_comma(self):
        r, n = clean_and_validate_phone(",")
        assert r == "-"
        assert n == "hanya tanda baca"

    def test_contains_letters(self):
        r, n = clean_and_validate_phone("0812abc")
        assert r == "-"
        assert n == "mengandung teks"

    def test_6_digit_too_short(self):
        r, n = clean_and_validate_phone("086521")
        assert r == "-"
        assert n == "terlalu pendek"

    def test_dot_zero_artifact_string(self):
        r, n = clean_and_validate_phone("085731939503.0")
        assert r == "085731939503"

    def test_dot_zero_artifact_float(self):
        r, n = clean_and_validate_phone(8123456789.0)
        assert r == "8123456789"

    def test_foreign_number_preserved(self):
        r, n = clean_and_validate_phone("+85291824889")
        assert r == "+85291824889"

    def test_not_08_indonesian(self):
        r, n = clean_and_validate_phone("05123456789")
        assert r == "05123456789"
        assert n == "tidak diawali 08"

    def test_repeated_digits_flag(self):
        r, n = clean_and_validate_phone("0000000000")
        assert r == "0000000000"
        assert n == "pola mencurigakan (digit berulang)"

    def test_long_number_preserved(self):
        r, n = clean_and_validate_phone("085623451234567")
        assert r == "085623451234567"


# ======================================================================
# clean_email
# ======================================================================

class TestCleanEmail:
    def test_valid_email(self):
        assert clean_email("test@gmail.com") == "test@gmail.com"

    def test_no_at_symbol(self):
        assert clean_email("testemail") is None

    def test_sentinel_zero(self):
        assert clean_email(0) is None

    def test_sentinel_one(self):
        assert clean_email(1) is None

    def test_empty(self):
        assert clean_email("") is None

    def test_none(self):
        assert clean_email(None) is None


# ======================================================================
# clean_income
# ======================================================================

class TestCleanIncome:
    def test_valid_income(self):
        assert clean_income(12000000) == 12000000

    def test_sentinel_zero(self):
        assert clean_income(0) is None

    def test_sentinel_one(self):
        assert clean_income(1) is None

    def test_string_with_dots(self):
        assert clean_income("12.000.000") == 12000000

    def test_empty(self):
        assert clean_income("") is None

    def test_dash(self):
        assert clean_income("-") is None

    def test_none(self):
        assert clean_income(None) is None

    def test_non_numeric(self):
        assert clean_income("abc") is None


# ======================================================================
# detect_health_anomaly
# ======================================================================

class TestDetectHealthAnomaly:
    def test_none_no_anomaly(self):
        r, t, m = detect_health_anomaly(None)
        assert r is False

    def test_int_no_anomaly(self):
        r, t, m = detect_health_anomaly(4)
        assert r is False

    def test_float_no_anomaly(self):
        r, t, m = detect_health_anomaly(4.0)
        assert r is False

    def test_plain_text_no_anomaly(self):
        r, t, m = detect_health_anomaly("TIDAK PERNAH")
        assert r is False

    def test_mixed_text_number(self):
        r, t, m = detect_health_anomaly("TIDAK PERNAH, 1")
        assert r is True
        assert t == "mixed"

    def test_multi_numeric(self):
        r, t, m = detect_health_anomaly("2, 3")
        assert r is True
        assert t == "multi_numeric"

    def test_multi_text_no_anomaly(self):
        r, t, m = detect_health_anomaly("TIDAK PERNAH, Setiap Bulan")
        assert r is False

    def test_multi_text_long_no_anomaly(self):
        r, t, m = detect_health_anomaly("TIDAK PERNAH, Lebih dari 5 kali")
        assert r is False


# ======================================================================
# normalize_bantuan
# ======================================================================

class TestNormalizeBantuan:
    def test_ya(self):
        assert normalize_bantuan("Ya") == "YA"

    def test_tidak(self):
        assert normalize_bantuan("Tidak") == "TIDAK"

    def test_ambiguous_ya_tidak(self):
        assert normalize_bantuan("Ya, Tidak") == "YA"

    def test_empty_defaults_to_tidak(self):
        assert normalize_bantuan("") == "TIDAK"

    def test_none_defaults_to_tidak(self):
        assert normalize_bantuan(None) == "TIDAK"


# ======================================================================
# normalize_jamkes
# ======================================================================

class TestNormalizeJamkes:
    def test_peserta(self):
        assert normalize_jamkes("Peserta") == "PESERTA"

    def test_bukan_peserta(self):
        assert normalize_jamkes("Bukan Peserta") == "BUKAN PESERTA"

    def test_none(self):
        assert normalize_jamkes(None) is None

    def test_unknown_preserved(self):
        assert normalize_jamkes("something") == "SOMETHING"


# ======================================================================
# normalize_yes_no
# ======================================================================

class TestNormalizeYesNo:
    def test_ya(self):
        assert normalize_yes_no("Ya") == "YA"

    def test_tidak(self):
        assert normalize_yes_no("Tidak") == "TIDAK"

    def test_none(self):
        assert normalize_yes_no(None) is None

    def test_unknown_preserved(self):
        assert normalize_yes_no("maybe") == "MAYBE"


# ======================================================================
# normalize_jk
# ======================================================================

class TestNormalizeJk:
    def test_L(self):
        assert normalize_jk("L") == "L"

    def test_P(self):
        assert normalize_jk("P") == "P"

    def test_laki_laki(self):
        assert normalize_jk("LAKI-LAKI") == "L"

    def test_perempuan(self):
        assert normalize_jk("PEREMPUAN") == "P"


# ======================================================================
# normalize_pendidikan
# ======================================================================

class TestNormalizePendidikan:
    def test_standard_format(self):
        assert normalize_pendidikan("SLTA / SEDERAJAT") == "SLTA / SEDERAJAT"

    def test_bip_no_spaces(self):
        assert normalize_pendidikan("SLTP/SEDERAJAT") == "SLTP / SEDERAJAT"

    def test_none(self):
        assert normalize_pendidikan(None) is None

    def test_empty(self):
        assert normalize_pendidikan("") is None

    def test_dash(self):
        assert normalize_pendidikan("-") is None


# ======================================================================
# derive_pendidikan_years
# ======================================================================

class TestDerivePendidikanYears:
    def test_sd(self):
        assert derive_pendidikan_years("SD / SEDERAJAT") == 6

    def test_sltp(self):
        assert derive_pendidikan_years("SLTP / SEDERAJAT") == 9

    def test_slta(self):
        assert derive_pendidikan_years("SLTA / SEDERAJAT") == 12

    def test_d3(self):
        assert derive_pendidikan_years("DIPLOMA I - III") == 13

    def test_s1(self):
        assert derive_pendidikan_years("S-1 / SEDERAJAT") == 16

    def test_s2(self):
        assert derive_pendidikan_years("S-2 / SEDERAJAT") == 18

    def test_s3(self):
        assert derive_pendidikan_years("S-3 / SEDERAJAT") == 21

    def test_tidak_sekolah(self):
        assert derive_pendidikan_years("TIDAK / BELUM SEKOLAH") == 0

    def test_belum_sekolah(self):
        assert derive_pendidikan_years("BELUM SEKOLAH") == 0

    def test_none(self):
        assert derive_pendidikan_years(None) is None

    def test_empty(self):
        assert derive_pendidikan_years("") is None

    def test_unknown(self):
        assert derive_pendidikan_years("KURSUS KOMPUTER") is None

    def test_fuzzy_smp(self):
        assert derive_pendidikan_years("SMP NEGERI 1") == 9


# ======================================================================
# parse_date
# ======================================================================

class TestParseDate:
    def test_dd_mm_yyyy(self):
        d = parse_date("07-07-1971")
        assert d == datetime.date(1971, 7, 7)

    def test_yyyy_mm_dd(self):
        d = parse_date("1971-07-07")
        assert d == datetime.date(1971, 7, 7)

    def test_datetime_object(self):
        dt = datetime.datetime(1971, 7, 7, 12, 0)
        assert parse_date(dt) == datetime.date(1971, 7, 7)

    def test_date_object(self):
        d = datetime.date(1971, 7, 7)
        assert parse_date(d) == d

    def test_none(self):
        assert parse_date(None) is None

    def test_empty(self):
        assert parse_date("") is None

    def test_dash(self):
        assert parse_date("-") is None

    def test_unparseable(self):
        assert parse_date("abc") is None


# ======================================================================
# calculate_age
# ======================================================================

class TestCalculateAge:
    def test_birthday_past_this_year(self):
        d = datetime.date(1971, 1, 1)
        age = calculate_age(d)
        assert age >= 53  # as of 2025-2026

    def test_birthday_later_this_year(self):
        d = datetime.date(1971, 12, 31)
        age = calculate_age(d)
        assert age >= 53

    def test_none_returns_none(self):
        assert calculate_age(None) is None

    def test_very_old(self):
        d = datetime.date(1900, 1, 1)
        age = calculate_age(d)
        assert age > 120

    def test_recent_birth(self):
        d = datetime.date(2020, 1, 1)
        age = calculate_age(d)
        assert age >= 5


# ======================================================================
# format_currency
# ======================================================================

class TestFormatCurrency:
    def test_int(self):
        assert format_currency(12000000) == 12000000

    def test_float(self):
        assert format_currency(12000000.50) == 12000000

    def test_none(self):
        assert format_currency(None) is None

    def test_empty(self):
        assert format_currency("") is None

    def test_string_with_dots(self):
        assert format_currency("12.000.000") == 12000000


# ======================================================================
# is_sentinel
# ======================================================================

class TestIsSentinel:
    def test_int_0(self):
        assert is_sentinel(0) is True

    def test_int_1(self):
        assert is_sentinel(1) is True

    def test_float_0(self):
        assert is_sentinel(0.0) is True

    def test_float_1(self):
        assert is_sentinel(1.0) is True

    def test_str_0(self):
        assert is_sentinel("0") is True

    def test_str_1(self):
        assert is_sentinel("1") is True

    def test_str_dot_zero(self):
        assert is_sentinel("1.0") is True

    def test_normal_number(self):
        assert is_sentinel(2) is False

    def test_string(self):
        assert is_sentinel("hello") is False


# ======================================================================
# dash_if_empty
# ======================================================================

class TestDashIfEmpty:
    def test_none(self):
        assert dash_if_empty(None) == "-"

    def test_empty_string(self):
        assert dash_if_empty("") == "-"

    def test_value_preserved(self):
        assert dash_if_empty("TIDAK") == "TIDAK"

    def test_dash_preserved(self):
        assert dash_if_empty("-") == "-"


# ======================================================================
# build_bip_name_index
# ======================================================================

class TestBuildBipNameIndex:
    def test_empty_list(self):
        assert build_bip_name_index([]) == {}

    def test_single_record(self):
        records = [{"NAMA LENGKAP": "GITO", "NIK": "3505200107570071"}]
        idx = build_bip_name_index(records)
        assert "gito" in idx
        assert len(idx["gito"]) == 1

    def test_multiple_same_name(self):
        records = [
            {"NAMA LENGKAP": "SUPRIYANTO", "NIK": "A"},
            {"NAMA LENGKAP": "SUPRIYANTO", "NIK": "B"},
        ]
        idx = build_bip_name_index(records)
        assert len(idx["supriyanto"]) == 2


# ======================================================================
# classify_nik_duplicate
# ======================================================================

class TestClassifyNikDuplicate:
    def test_same_name(self, bip_pool):
        result = classify_nik_duplicate(
            "3505200107570071", "GITO", "GITO", bip_pool["by_nik"])
        assert result == "same"

    def test_a_owns(self, bip_pool):
        result = classify_nik_duplicate(
            "3505200107570071", "GITO", "SUPRIYANTO", bip_pool["by_nik"])
        assert result == "a_owns"

    def test_b_owns(self, bip_pool):
        result = classify_nik_duplicate(
            "3505200107570071", "SUPRIYANTO", "GITO", bip_pool["by_nik"])
        assert result == "b_owns"

    def test_neither_no_bip(self, bip_pool):
        result = classify_nik_duplicate(
            "9999999999999999", "A", "B", bip_pool["by_nik"])
        assert result == "neither"

    def test_neither_different_name(self, bip_pool):
        result = classify_nik_duplicate(
            "3505200107570071", "XYZ", "ABC", bip_pool["by_nik"])
        assert result == "neither"


# ======================================================================
# repair_nik_by_name
# ======================================================================

class TestRepairNikByName:
    def test_valid_nik_no_repair(self, bip_pool):
        from logger import IssueLogger
        r, n = repair_nik_by_name(
            "3505200107570071", "GITO", "5", "1", bip_pool["by_name"], IssueLogger())
        assert r == "3505200107570071"
        assert n is None

    def test_repair_by_name_and_rt_rw(self, bip_pool):
        from logger import IssueLogger
        r, n = repair_nik_by_name(
            "3505200107570", "GITO", "5", "1", bip_pool["by_name"], IssueLogger())
        assert r == "3505200107570071"
        assert "diperbaiki" in n

    def test_no_name_match(self, bip_pool):
        from logger import IssueLogger
        r, n = repair_nik_by_name(
            "3505200107570", "NONEXISTENT", "5", "1", bip_pool["by_name"], IssueLogger())
        assert r is None

    def test_already_valid(self, bip_pool):
        from logger import IssueLogger
        r, n = repair_nik_by_name(
            "3505200107570071", "GITO", "5", "1", bip_pool["by_name"], IssueLogger())
        assert r == "3505200107570071"


# ======================================================================
# repair_nik_kk_from_bip
# ======================================================================

class TestRepairNikKkFromBip:
    def test_find_kepala_from_kk(self, bip_pool):
        r, n = repair_nik_kk_from_bip("3505201010060507", bip_pool["by_kk"])
        assert r == "3505200107570071"
        assert "diperbaiki" in n

    def test_kk_not_found(self, bip_pool):
        r, n = repair_nik_kk_from_bip("9999999999999999", bip_pool["by_kk"])
        assert r is None

    def test_kk_as_int(self, bip_pool):
        r, n = repair_nik_kk_from_bip(3505201010060507, bip_pool["by_kk"])
        assert r == "3505200107570071"
