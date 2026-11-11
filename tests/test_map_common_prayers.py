import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path

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
    def test_temporal_remembrance_does_not_generate_saints_collect(self) -> None:
        for remembrance in (
            "The Tenth Day of Christmas",
            "The Monday in the First Week After Epiphany",
            "The Second Sunday of Easter",
        ):
            with self.subTest(remembrance=remembrance):
                self.assertEqual(
                    MODULE.infer_common_type(remembrance, "The Second Sunday of Christmas"),
                    "",
                )

    def test_ember_day_keeps_its_common_prayer(self) -> None:
        self.assertEqual(
            MODULE.infer_common_type("Ember Day", "Advent"), "ember day"
        )

    def test_teacher_of_the_faith_title_prefers_teacher_common(self) -> None:
        for remembrance in (
            "Example Person, Bishop of Nowhere and Teacher of the Faith, 400",
            "Example Person, Priest and Teacher of the Faith, 400",
            "Example Person, Deacon and Teacher of the Faith, 400",
        ):
            with self.subTest(remembrance=remembrance):
                self.assertEqual(
                    MODULE.infer_common_type(remembrance, ""), "common of a teacher of the faith"
                )

    def test_earlier_categories_still_outrank_teacher_title(self) -> None:
        self.assertEqual(
            MODULE.infer_common_type("Justin, Teacher of the Faith and Martyr at Rome, c. 165", ""),
            "common of a martyr",
        )
        self.assertEqual(
            MODULE.infer_common_type("Example Person, Evangelist in Nowhere and Teacher of the Faith, 400", ""),
            "common of a missionary or evangelist",
        )

    def test_bishop_without_teacher_title_stays_pastor_common(self) -> None:
        self.assertEqual(
            MODULE.infer_common_type("Example Person, Bishop of Nowhere, 400", ""), "common of a pastor"
        )

    def test_teacher_without_pastoral_role_stays_teacher_common(self) -> None:
        remembrance = "Clive Staples Lewis, Teacher of the Faith, 1963"
        self.assertEqual(
            MODULE.infer_common_type(remembrance, ""),
            "common of a teacher of the faith",
        )

    def test_prepare_rows_exposes_unreviewed_bishop_common_type_and_collect(self) -> None:
        fieldnames, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "March 12",
                    "Observance": "Lent",
                    "Remembrance": (
                        "Example Person, Bishop of Nowhere, 400"
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


class FixedHolyDayProperTests(unittest.TestCase):
    def test_secondary_holy_day_uses_exact_heading_and_proper_collect(self) -> None:
        _, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "March 19",
                    "Observance": "Lent / St Joseph",
                    "Remembrance": "The Thursday in the Fourth Week of Lent",
                    "Special Collect": MODULE.COMMON_PRAYERS["common of any commemoration"],
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

        self.assertEqual(rows[0]["Observance"], "Lent / Saint Joseph")
        self.assertEqual(rows[0]["Remembrance"], "Saint Joseph")
        self.assertEqual(
            rows[0]["Special Collect"],
            MODULE.FIXED_HOLY_DAY_PROPERS[(3, 19)]["collect"],
        )
        self.assertEqual(rows[0]["Common Type"], "fixed holy day proper")
        self.assertEqual(rows[0]["Liturgical Color"], "White")

    def test_primary_holy_day_replaces_generic_weekday_remembrance(self) -> None:
        _, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "Apr 25",
                    "Observance": "Mark the Evangelist",
                    "Seasonal Collect": MODULE.FIXED_HOLY_DAY_PROPERS[(4, 25)]["collect"],
                    "Remembrance": "The Third Saturday of Easter",
                    "Special Collect": MODULE.COMMON_PRAYERS["common of a missionary or evangelist"],
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

        self.assertEqual(rows[0]["Observance"], "Saint Mark")
        self.assertEqual(rows[0]["Remembrance"], "")
        self.assertEqual(rows[0]["Special Collect"], "")
        self.assertEqual(rows[0]["Common Type"], "fixed holy day proper")
        self.assertEqual(rows[0]["Liturgical Color"], "Red")

    def test_combined_sunday_observance_is_normalized_to_exact_heading(self) -> None:
        _, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "Jan 18",
                    "Observance": "2nd Sunday in Epiphany / Confession of Peter",
                    "Remembrance": "",
                    "Special Collect": "",
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

        self.assertEqual(
            rows[0]["Observance"],
            "2nd Sunday in Epiphany / Confession of Saint Peter",
        )
        self.assertEqual(rows[0]["Remembrance"], "Confession of Saint Peter")
        self.assertEqual(
            rows[0]["Special Collect"],
            MODULE.FIXED_HOLY_DAY_PROPERS[(1, 18)]["collect"],
        )
        self.assertEqual(rows[0]["Common Type"], "fixed holy day proper")
        self.assertEqual(rows[0]["Liturgical Color"], "White")


class LiturgicalColorInferenceTests(unittest.TestCase):
    def test_optional_saint_in_lent_keeps_seasonal_purple(self) -> None:
        _, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "March 23",
                    "Observance": "Lent",
                    "Remembrance": "Gregory the Illuminator, Missionary to Armenia, 333",
                    "Liturgical Color": "Green",
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
            special_collect_mode="off",
            include_common_type=False,
        )

        self.assertEqual(rows[0]["Liturgical Color"], "Purple")

    def test_annunciation_transfer_date_covers_holy_week_and_easter_week(self) -> None:
        expected = {
            2008: date(2008, 3, 31),  # Easter Week
            2016: date(2016, 4, 4),  # Good Friday
            2024: date(2024, 4, 8),  # Monday of Holy Week
            2027: date(2027, 4, 5),  # Maundy Thursday
            2026: None,
            2028: None,
        }
        for year, transfer in expected.items():
            with self.subTest(year=year):
                self.assertEqual(MODULE.annunciation_transfer_date(year), transfer)

    def test_secondary_holy_day_in_lent_can_override_with_white(self) -> None:
        _, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "March 25",
                    "Observance": "Lent / The Annunciation",
                    "Remembrance": "The Annunciation",
                    "Liturgical Color": "Purple",
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
            special_collect_mode="off",
            include_common_type=False,
        )

        self.assertEqual(rows[0]["Liturgical Color"], "White")

    def test_last_sunday_in_epiphany_keeps_green_despite_transfiguration_label(self) -> None:
        _, rows = MODULE.prepare_rows(
            rows=[
                {
                    "Date": "Feb 15",
                    "Observance": "Last Sunday in Epiphany / Transfiguration",
                    "Remembrance": "",
                    "Liturgical Color": "Purple",
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
            special_collect_mode="off",
            include_common_type=False,
        )

        self.assertEqual(rows[0]["Liturgical Color"], "Green")


class AntiphonInferenceTests(unittest.TestCase):
    def test_good_friday_keeps_lenten_antiphon_despite_saint_remembrance(self) -> None:
        self.assertEqual(
            MODULE.infer_antiphon(
                "Good Friday",
                "James Lloyd Breck, Priest and Missionary, 1879",
            ),
            MODULE.SEASONAL_ANTIPHONS["lent"],
        )

    def test_holy_saturday_keeps_lenten_antiphon_despite_easter_eve_remembrance(self) -> None:
        self.assertEqual(
            MODULE.infer_antiphon(
                "Holy Saturday",
                "Easter Eve / Martin Luther King, Jr., Renewer of Society, 1968",
            ),
            MODULE.SEASONAL_ANTIPHONS["lent"],
        )

    def test_annunciation_sunday_keeps_advent_antiphon(self) -> None:
        # "Annunciation Sunday" names Advent 4, not the Annunciation feast.
        for current in (date(2026, 12, 20), date(2027, 12, 19), date(2028, 12, 24)):
            with self.subTest(current=current):
                self.assertEqual(
                    MODULE.infer_antiphon(
                        "The Fourth Sunday in Advent (Annunciation Sunday)", "", current,
                    ),
                    MODULE.SEASONAL_ANTIPHONS["advent"],
                )
        self.assertEqual(
            MODULE.infer_antiphon(
                "The Annunciation of Our Lord Jesus Christ to the Virgin Mary (Lady Day)",
                "", date(2027, 4, 5),
            ),
            MODULE.SEASONAL_ANTIPHONS["presentation_annunciation"],
        )

    def test_ordinary_antiphons_rotate_from_the_monday_after_pentecost(self) -> None:
        for monday in (date(2027, 5, 17), date(2028, 6, 5)):
            with self.subTest(monday=monday):
                for offset in range(6):
                    self.assertEqual(
                        MODULE.infer_antiphon("Ordinary day", "", monday + timedelta(days=offset)),
                        MODULE.ORDINARY_ANTIPHONS[offset % 3],
                    )

    def test_ordinary_antiphons_keep_bcp_order(self) -> None:
        self.assertEqual(
            [antiphon.split(":", 1)[0] for antiphon in MODULE.ORDINARY_ANTIPHONS],
            [
                "The earth is the Lord’s for he made it",
                "Worship the Lord in the beauty of holiness",
                "The mercy of the Lord is everlasting",
            ],
        )

    def test_approved_feasts_after_pentecost_use_the_saints_antiphon(self) -> None:
        saints = MODULE.SEASONAL_ANTIPHONS["all_saints_major"]
        feasts = (
            (5, 31), (6, 11), (6, 24), (6, 29), (7, 22), (7, 25), (8, 15),
            (8, 24), (9, 21), (9, 29), (10, 18), (10, 23), (10, 28),
        )
        for month, day in feasts:
            with self.subTest(month=month, day=day):
                self.assertEqual(MODULE.infer_antiphon("Feast", "", date(2027, month, day)), saints)
        self.assertEqual(MODULE.infer_antiphon("All Saints' Day", "", date(2027, 11, 1)), saints)

    def test_saint_andrew_uses_saints_antiphon_only_before_advent(self) -> None:
        self.assertEqual(
            MODULE.infer_antiphon("Saint Andrew", "", date(2028, 11, 30)),
            MODULE.SEASONAL_ANTIPHONS["all_saints_major"],
        )
        self.assertEqual(
            MODULE.infer_antiphon("Saint Andrew", "", date(2027, 11, 30)),
            MODULE.SEASONAL_ANTIPHONS["advent"],
        )

    def test_holy_cross_follows_the_ordinary_rotation(self) -> None:
        current = date(2027, 9, 14)
        expected = MODULE.ORDINARY_ANTIPHONS[(current - date(2027, 5, 17)).days % 3]
        self.assertEqual(MODULE.infer_antiphon("Holy Cross Day", "", current), expected)

    def test_optional_commemorations_follow_the_ordinary_rotation(self) -> None:
        current = date(2027, 5, 25)
        expected = MODULE.ORDINARY_ANTIPHONS[(current - date(2027, 5, 17)).days % 3]
        for remembrance in (
            "Bede the Venerable, Priest and Monk of Jarrow, 735",
            "John Calvin, Reformer of the Church, 1564",
            "Ember Day",
        ):
            with self.subTest(remembrance=remembrance):
                self.assertEqual(MODULE.infer_antiphon("Ordinary day", remembrance, current), expected)

    def test_seasonal_antiphons_outrank_feasts_and_commemorations(self) -> None:
        cases = (
            (date(2025, 5, 31), "The Visitation", "", "ascension_until_pentecost"),
            (date(2028, 6, 11), "Trinity Sunday", "Barnabas the Apostle", "trinity_sunday"),
            (date(2027, 3, 12), "Lent", "Gregory the Great, Bishop of Rome, 604", "lent"),
        )
        for current, observance, remembrance, key in cases:
            with self.subTest(current=current):
                self.assertEqual(
                    MODULE.infer_antiphon(observance, remembrance, current),
                    MODULE.SEASONAL_ANTIPHONS[key],
                )

    def test_transferred_annunciation_keeps_its_antiphon(self) -> None:
        self.assertEqual(
            MODULE.infer_antiphon("The Second Monday of Easter", "The Annunciation", date(2027, 4, 5)),
            MODULE.SEASONAL_ANTIPHONS["presentation_annunciation"],
        )

    def test_annunciation_antiphon_does_not_apply_outside_a_transfer(self) -> None:
        self.assertEqual(
            MODULE.infer_antiphon("Lent", "", date(2028, 4, 5)),
            MODULE.SEASONAL_ANTIPHONS["lent"],
        )
        self.assertEqual(
            MODULE.infer_antiphon("Maundy Thursday", "", date(2027, 3, 25)),
            MODULE.SEASONAL_ANTIPHONS["lent"],
        )

    def test_every_day_has_an_antiphon_across_years(self) -> None:
        for year in (2027, 2028):
            current = date(year, 1, 1)
            while current.year == year:
                self.assertTrue(MODULE.infer_antiphon("Ordinary day", "", current), current)
                current += timedelta(days=1)


if __name__ == "__main__":
    unittest.main()


class JanuarySeasonRegressionTests(unittest.TestCase):
    def test_named_feasts_keep_seasonal_openings_across_years(self):
        from datetime import date

        for year in (2027, 2028):
            for day, observance, season in (
                (1, 'The Circumcision and Holy Name of Our Lord Jesus Christ', 'christmas'),
                (18, 'Confession of Saint Peter', 'epiphany'),
                (25, 'Conversion of Saint Paul', 'epiphany'),
            ):
                with self.subTest(year=year, day=day):
                    dt = date(year, 1, day)
                    self.assertEqual(
                        MODULE.infer_mp_opening_sentence(observance, dt),
                        MODULE.MP_OPENING_SENTENCES[season],
                    )
                    self.assertEqual(
                        MODULE.infer_ep_opening_sentence(observance, dt),
                        MODULE.EP_OPENING_SENTENCES[season],
                    )

    def test_epiphany_feast_color_and_blessing_across_years(self):
        from datetime import date

        for year in (2027, 2028):
            heading = 'The Epiphany of Our Lord Jesus Christ'
            dt = date(year, 1, 6)
            self.assertEqual(MODULE.infer_liturgical_color(heading, dt), 'White')
            self.assertEqual(
                MODULE.infer_seasonal_blessing(heading, dt),
                MODULE.SEASONAL_BLESSING_TEXT['epiphany_feast'],
            )
            self.assertEqual(
                MODULE.infer_seasonal_blessing('The First Day After the Epiphany', date(year, 1, 7)),
                '',
            )

    def test_baptism_color_follows_moving_sunday(self):
        from datetime import date, timedelta

        for year, expected_day in ((2027, 10), (2028, 9)):
            epiphany = date(year, 1, 6)
            baptism = epiphany + timedelta(days=(6 - epiphany.weekday()) % 7 or 7)
            self.assertEqual(baptism.day, expected_day)
            self.assertEqual(
                MODULE.infer_liturgical_color(
                    'The First Sunday of Epiphany (The Baptism of Our Lord Jesus Christ)', baptism
                ),
                'White',
            )

    def test_epiphany_season_ends_at_moving_ash_wednesday(self):
        from datetime import timedelta

        for year in (2027, 2028):
            ash_wednesday = MODULE.easter_sunday(year) - timedelta(days=46)
            self.assertEqual(MODULE.office_season(ash_wednesday - timedelta(days=1)), 'epiphany')
            self.assertEqual(MODULE.office_season(ash_wednesday), 'lent')
