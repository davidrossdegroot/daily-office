"""Offline full-year auditing uses recorded source data, not live network calls."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CalendarAuditTests(unittest.TestCase):
    def test_full_year_audit_is_reproducible_from_a_source_snapshot(self):
        source = ROOT / 'tests' / 'fixtures' / 'calendar-source-2027.csv'
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / 'bin' / 'audit_years.py'), str(source),
                 '--output-dir', directory],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / '2027.review.json').read_text())
            self.assertEqual(len(list((Path(directory) / '2027-site').glob('2027-*.html'))), 365)
            self.assertTrue(any(item['code'] == 'rendered_placeholder' for item in report['findings']))
            with (Path(directory) / '2027.csv').open(newline='') as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 365)
        self.assertFalse(report['publishable'])
        self.assertTrue(report['source_sha256'])
        self.assertTrue(all(item['date'] and item['field'] and item['message']
                            for item in report['findings']))
        self.assertFalse(any(item['code'] in {'missing_date', 'duplicate_date'}
                             for item in report['findings']))

    def test_2028_leap_day_and_moving_seasons_survive_full_year_generation(self):
        source = ROOT / 'tests' / 'fixtures' / 'calendar-source-2028.csv'
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(ROOT / 'bin' / 'audit_years.py'), str(source),
                       '--output-dir', directory]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with (Path(directory) / '2028.csv').open(newline='') as stream:
                rows = {row['Date']: row for row in csv.DictReader(stream)}
            first = (Path(directory) / '2028.review.json').read_bytes()
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first, (Path(directory) / '2028.review.json').read_bytes())
        self.assertEqual(len(rows), 366)
        self.assertTrue(rows['Feb 29']['MP Opening Sentence of Scripture'].endswith('malachi 1:11'))
        self.assertEqual(rows['Jan 9']['Liturgical Color'], 'White')
        self.assertEqual(rows['Mar 1']['Liturgical Color'], 'Purple')
        self.assertTrue(rows['Mar 1']['Seasonal Blessing'])
