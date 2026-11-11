"""The personal Book spans one Liturgical Year and checks exactly its own dates."""
import csv
import importlib.util
import io
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('generate', ROOT / 'generate.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def edit_row(path, label, field, value):
    """Change one cell, keeping the file's other rows exactly as they were."""
    raw = path.read_text(encoding='utf-8')
    rows = list(csv.DictReader(io.StringIO(raw)))
    for row in rows:
        if row['Date'] == label:
            row[field] = value
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=rows[0].keys(), lineterminator='\r\n')
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(out.getvalue(), encoding='utf-8')


class LiturgicalYearTests(unittest.TestCase):
    def test_first_sunday_of_advent(self):
        expected = {2022: date(2022, 11, 27), 2023: date(2023, 12, 3), 2026: date(2026, 11, 29),
                    2027: date(2027, 11, 28), 2028: date(2028, 12, 3), 2033: date(2033, 11, 27)}
        for year, sunday in expected.items():
            with self.subTest(year=year):
                self.assertEqual(MODULE.first_sunday_of_advent(year), sunday)

    def test_liturgical_year_ends_the_saturday_before_the_next_advent(self):
        start, end = MODULE.liturgical_year_range(2026)
        self.assertEqual((start, end), (date(2026, 11, 29), date(2027, 11, 27)))
        self.assertEqual((end - start).days + 1, 364)
        self.assertEqual(end.isoweekday(), 6)

    def test_book_is_named_by_both_calendar_years(self):
        self.assertEqual(MODULE.book_name(2026), '2026–27')
        self.assertEqual(MODULE.book_name(2099), '2099–00')
        self.assertEqual(MODULE.book_slug(2026), 'daily-office-2026-27')


class BookDataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.data = Path(self.directory.name) / 'data'
        self.data.mkdir()
        for year in (2026, 2027):
            shutil.copy(ROOT / 'data' / f'acna-prayers-{year}.csv', self.data)

    def tearDown(self):
        self.directory.cleanup()

    def test_book_takes_exactly_its_dates_from_both_years(self):
        days, findings = MODULE.collect_book_days(2026, self.data)
        self.assertEqual(findings, [])
        self.assertEqual(len(days), 364)
        self.assertEqual(days[0]['date_slug'], '2026-11-29')
        self.assertEqual(days[-1]['date_slug'], '2027-11-27')
        self.assertEqual(days[33]['date_slug'], '2027-01-01')

    def test_finding_on_a_2026_book_date_blocks_despite_the_site_exemption(self):
        edit_row(self.data / 'acna-prayers-2026.csv', 'Dec 1', 'Antiphon', '')
        _, findings = MODULE.collect_book_days(2026, self.data)
        self.assertEqual([(item['date'], item['field']) for item in findings], [('2026-12-01', 'Antiphon')])
        self.assertTrue(all(item['blocking'] for item in findings))

    def test_findings_outside_the_book_are_ignored(self):
        edit_row(self.data / 'acna-prayers-2026.csv', 'Nov 28', 'Antiphon', '')
        edit_row(self.data / 'acna-prayers-2027.csv', 'Nov 28', 'Antiphon', '')
        self.assertEqual(MODULE.collect_book_days(2026, self.data)[1], [])

    def test_missing_book_date_and_missing_year_are_reported(self):
        path = self.data / 'acna-prayers-2027.csv'
        lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
        path.write_text(''.join(line for line in lines if not line.startswith('Mar 3,')), encoding='utf-8')
        _, findings = MODULE.collect_book_days(2026, self.data)
        self.assertIn(('2027-03-03', 'missing_date'), [(item['date'], item['code']) for item in findings])

        _, findings = MODULE.collect_book_days(2027, self.data)
        self.assertIn('missing_source', [item['code'] for item in findings])

    def test_build_writes_title_page_and_one_article_per_day_outside_the_site(self):
        output = Path(self.directory.name) / 'book'
        html_path, pdf_path = MODULE.build_book(2026, self.data, output)
        html = html_path.read_text(encoding='utf-8')
        self.assertIsNone(pdf_path)
        self.assertEqual(html.count('<article class="book-day office">'), 364)
        self.assertTrue((html_path.parent / 'static' / 'office.css').exists())
        self.assertIn('Daily Office 2026–27', html)
        self.assertIn('2027 Liturgical Year', html)
        self.assertIn('The Book of Common Prayer (2019)', html)
        self.assertNotIn('googletagmanager', html)
        self.assertTrue((html_path.parent / 'static' / 'fonts' / 'EBGaramond-wght.ttf').exists())
        self.assertTrue((html_path.parent / 'static' / 'fonts' / 'OFL.txt').exists())

    def test_build_refuses_a_book_with_findings(self):
        edit_row(self.data / 'acna-prayers-2027.csv', 'Mar 3', 'Antiphon', '')
        with self.assertRaises(MODULE.BookError):
            MODULE.build_book(2026, self.data, Path(self.directory.name) / 'book')


class BookOutputTests(unittest.TestCase):
    def test_book_output_is_ignored_and_its_assets_stay_out_of_the_site(self):
        self.assertIn('/book/', (ROOT / '.gitignore').read_text().splitlines())
        self.assertFalse((ROOT / 'static' / 'book.css').exists())

    def test_pdf_page_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.pdf'
            path.write_bytes(b'<< /Type /Pages /Count 2 >> << /Type /Page >> << /Type/Page >>')
            self.assertEqual(MODULE.count_pdf_pages(path), 2)


if __name__ == '__main__':
    unittest.main()


class SharedStyleTests(unittest.TestCase):
    """The site and the Book share one Daily Office stylesheet and bundled fonts."""

    def test_no_template_loads_google_fonts(self):
        for template in (ROOT / 'templates').glob('*.html'):
            with self.subTest(template=template.name):
                self.assertNotIn('fonts.googleapis.com', template.read_text(encoding='utf-8'))

    def test_site_pages_use_the_shared_office_stylesheet(self):
        with tempfile.TemporaryDirectory() as directory:
            days = MODULE.parse_csv(ROOT / 'data' / 'acna-prayers-2027.csv', year=2027)
            output = Path(directory)
            MODULE.build_site({2027: days}, output, 2027)
            for page in ('index.html', '2027-12-19.html', 'all.html', 'all-may.html', 'about.html'):
                with self.subTest(page=page):
                    html = (output / page).read_text(encoding='utf-8')
                    self.assertLess(html.index('static/office.css'), html.index('static/style.css'))
            self.assertTrue((output / 'static' / 'fonts' / 'EBGaramond-wght.ttf').exists())
            self.assertTrue((output / 'static' / 'fonts' / 'OFL.txt').exists())
            self.assertIn('class="daily-office office"', (output / '2027-12-19.html').read_text(encoding='utf-8'))
