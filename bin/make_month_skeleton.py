#!/usr/bin/env python3
"""
Generate a month input CSV skeleton for map_common_prayers.py.

Output columns:
- Date
- Remembrance

Example:
  python bin/make_month_skeleton.py --year 2026 --month 3 --out month.input.csv
"""

from __future__ import annotations

import argparse
import calendar
import csv
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a month CSV skeleton with Date + Remembrance columns."
    )
    parser.add_argument("--year", type=int, required=True, help="Year (for example: 2026)")
    parser.add_argument("--month", type=int, required=True, help="Month number 1-12")
    parser.add_argument("--out", required=True, help="Output CSV path")
    return parser.parse_args()


def month_rows(year: int, month: int) -> list[dict[str, str]]:
    if month < 1 or month > 12:
        raise ValueError("--month must be between 1 and 12")
    _, days_in_month = calendar.monthrange(year, month)
    rows: list[dict[str, str]] = []
    for day in range(1, days_in_month + 1):
        dt = date(year, month, day)
        rows.append(
            {
                "Date": f"{dt.strftime('%b')} {dt.day}",
                "Remembrance": "",
            }
        )
    return rows


def write_rows(rows: list[dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Remembrance"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    rows = month_rows(args.year, args.month)
    output_path = Path(args.out)
    write_rows(rows, output_path)
    print(f"Wrote month skeleton: {output_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
