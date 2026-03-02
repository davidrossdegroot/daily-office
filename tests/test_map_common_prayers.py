import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "bin" / "map_common_prayers.py"
SPEC = importlib.util.spec_from_file_location("map_common_prayers", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load script at {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ParseOfficeLineTests(unittest.TestCase):
    def test_psalm_reference_keeps_chapter_prefix(self) -> None:
        self.assertEqual(MODULE.parse_office_line("Psalm 107:1-22"), ("psalms", "107:1-22"))

    def test_psalm_reference_keeps_chapter_prefix_with_en_dash(self) -> None:
        self.assertEqual(
            MODULE.parse_office_line("Psalm 107:1\u201322"),
            ("psalms", "107:1\u201322"),
        )

    def test_psalm_cycle_label_still_parses_value(self) -> None:
        self.assertEqual(
            MODULE.parse_office_line("Psalms (60 day cycle): 107:1-22"),
            ("psalms", "107:1-22"),
        )

    def test_lesson_label_parses_normally(self) -> None:
        self.assertEqual(
            MODULE.parse_office_line("Lesson I: Romans 14"),
            ("first_lesson", "Romans 14"),
        )

    def test_susanna_is_treated_as_scripture_reference(self) -> None:
        parsed = MODULE.parse_office_entries(["Psalm 10", "Susanna", "Acts 26"])
        self.assertEqual(parsed["psalms"], "10")
        self.assertEqual(parsed["first_lesson"], "Susanna")
        self.assertEqual(parsed["second_lesson"], "Acts 26")


if __name__ == "__main__":
    unittest.main()
