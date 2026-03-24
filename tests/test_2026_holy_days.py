import csv
from pathlib import Path
import unittest


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "acna-prayers-2026.csv"


class HolyDayDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with DATA_PATH.open(newline="", encoding="utf-8") as f:
            cls.rows = {row["Date"]: row for row in csv.DictReader(f)}

    def test_st_joseph_uses_proper_remembrance_and_collect(self) -> None:
        row = self.rows["March 19"]
        self.assertEqual(row["Liturgical Color"], "White")
        self.assertEqual(row["Observance"], "Lent / Saint Joseph")
        self.assertEqual(row["Remembrance"], "Saint Joseph")
        self.assertEqual(
            row["Special Collect"],
            "O God, who from the family of your servant David raised up Joseph to be "
            "the guardian of your incarnate Son and the husband of his virgin mother: "
            "Give us grace to imitate his uprightness of life and his obedience to "
            "your commands; through Jesus Christ our Lord, who lives and reigns with "
            "you and the Holy Spirit, one God, for ever and ever. Amen.",
        )

    def test_annunciation_uses_proper_remembrance_and_collect(self) -> None:
        row = self.rows["March 25"]
        self.assertEqual(row["Liturgical Color"], "White")
        self.assertEqual(row["Observance"], "Lent / The Annunciation")
        self.assertEqual(row["Remembrance"], "The Annunciation")
        self.assertEqual(
            row["Special Collect"],
            "Pour your grace into our hearts, O Lord, that we who have known the "
            "incarnation of your Son Jesus Christ, announced by an angel to the "
            "Virgin Mary, may by his Cross and passion be brought to the glory of "
            "his resurrection; who lives and reigns with you, in the unity of the "
            "Holy Spirit, one God, now and for ever. Amen.",
        )

    def test_saint_mark_uses_exact_primary_heading_and_no_weekday_remembrance(self) -> None:
        row = self.rows["Apr 25"]
        self.assertEqual(row["Observance"], "Saint Mark")
        self.assertEqual(row["Remembrance"], "")
        self.assertEqual(row["Special Collect"], "")


if __name__ == "__main__":
    unittest.main()
