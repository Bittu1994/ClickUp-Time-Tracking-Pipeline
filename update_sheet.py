#!/usr/bin/env python3
"""Simple script: take a local Excel file (first sheet) and POST it as CSV to an Apps Script URL.

Usage:
    python update_sheet.py /path/to/file.xlsx https://script.google.com/macros/s/AKfy.../exec

Requirements: requests, pandas, openpyxl
    pip install requests pandas openpyxl

This is intentionally minimal and assumes the Excel file is valid .xlsx and the Apps Script endpoint
accepts a POST with Content-Type: text/csv and writes it into the spreadsheet.
"""
import sys
import io
import pandas as pd
import requests


def excel_first_sheet_to_csv_text(path):
    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    df = xls.parse(sheet, dtype=str).fillna("")
    return df.to_csv(index=False)


def post_csv(apps_url, csv_text):
    headers = {"Content-Type": "text/csv; charset=utf-8"}
    resp = requests.post(apps_url, data=csv_text.encode("utf-8"), headers=headers, timeout=30)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return resp.text


def main():
    if len(sys.argv) != 3:
        print("Usage: python update_sheet.py /path/to/file.xlsx <Apps Script URL>")
        sys.exit(1)

    path = sys.argv[1]
    apps_url = sys.argv[2]

    csv_text = excel_first_sheet_to_csv_text(path)
    print(f"Converted '{path}' -> {len(csv_text.splitlines())} CSV lines. Posting to Apps Script...")
    resp = post_csv(apps_url, csv_text)
    print("Response from Apps Script:", resp)


if __name__ == "__main__":
    main()
