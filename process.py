#!/usr/bin/env python3
"""
Data Processing Tool for Desa Wates Micro Data Survey.

Processes survey responses (BAHAN) and civil registry data (BIP) into
template-formatted Excel outputs for both INDIVIDU and KELUARGA datasets.

Usage:
    python3 process.py
"""

import os
import sys

from config import BAHAN_DIR, BIP_DIR, OUTPUT_DIR
from config import TEMPLATE_INDIVIDU, TEMPLATE_KELUARGA
from config import OUTPUT_ISSUES

from logger import IssueLogger
from bip_loader import load_bip_pool
from survey_loader import find_survey_files, parse_survey_filename, build_output_name
from pipeline_individu import process_individu
from pipeline_keluarga import process_keluarga
from excel_writer import write_individu_output, write_keluarga_output


def main():
    """Main orchestrator: load all inputs, run both pipelines, write outputs."""
    print("=" * 70)
    print("  DATA PROCESSING TOOL - DESA WATES MICRO DATA SURVEY")
    print("=" * 70)
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---- Load BIP pool ----
    print("[1/5] Loading BIP files...")
    bip_by_nik, bip_by_kk, bip_all, bip_logger, bip_by_name = load_bip_pool(BIP_DIR)
    print(f"      Loaded {len(bip_all)} BIP records "
          f"({len(bip_by_nik)} unique NIKs, {len(bip_by_kk)} unique KKs)")

    logger = IssueLogger()
    logger.issues.extend(bip_logger.issues)

    # ---- Find survey files ----
    print()
    print("[2/5] Finding survey files...")
    individu_files = find_survey_files(BAHAN_DIR, "INDIVIDU")
    keluarga_files = find_survey_files(BAHAN_DIR, "Keluarga")

    if not individu_files and not keluarga_files:
        print("\nERROR: No survey files found in BAHAN/.")
        print("       Expected files containing 'INDIVIDU' or 'Keluarga' in the name.")
        sys.exit(1)

    print(f"      INDIVIDU: {len(individu_files)} files")
    for f in individu_files:
        info = parse_survey_filename(os.path.basename(f))
        name = build_output_name(
            info["data_type"],
            [int(info["rt"])] if info["rt"] else [],
            info["rw"], info["dusun"])
        print(f"        -> {name}")
    print(f"      KELUARGA: {len(keluarga_files)} files")
    for f in keluarga_files:
        info = parse_survey_filename(os.path.basename(f))
        name = build_output_name(
            info["data_type"],
            [int(info["rt"])] if info["rt"] else [],
            info["rw"], info["dusun"])
        print(f"        -> {name}")

    # ---- Process INDIVIDU files ----
    print()
    print("[3/5] Processing INDIVIDU pipeline...")
    if individu_files:
        for fpath in individu_files:
            fname = os.path.basename(fpath)
            info = parse_survey_filename(fname)
            rt = int(info["rt"]) if info["rt"] else None
            output_name = build_output_name(
                info["data_type"], [rt] if rt else [],
                info["rw"], info["dusun"])
            output_path = os.path.join(OUTPUT_DIR, output_name)

            print(f"      File: {fname}")
            records = process_individu([fpath], bip_by_nik, bip_by_name, logger)
            print(f"        Output: {len(records)} rows")
            write_individu_output(records, TEMPLATE_INDIVIDU,
                                  output_path, logger)
            print(f"        Written: OUTPUT/{output_name}")
    else:
        print("      No INDIVIDU survey files found, skipping.")

    # ---- Process KELUARGA files ----
    print()
    print("[4/5] Processing KELUARGA pipeline...")
    if keluarga_files:
        for fpath in keluarga_files:
            fname = os.path.basename(fpath)
            info = parse_survey_filename(fname)
            rt = int(info["rt"]) if info["rt"] else None
            output_name = build_output_name(
                info["data_type"], [rt] if rt else [],
                info["rw"], info["dusun"])
            output_path = os.path.join(OUTPUT_DIR, output_name)

            print(f"      File: {fname}")
            records = process_keluarga([fpath], bip_by_kk, bip_all, logger)
            print(f"        Output: {len(records)} rows")
            write_keluarga_output(records, TEMPLATE_KELUARGA,
                                  output_path, logger)
            print(f"        Written: OUTPUT/{output_name}")
    else:
        print("      No KELUARGA survey files found, skipping.")

    # ---- Write data issues ----
    print()
    print("[5/5] Writing data issues log...")
    logger.write_to_excel(OUTPUT_ISSUES)
    print(f"      {len(logger.issues)} issues logged to OUTPUT/DATA_ISSUES.xlsx")

    print()
    print("=" * 70)
    print("  PROCESSING COMPLETE")
    print("=" * 70)
    print(f"  Output directory: {OUTPUT_DIR}")
    print()

    warnings = [i for i in logger.issues if i["Severity"] == "WARNING"]
    infos = [i for i in logger.issues if i["Severity"] == "INFO"]
    print(f"  Data Issues: {len(warnings)} warnings, {len(infos)} info")
    if warnings:
        print()
        print("  WARNINGS:")
        for w in warnings[:10]:
            print(f"    [{w['Category']}] {w['Description'][:80]}")
        if len(warnings) > 10:
            print(f"    ... and {len(warnings) - 10} more (see DATA_ISSUES.xlsx)")
    print()


if __name__ == "__main__":
    main()
