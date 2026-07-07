#!/usr/bin/env python3
"""Formatter, normalizer, and general utility functions."""

import re
import datetime

import openpyxl
from openpyxl.utils import get_column_letter

from config import TODAY, PENDIDIKAN_YEARS


def auto_fit_columns(ws, headers, max_row, min_width=8, max_width=50, padding=2):
    """Auto-size column widths based on content.

    Scans all cells in each column and sets width to fit the longest value,
    capped at max_width to avoid excessively wide columns.
    """
    for col_idx, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_idx)
        max_len = len(str(header)) if header else 0
        for row in range(2, max_row + 1):
            val = ws.cell(row, col_idx).value
            if val is not None:
                s = str(val)
                line_len = max(len(line) for line in s.split("\n"))
                if line_len > max_len:
                    max_len = line_len
        width = min(max(max_len + padding, min_width), max_width)
        ws.column_dimensions[col_letter].width = width


def to_upper(val):
    """Convert a value to uppercase string, preserving None/empty."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "":
        return None
    return s.upper()


def to_text(val):
    """Convert a value to stripped string, preserving None/empty."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "":
        return None
    return s


def clean_id(val):
    """Clean an ID value (NIK, KK) from Excel numeric artifacts."""
    if val is None:
        return ""
    if isinstance(val, float):
        return str(int(val))
    if isinstance(val, int):
        return str(val)
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def to_int(val):
    """Convert a value to int, preserving None/empty."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def clean_health_value(val):
    """Clean a health access survey value for storage.

    Numeric values (1.0, 2.0) -> int. Text values kept as-is. None -> 0.
    """
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    if s == "":
        return 0
    return s


def normalize_jamkes(val):
    """Normalize Jamkes (health insurance) values."""
    if val is None:
        return None
    s = str(val).strip().upper()
    if s == "PESERTA":
        return "PESERTA"
    if "BUKAN" in s:
        return "BUKAN PESERTA"
    return s if s else None


def normalize_yes_no(val):
    """Normalize Ya/Tidak values."""
    if val is None:
        return None
    s = str(val).strip().upper()
    if s == "YA":
        return "YA"
    if s == "TIDAK":
        return "TIDAK"
    return s if s else None


def normalize_jk(val):
    """Normalize Jenis Kelamin values."""
    if val is None:
        return None
    s = str(val).strip().upper()
    if s in ("L", "P"):
        return s
    if "LAKI" in s:
        return "L"
    if "PEREMPUAN" in s or "WANITA" in s:
        return "P"
    return s if s else None


def parse_date(val):
    """Parse a date value from BIP (dd-mm-yyyy) or Excel date."""
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def calculate_age(birth_date):
    """Calculate age from birth date to today."""
    if birth_date is None:
        return None
    age = TODAY.year - birth_date.year
    if (TODAY.month, TODAY.day) < (birth_date.month, birth_date.day):
        age -= 1
    if age < 0:
        age = 0
    return age


def dash_if_empty(val):
    """Return dash if value is None or empty, otherwise the value."""
    if val is None:
        return "-"
    s = str(val).strip()
    if s == "":
        return "-"
    return val


def format_currency(val):
    """Format a numeric value as integer rupiah (strip decimals)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    s = s.replace(".", "").replace(",", "")
    try:
        return int(float(s))
    except ValueError:
        return None


def clean_phone(val):
    """Clean phone number values, removing Google Forms sentinels."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if val <= 1:
            return None
        return str(int(val))
    s = str(val).strip()
    if s == "" or s in ("0", "1", "0.0", "1.0"):
        return None
    return s


def clean_email(val):
    """Clean email values, removing Google Forms sentinels."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if val <= 1:
            return None
        return str(int(val))
    s = str(val).strip()
    if s == "" or s in ("0", "1", "0.0", "1.0"):
        return None
    if "@" not in s:
        return None
    return s


def clean_income(val):
    """Clean income values, treating 0/1 sentinels as empty."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if val <= 1:
            return None
        return int(val)
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    s = s.replace(".", "").replace(",", "")
    try:
        n = int(float(s))
        if n <= 1:
            return None
        return n
    except ValueError:
        return None


def is_sentinel(val):
    """Check if a value is a Google Forms sentinel (0 or 1)."""
    if isinstance(val, (int, float)):
        return val in (0, 1, 0.0, 1.0)
    if isinstance(val, str):
        return val.strip() in ("0", "1", "0.0", "1.0")
    return False


def normalize_pendidikan(val):
    """Normalize pendidikan values to template format (spaces around /)."""
    if val is None:
        return None
    s = str(val).strip().upper()
    if s == "" or s == "-":
        return None
    s = re.sub(r"\s*/\s*", " / ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def derive_pendidikan_years(pendidikan):
    """Derive years of education from pendidikan level."""
    if not pendidikan:
        return None
    p = pendidikan.upper().strip()
    if p in PENDIDIKAN_YEARS:
        return PENDIDIKAN_YEARS[p]
    for key, years in PENDIDIKAN_YEARS.items():
        if key in p or p in key:
            return years
    if "TIDAK" in p or "BELUM" in p:
        return 0
    if "SD" in p:
        return 6
    if "SLTP" in p or "SMP" in p:
        return 9
    if "SLTA" in p or "SMA" in p:
        return 12
    if "DIPLOMA" in p:
        return 13
    if "S-1" in p or "S1" in p or "STRATA I" in p:
        return 16
    if "S-2" in p or "S2" in p or "STRATA II" in p:
        return 18
    if "S-3" in p or "S3" in p or "STRATA III" in p:
        return 21
    return None
