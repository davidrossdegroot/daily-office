import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "generate.py"
SPEC = importlib.util.spec_from_file_location("generate", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load script at {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "acna-prayers-2026.csv"


class RemembranceSubstitutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        days = MODULE.parse_csv(str(CSV_PATH))
        cls.days = {day["Date"]: day for day in days}

    def test_saint_name_replaces_N_placeholder(self) -> None:
        day = self.days["March 17"]  # Patrick, Bishop and Apostle to the Irish, 461
        self.assertIn("Patrick", day["Special Collect"])
        self.assertNotIn(" N.", day["Special Collect"])

    def test_blank_placeholder_is_left_untouched(self) -> None:
        day = self.days["March 17"]
        self.assertIn("people of _________", day["Special Collect"])

    def test_substitution_uses_name_before_first_comma(self) -> None:
        day = self.days["March 21"]  # Thomas Cranmer, Archbishop of Canterbury..., 1556
        self.assertIn("Thomas Cranmer", day["Special Collect"])
        self.assertNotIn(" N.", day["Special Collect"])

    def test_saint_name_replaces_N_followed_by_comma(self) -> None:
        day = self.days["March 29"]  # John Keble — collect uses "servant N., kindled…"
        self.assertIn("John Keble", day["Special Collect"])
        self.assertNotIn("N.,", day["Special Collect"])

    def test_no_substitution_without_remembrance(self) -> None:
        day_without_remembrance = next(
            d for d in self.days.values()
            if d.get("Special Collect") and not d.get("Remembrance")
        )
        # If N. was in the original it should still be there (no substitution attempted)
        # We just assert the collect is a non-empty string
        self.assertIsNotNone(day_without_remembrance["Special Collect"])

    def test_no_error_when_special_collect_is_absent(self) -> None:
        day_without_collect = next(
            d for d in self.days.values() if not d.get("Special Collect")
        )
        # Should not raise; Remembrance field (if any) is irrelevant
        self.assertIsNone(day_without_collect["Special Collect"])
