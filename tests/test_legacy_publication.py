"""The 2026 exemption is about page ownership, not finding labels."""
import csv
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class LegacyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'data').mkdir()
        for directory in ('templates', 'static'):
            (self.root / directory).symlink_to(ROOT / directory, target_is_directory=True)
        shutil.copyfile(ROOT / 'generate.py', self.root / 'generate.py')
        spec = importlib.util.spec_from_file_location('legacy_publication_generator', self.root / 'generate.py')
        self.generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.generator)
        self.output = self.root / 'site'

    def source(self, year, problem=None, complete=True):
        with (ROOT / 'tests/fixtures/february-2027-pr51.csv').open(newline='') as stream:
            seed = next(csv.DictReader(stream))
        rows = []
        dt = date(year, 1, 1)
        while dt.year == year:
            row = dict(seed, **{'Date': f'{dt:%b} {dt.day}', 'Observance': 'Feria',
                               'Remembrance': '', 'Special Collect': '',
                               'Seasonal Blessing': 'A reviewed prayer. Amen.'})
            rows.append(row)
            dt += timedelta(days=1)
        if problem == 'csv':
            rows[0]['MP First Lesson'] = ''
        if problem in {'legacy', 'rendered'}:
            rows[0]['Seasonal Collect'] = 'A prayer for N&#46;'
        if problem == 'legacy':
            rows[0]['MP First Lesson'] = ''
            rows[0]['Observance'] = 'Legacy N&#46;'
        if not complete:
            rows = rows[:31]
        with (self.root / 'data' / f'acna-prayers-{year}.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(seed))
            writer.writeheader()
            writer.writerows(rows)

    def publish(self, current_year):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(current_year, 11, 8, tzinfo=UTC)

        with patch.object(self.generator, 'datetime', Clock), patch.object(
            sys, 'argv', ['generate.py', '--publish', '--output-dir', str(self.output)]
        ):
            self.generator.main()
        return json.loads(self.output.with_suffix('.review.json').read_text())

    def test_only_2026_publishes_with_nonblocking_csv_and_root_rendered_findings(self):
        self.source(2026, problem='legacy')
        report = self.publish(2026)
        self.assertTrue(report['publishable'])
        self.assertTrue({'missing_field', 'rendered_placeholder'} <= {item['code'] for item in report['findings']})
        self.assertTrue(all(item['year'] == 2026 and not item['blocking'] for item in report['findings']))
        rendered = {item['date'] for item in report['findings'] if item['code'] == 'rendered_placeholder'}
        self.assertTrue({'index', 'all', 'all-january', '2026-01-01'} <= rendered)
        self.assertTrue((self.output / '2026-01-01.html').exists())

    def test_2027_errors_and_incomplete_year_block_without_replacing_existing_output(self):
        self.source(2026, problem='legacy')
        self.output.mkdir()
        (self.output / 'index.html').write_text('existing published calendar')
        for current_year in (2026, 2027):
            for problem, complete in (('csv', True), ('rendered', True), (None, False)):
                with self.subTest(current_year=current_year, problem=problem, complete=complete):
                    self.source(2027, problem=problem, complete=complete)
                    with self.assertRaises(SystemExit) as error:
                        self.publish(current_year)
                    self.assertEqual(error.exception.code, 2)
                    self.assertEqual((self.output / 'index.html').read_text(), 'existing published calendar')
                    self.assertEqual(list(self.output.iterdir()), [self.output / 'index.html'])
                    report = json.loads(self.output.with_suffix('.review.json').read_text())
                    self.assertFalse(report['publishable'])
                    self.assertTrue(any(item['year'] == 2027 and item['blocking'] for item in report['findings']))
                    self.assertFalse(any(item['year'] == 2026 and item['blocking'] for item in report['findings']))

    def test_clean_complete_2027_publishes_both_years_and_preserves_year_switching_and_urls(self):
        self.source(2026, problem='legacy')
        self.source(2027)
        for current_year in (2026, 2027):
            with self.subTest(current_year=current_year):
                report = self.publish(current_year)
                self.assertTrue(report['publishable'])
                self.assertTrue(report['findings'])
                self.assertTrue(all(item['year'] == 2026 and not item['blocking'] for item in report['findings']))
                for year in (2026, 2027):
                    page = self.output / str(year) / 'index.html'
                    self.assertIn(f'{year} Calendar', page.read_text())
                    switcher = page.read_text().split('<nav class="year-switcher"', 1)[1].split('</nav>', 1)[0]
                    self.assertIn(f'aria-current="page">{year}<', switcher)
                    self.assertIn(f'href="../{2027 if year == 2026 else 2026}/index.html"', switcher)
                    self.assertTrue((self.output / str(year) / f'{year}-01-01.html').exists())
                    root_day = (self.output / f'{year}-01-01.html').read_text()
                    if year != current_year:
                        self.assertIn(f'url={year}/{year}-01-01.html', root_day)
                    else:
                        self.assertNotIn('http-equiv="refresh"', root_day)
                root = (self.output / 'index.html').read_text()
                self.assertIn(f'{current_year} Calendar', root)
                switcher = root.split('<nav class="year-switcher"', 1)[1].split('</nav>', 1)[0]
                self.assertIn(f'aria-current="page">{current_year}<', switcher)
                self.assertIn(f'href="{2027 if current_year == 2026 else 2026}/index.html"', switcher)
                labels = {item['date'] for item in report['findings'] if item['code'] == 'rendered_placeholder'}
                self.assertTrue({'2026/index', '2026/all', '2026/all-january'} <= labels)
                self.assertEqual('index' in labels, current_year == 2026)
                self.assertEqual('all' in labels, current_year == 2026)
                self.assertEqual('all-january' in labels, current_year == 2026)

    def test_unknown_rendered_page_ownership_is_strict_even_with_2026_filename(self):
        self.output.mkdir()
        (self.output / '2026-01-01.html').write_text('N&#46;')
        findings = self.generator.validate_rendered_pages(self.output)
        self.assertTrue(findings[0]['blocking'])
        self.assertIsNone(findings[0]['year'])

    def test_exemption_does_not_expand_to_other_past_or_future_years(self):
        self.source(2026, problem='legacy')
        self.output.mkdir()
        (self.output / 'index.html').write_text('existing output')
        for year in (2025, 2027, 2028):
            for problem in ('csv', 'rendered'):
                with self.subTest(year=year, problem=problem):
                    self.source(year, problem=problem)
                    with self.assertRaises(SystemExit):
                        self.publish(2026)
                    report = json.loads(self.output.with_suffix('.review.json').read_text())
                    self.assertTrue(any(item['year'] == year and item['blocking'] for item in report['findings']))
                    self.assertEqual((self.output / 'index.html').read_text(), 'existing output')
            (self.root / 'data' / f'acna-prayers-{year}.csv').unlink()
