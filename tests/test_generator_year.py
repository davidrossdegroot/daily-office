import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'generate', Path(__file__).resolve().parents[1] / 'generate.py'
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GeneratorYearTests(unittest.TestCase):
    def test_explicit_year_handles_leap_day(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.csv'
            path.write_text('Date\nFeb 29\n')
            days = MODULE.parse_csv(path, year=2028)
        self.assertEqual(days[0]['date_slug'], '2028-02-29')
        self.assertEqual(days[0]['day_of_week'], 'Tuesday')

    def test_year_is_inferred_from_draft_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'acna-prayers-2027-01.csv'
            path.write_text('Date\nJan 1\n')
            days = MODULE.parse_csv(path)
        self.assertEqual(days[0]['date_slug'], '2027-01-01')
        self.assertEqual(days[0]['day_of_week'], 'Friday')
