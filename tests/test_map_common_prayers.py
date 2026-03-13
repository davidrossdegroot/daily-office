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


class InferCommonTypeTests(unittest.TestCase):
    def test_bishop_and_teacher_prefers_pastor_common(self) -> None:
        remembrance = "Gregory the Great, Bishop of Rome and Teacher of the Faith, 604"
        self.assertEqual(MODULE.infer_common_type(remembrance, ""), "common of a pastor")

    def test_teacher_without_pastoral_role_stays_teacher_common(self) -> None:
        remembrance = "Clive Staples Lewis, Teacher of the Faith, 1963"
        self.assertEqual(
            MODULE.infer_common_type(remembrance, ""),
            "common of a teacher of the faith",
        )

    def test_prepare_rows_exposes_gregory_common_type_and_collect(self) -> None:
        fieldnames, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "March 12",
                    "Observance": "Lent",
                    "Remembrance": (
                        "Gregory the Great, Bishop of Rome and Teacher of the Faith, 604"
                    ),
                }
            ],
            source_path_for_inference=None,
            generated_year_for_inference=2026,
            flatten=False,
            acna_year=None,
            acna_base_url="",
            acna_province="",
            calendar_mode="fill",
            fill_remembrance_from_calendar=False,
            ignore_fetch_errors=False,
            seasonal_map_path=None,
            seasonal_mode="fill",
            mp_opening_mode="off",
            ep_opening_mode="off",
            antiphon_mode="off",
            seasonal_blessing_mode="off",
            special_collect_mode="overwrite",
            include_common_type=True,
        )

        self.assertIn("Common Type", fieldnames)
        self.assertEqual(rows[0]["Common Type"], "common of a pastor")
        self.assertEqual(
            rows[0]["Special Collect"],
            MODULE.COMMON_PRAYERS["common of a pastor"],
        )


if __name__ == "__main__":
    unittest.main()
