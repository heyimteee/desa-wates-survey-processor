#!/usr/bin/env python3
"""Data quality issue logger."""

import openpyxl
from openpyxl.styles import Font

from utils import auto_fit_columns


class IssueLogger:
    """Collects data quality warnings for the DATA_ISSUES output sheet."""

    def __init__(self):
        self.issues = []

    def log(self, category, severity, description, nik="", nama="", kk=""):
        """Record a data issue.

        Args:
            category: Type of issue (e.g. 'DUPLICATE_NIK', 'BIP_NOT_FOUND').
            severity: 'WARNING' or 'INFO'.
            description: Human-readable explanation.
            nik: Related NIK if applicable.
            nama: Related name if applicable.
            kk: Related KK if applicable.
        """
        self.issues.append({
            "Category": category,
            "Severity": severity,
            "NIK": nik,
            "Nama": nama,
            "KK": kk,
            "Description": description,
        })

    def write_to_excel(self, filepath):
        """Write all collected issues to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "DATA ISSUES"
        headers = ["Category", "Severity", "NIK", "Nama", "KK", "Description"]
        for col, h in enumerate(headers, 1):
            cell = ws.cell(1, col)
            cell.value = h
            cell.font = Font(bold=True)

        for row_idx, issue in enumerate(self.issues, 2):
            ws.cell(row_idx, 1).value = issue["Category"]
            ws.cell(row_idx, 2).value = issue["Severity"]
            ws.cell(row_idx, 3).value = issue["NIK"]
            ws.cell(row_idx, 4).value = issue["Nama"]
            ws.cell(row_idx, 5).value = issue["KK"]
            ws.cell(row_idx, 6).value = issue["Description"]

        auto_fit_columns(ws, headers, ws.max_row, min_width=10, max_width=80)
        wb.save(filepath)
