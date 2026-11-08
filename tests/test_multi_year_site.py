import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'generate', Path(__file__).resolve().parents[1] / 'generate.py'
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

ATTRIBUTION = 'The Book of Common Prayer (2019)'
LOCAL_LINK = re.compile(r'(?:href|src)="(?!https?:|mailto:|#)([^"]+)"')


def days_for(directory, year):
    path = Path(directory) / f'acna-prayers-{year}.csv'
    path.write_text('Date,Liturgical Color,Observance\nJan 1,White,Feast\nJan 2,White,Feria\n')
    return MODULE.parse_csv(path)


class MultiYearSiteTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.output = self.directory / 'build'

    def build(self, years, current_year):
        MODULE.build_site(
            {year: days_for(self.directory, year) for year in years},
            self.output,
            current_year,
        )

    def text(self, relative):
        return (self.output / relative).read_text(encoding='utf-8')

    def test_two_years_are_built_without_overwriting_each_other(self):
        self.build([2026, 2027], current_year=2026)
        self.assertIn('2026 Calendar', self.text('2026/index.html'))
        self.assertIn('2027 Calendar', self.text('2027/index.html'))
        self.assertIn('2026 Calendar', self.text('index.html'))

    def test_visitors_can_switch_between_years_in_both_directions(self):
        self.build([2026, 2027], current_year=2026)
        self.assertIn('href="2027/index.html"', self.text('index.html'))
        self.assertIn('href="../2027/index.html"', self.text('2026/index.html'))
        self.assertIn('href="../2026/index.html"', self.text('2027/index.html'))
        self.assertIn('aria-current="page">2027<', self.text('2027/index.html'))

    def test_single_year_is_flat_with_no_switcher(self):
        self.build([2026], current_year=2026)
        self.assertNotIn('year-switcher', self.text('index.html'))
        self.assertTrue((self.output / '2026-01-01.html').exists())
        self.assertFalse((self.output / '2026').exists())

    def test_every_local_link_resolves(self):
        self.build([2026, 2027], current_year=2026)
        for page in self.output.rglob('*.html'):
            for link in LOCAL_LINK.findall(page.read_text(encoding='utf-8')):
                if re.search(r'all-(?!january)[a-z]+\.html$', link):
                    continue  # The fixtures only cover January.
                with self.subTest(page=str(page), link=link):
                    self.assertTrue((page.parent / link).resolve().exists())

    def test_day_navigation_stays_within_the_year(self):
        self.build([2026, 2027], current_year=2026)
        self.assertIn('href="2027-01-02.html"', self.text('2027/2027-01-01.html'))
        self.assertIn('href="../static/style.css"', self.text('2027/2027-01-01.html'))

    def test_day_urls_survive_a_change_of_default_year(self):
        self.build([2026, 2027], current_year=2027)
        redirect = self.text('2026-01-01.html')
        self.assertIn('url=2026/2026-01-01.html', redirect)
        self.assertIn('2027 Calendar', self.text('index.html'))
        self.assertNotIn('http-equiv="refresh"', self.text('2027-01-01.html'))

    def test_attribution_is_on_every_page(self):
        self.build([2026, 2027], current_year=2026)
        for page in self.output.rglob('*.html'):
            content = page.read_text(encoding='utf-8')
            if 'http-equiv="refresh"' in content:
                continue
            with self.subTest(page=str(page)):
                self.assertIn(ATTRIBUTION, content)

    def test_default_year_selection(self):
        self.assertEqual(MODULE.select_default_year([2026, 2027], 2026), 2026)
        self.assertEqual(MODULE.select_default_year([2026, 2027], 2027), 2027)
        self.assertEqual(MODULE.select_default_year([2026, 2027], 2030), 2027)
        self.assertEqual(MODULE.select_default_year([2026, 2027], 2025), 2026)


    def test_publication_review_checks_nondefault_year_pages(self):
        days = {year: days_for(self.directory, year) for year in (2026, 2027)}
        days[2027][0]['Seasonal Collect'] = 'Unresolved prayer for N&#46;'
        MODULE.build_site(days, self.output, current_year=2026)
        findings = MODULE.validate_rendered_pages(self.output)
        self.assertTrue(any(item['date'] == '2027/2027-01-01' and
                            item['code'] == 'rendered_placeholder' for item in findings))


if __name__ == '__main__':
    unittest.main()
