#!/usr/bin/env python3
"""Regenerate and audit complete years offline from recorded calendar-source CSVs."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from map_common_prayers import (
    infer_year_from_filename,
    prepare_rows,
    read_rows,
    validate_rows,
    write_review_report,
    write_rows,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', nargs='+', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for source in args.sources:
        year = infer_year_from_filename(source)
        if year is None:
            parser.error(f'Cannot determine year from {source}')
        fields, rows = prepare_rows(
            rows=read_rows(source), source_path_for_inference=source,
            generated_year_for_inference=year, flatten=True, acna_year=None,
            acna_base_url='', acna_province='', calendar_mode='fill',
            fill_remembrance_from_calendar=False, ignore_fetch_errors=False,
            seasonal_map_path=None, seasonal_mode='fill', mp_opening_mode='overwrite',
            ep_opening_mode='overwrite', antiphon_mode='overwrite',
            seasonal_blessing_mode='overwrite', special_collect_mode='overwrite',
            include_common_type=False,
        )
        target = args.output_dir / f'{year}.csv'
        write_rows(target, fields, rows, delimiter=',')
        findings = validate_rows(rows, year, full_year=True)
        report_path = target.with_suffix('.review.json')
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / 'generate.py'),
             '--year', str(year), '--csv', str(target),
             '--output-dir', str(args.output_dir / f'{year}-site'),
             '--review-report', str(report_path)],
            check=True, capture_output=True, text=True,
        )
        rendered = json.loads(report_path.read_text())['findings']
        findings.extend(item for item in rendered if item['code'] == 'rendered_placeholder')
        write_review_report(report_path, findings, year)
        report = json.loads(report_path.read_text())
        report['source'] = source.name
        report['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        report['row_count'] = len(rows)
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(f'{year}: {len(rows)} entries, {len(findings)} publication blockers ({report_path})')


if __name__ == '__main__':
    main()
