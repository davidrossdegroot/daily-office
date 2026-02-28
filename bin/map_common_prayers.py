#!/usr/bin/env python3
"""
Prepare month rows in canonical Daily Office schema.

What this script does:
- Ensures all canonical CSV columns exist and are output in canonical order.
- Maps `Remembrance` to a `Special Collect` (common prayer text).
- Optionally fetches day-page fields from liturgical-calendar.com (observance, color, and
  available Daily Office psalms/readings/collect).
- Optionally infers `MP Opening Sentence of Scripture` from Observance.
- Optionally infers `EP Opening Sentence of Scripture` from Observance.
- Optionally applies seasonal defaults by `Observance` from a mapping CSV.
- Outputs CSV or TSV (TSV is best for Google Sheets paste).

Examples:
  python bin/map_common_prayers.py --in month.csv --out month.full.tsv --format tsv --flatten-whitespace
  python bin/map_common_prayers.py --in month.csv --out month.full.tsv --format tsv --acna-year 2026 --ignore-fetch-errors
  python bin/map_common_prayers.py --in month.csv --out month.full.csv --seasonal-map data/mappings/seasonal-defaults.csv

Seasonal blessing inference rules are based on:
- Advent
- Feast of the Nativity
- Feast of the Epiphany
- Lent (including Lent 1-5 prayers and Holy Week from Palm Sunday through Holy Saturday)
- Eastertide and Commemoration of the Faithful Departed
- Day of Pentecost
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
import re
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

CANONICAL_COLUMNS = [
    "Date",
    "Liturgical Color",
    "Observance",
    "MP Opening Sentence of Scripture",
    "Antiphon",
    "MP First Lesson",
    "MP Second Lesson",
    "Psalms (MP, 60-day)",
    "EP Opening Sentence of Scripture",
    "EP First Lesson",
    "EP Second Lesson",
    "Psalms (EP, 60-day)",
    "Seasonal Collect",
    "Special Collect",
    "Seasonal Blessing",
    "Remembrance",
]

SEASONAL_DEFAULT_COLUMNS = [
    "Liturgical Color",
    "MP Opening Sentence of Scripture",
    "Antiphon",
    "EP Opening Sentence of Scripture",
    "Seasonal Collect",
    "Seasonal Blessing",
]

COMMON_PRAYERS = {
    "common of a martyr": (
        "For the witness of your martyrs, who took up their cross and followed you "
        "even unto death, and revealed your power made perfect in human weakness."
    ),
    "common of a missionary or evangelist": (
        "For the gifts of your Holy Spirit poured out upon prophets and evangelists, "
        "to proclaim the Gospel to the ends of the earth, and to bring all peoples "
        "under the reign of Jesus Christ our Lord."
    ),
    "common of a pastor": (
        "Through Jesus Christ, the great shepherd of the sheep; in him you call "
        "faithful pastors and anoint them with your Holy Spirit, to feed your flock "
        "by Word and Sacrament, and to lead them in the way of everlasting life."
    ),
    "common of a teacher of the faith": (
        "For you have imparted gifts of wisdom and knowledge to those who teach the "
        "Gospel in word and deed, to build up the body of Christ, until we all attain "
        "to the unity of the faith and of the knowledge of the Son of God."
    ),
    "common of a monastic or religious": (
        "For calling to the consecrated life those who leave everything for the sake "
        "of your kingdom, and who show forth in this world an anticipation of the "
        "abundant life you promise in the age to come."
    ),
    "common of an ecumenist": (
        "Through your Son Jesus Christ our Lord; in him you bring us to the knowledge "
        "of your truth, and unite us by the bond of one Faith and one Baptism, that "
        "we might love one another and manifest your love to the world."
    ),
    "common of a renewer of society": (
        "For you never turn away from us, and continually send among us those who seek "
        "justice, defend the oppressed, feed the poor, and bind up the brokenhearted."
    ),
    "common of a reformer of the church": (
        "For you, the master builder, never abandon your Church, which you have built "
        "of living stones; you call your faithful servants to restore its ancient walls "
        "and reunite its broken ramparts, that it may be a holy temple of your presence."
    ),
    "common of any commemoration": (
        "For the grace and virtue manifest in [N. and all] your saints, who have been "
        "the chosen vessels of your love, and the lights of the world in their generations."
    ),
}

SEASONAL_BLESSING_TEXT = {
    "advent": (
        "Christ the Sun of Righteousness shine upon you, scatter the darkness from "
        "before your path, and make you ready to meet him when he comes in glory; "
        "and the blessing of God Almighty, the Father, the Son, and the Holy Spirit, "
        "be among you, and remain with you always. Amen."
    ),
    "nativity": (
        "Christ, who by his incarnation gathered into one things earthly and heavenly, "
        "fill you with peace and goodwill and make you partakers of the divine nature; "
        "and the blessing of God Almighty, the Father, the Son, and the Holy Spirit, "
        "be among you, and remain with you always. Amen."
    ),
    "epiphany_feast": (
        "Christ our Lord, to whom kings bowed down in worship and offered gifts, "
        "reveal to you his glory and pour upon you the riches of his grace; and the "
        "blessing of God Almighty, the Father, the Son, and the Holy Spirit, be among "
        "you, and remain with you always. Amen."
    ),
    "lent_note": (
        "In Lent, in place of a seasonal blessing, a solemn Prayer over the People is used."
    ),
    "lent_1": (
        "Grant, Almighty God, that your people may recognize their weakness and put "
        "their whole trust in your strength, so that they may rejoice for ever in the "
        "protection of your loving providence; through Christ our Lord. Amen."
    ),
    "lent_2": (
        "Keep this your family, Lord, with your never-failing mercy, that relying "
        "solely on the help of your heavenly grace, they may be upheld by your divine "
        "protection; through Christ our Lord. Amen."
    ),
    "lent_3": (
        "Look mercifully on this your family, Almighty God, that by your great goodness "
        "they may be governed and preserved evermore; through Christ our Lord. Amen."
    ),
    "lent_4": (
        "Look down in mercy, Lord, on your people who kneel before you; and grant that "
        "those whom you have nourished by your Word and Sacraments may bring forth "
        "fruit worthy of repentance; through Christ our Lord. Amen."
    ),
    "lent_5": (
        "Look with compassion, O Lord, upon this your people; that, continuing to "
        "rightly observe this holy season, they may learn to know you more fully, and "
        "to serve you with a more perfect will; through Christ our Lord. Amen."
    ),
    "holy_week": (
        "Almighty God, we beseech you graciously to behold this your family, for whom "
        "our Lord Jesus Christ was willing to be betrayed and given into the hands of "
        "sinners, and to suffer death upon the Cross; who now lives and reigns with you "
        "and the Holy Spirit, one God, for ever and ever. Amen."
    ),
    "eastertide": (
        "The God of peace, who brought again from the dead our Lord Jesus Christ, the "
        "great Shepherd of the sheep, by the blood of the everlasting covenant, make "
        "you perfect in every good work to do his will, working in you that which is "
        "well-pleasing in his sight; and the blessing of God Almighty, the Father, the "
        "Son, and the Holy Spirit, be among you, and remain with you always. Amen."
    ),
    "pentecost": (
        "The Spirit of truth lead you into all truth, giving you grace to confess that "
        "Jesus Christ is Lord, and to proclaim the wonderful works of God; and the "
        "blessing of God Almighty, the Father, the Son, and the Holy Spirit, be among "
        "you, and remain with you always. Amen."
    ),
}

MP_OPENING_SENTENCES = {
    "advent": "In the wilderness prepare the way of the Lord; make straight in the desert a highway for our God. isaiah 40:3",
    "christmas": "Fear not, for behold, I bring you good news of great joy that will be for all the people. For unto you is born this day in the city of David a Savior, who is Christ the Lord. luke 2:10-11",
    "epiphany": "EPIPHANY_PLACEHOLDER",
    "lent": "Repent, for the kingdom of heaven is at hand. matthew 3:2",
    "holy_week": "Is it nothing to you, all you who pass by? Look and see if there is any sorrow like my sorrow, which was brought upon me, which the Lord inflicted on the day of his fierce anger. lamentations 1:12",
    "easter": "If then you have been raised with Christ, seek the things that are above, where Christ is, seated at the right hand of God. colossians 3:1",
    "ascension": "Since then we have a great high priest who has passed through the heavens, Jesus, the Son of God, let us hold fast our confession. Let us then with confidence draw near to the throne of grace, that we may receive mercy and find grace to help in time of need. hebrews 4:14, 16",
    "pentecost": "You will receive power when the Holy Spirit has come upon you, and you will be my witnesses in Jerusalem and in all Judea and Samaria, and to the end of the earth. acts 1:8",
    "trinity_sunday": "Holy, holy, holy, is the Lord God Almighty, who was and is and is to come! revelation 4:8",
    "thanksgiving": "Honor the Lord with your wealth and with the firstfruits of all your produce; then your barns will be filled with plenty, and your vats will be bursting with wine. proverbs 3:9-10",
    "at_any_time": "The Lord is in his holy temple; let all the earth keep silence before him. habakkuk 2:20",
}

MP_OPENING_ALTERNATES = {
    "lent": [
        "Turn your face from my sins, and blot out all my misdeeds. psalm 51:9",
        "If anyone would come after me, let him deny himself and take up his cross and follow me. mark 8:34",
    ],
    "at_any_time": [
        "O send out your light and your truth, that they may lead me, and bring me to your holy hill, and to your dwelling. psalm 43:3",
        "Thus says the One who is high and lifted up, who inhabits eternity, whose name is Holy: \"I dwell in the high and holy place, and also with him who is of a contrite and lowly spirit, to revive the spirit of the lowly, and to revive the heart of the contrite.\" isaiah 57:15",
        "The hour is coming, and is now here, when the true worshipers will worship the Father in spirit and truth, for the Father is seeking such people to worship him. john 4:23",
    ],
}

EP_OPENING_SENTENCES = {
    "advent": "Therefore stay awake, for you do not know when the master of the house will come, in the evening, or at midnight, or when the rooster crows, or in the morning, lest he come suddenly and find you asleep. mark 13:35-36",
    "christmas": "Behold, the dwelling place of God is with man. He will dwell with them, and they will be his people, and God himself will be with them as their God. revelation 21:3",
    "epiphany": "Nations shall come to your light, and kings to the brightness of your rising. isaiah 60:3",
    "lent": "If we say we have no sin, we deceive ourselves, and the truth is not in us. If we confess our sins, he is faithful and just to forgive us our sins and to cleanse us from all unrighteousness. 1 john 1:8-9",
    "holy_week": "All we like sheep have gone astray; we have turned every one to his own way; and the Lord has laid on him the iniquity of us all. isaiah 53:6",
    "easter": "Thanks be to God, who gives us the victory through our Lord Jesus Christ. 1 corinthians 15:57",
    "ascension": "For Christ has entered, not into holy places made with hands, which are copies of the true things, but into heaven itself, now to appear in the presence of God on our behalf. hebrews 9:24",
    "pentecost": "The Spirit and the Bride say, \"Come.\" And let the one who hears say, \"Come.\" And let the one who is thirsty come; let the one who desires take the water of life without price. revelation 22:17",
    "trinity_sunday": "Holy, holy, holy is the Lord of Hosts; the whole earth is full of his glory! isaiah 6:3",
    "thanksgiving": "The Lord by wisdom founded the earth; by understanding he established the heavens; by his knowledge the deeps broke open, and the clouds drop down the dew. proverbs 3:19-20",
    "at_any_time": "O worship the Lord in the beauty of holiness; let the whole earth stand in awe of him. psalm 96:9",
}

EP_OPENING_ALTERNATES = {
    "lent": [
        "For I acknowledge my faults, and my sin is ever before me. psalm 51:3",
        "To the Lord our God belong mercy and forgiveness, for we have rebelled against him. daniel 9:9",
    ],
    "pentecost": [
        "There is a river whose streams make glad the city of God, the holy dwelling place of the Most High. psalm 46:4",
    ],
    "at_any_time": [
        "I will thank the Lord for giving me counsel; my heart also chastens me in the night season. I have set the Lord always before me; he is at my right hand; therefore I shall not fall. psalm 16:8-9",
    ],
}

SEASONAL_ANTIPHONS = {
    "advent": "Our King and Savior now draws near: * O come, let us adore him.",
    "christmas": "Alleluia. Unto us a child is born: * O come, let us adore him. Alleluia.",
    "epiphany": "The Lord has shown forth his glory: * O come, let us adore him.",
    "presentation_annunciation": "The Word was made flesh and dwelt among us: * O come, let us adore him.",
    "lent": "The Lord is full of compassion and mercy: * O come, let us adore him.",
    "easter_until_ascension": "Alleluia. The Lord is risen indeed: * O come, let us adore him. Alleluia.",
    "ascension_until_pentecost": "Alleluia. Christ the Lord has ascended into heaven: * O come, let us adore him. Alleluia.",
    "day_of_pentecost": "Alleluia. The Spirit of the Lord renews the face of the earth: * O come, let us adore him. Alleluia.",
    "trinity_sunday": "Father, Son, and Holy Spirit, one God: * O come, let us adore him.",
    "all_saints_major": "The Lord is glorious in his saints: * O come, let us adore him.",
}


class LiturgicalDayPageParser(HTMLParser):
    """Extract basic heading/content blocks from a liturgical calendar day page."""

    RELEVANT_TAGS = {"h2", "h3", "h4", "h5", "p", "li"}
    SKIP_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.capture_stack: list[tuple[str, list[str]]] = []
        self.blocks: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth > 0:
            return
        if tag in self.RELEVANT_TAGS:
            self.capture_stack.append((tag, []))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
            return
        if self.skip_depth > 0:
            return
        if self.capture_stack and tag == self.capture_stack[-1][0]:
            close_tag, parts = self.capture_stack.pop()
            text = clean("".join(parts))
            if text:
                self.blocks.append((close_tag, text))

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return
        if self.capture_stack:
            self.capture_stack[-1][1].append(data)


class LiturgicalDayOfficeParser(HTMLParser):
    """Extract office-related headings/content blocks from a day page."""

    RELEVANT_TAGS = {"h2", "h3", "h4", "h5", "h6", "p", "li", "th", "td"}
    SKIP_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.capture_stack: list[tuple[str, list[str]]] = []
        self.blocks: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth > 0:
            return
        if tag in self.RELEVANT_TAGS:
            self.capture_stack.append((tag, []))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
            return
        if self.skip_depth > 0:
            return
        if self.capture_stack and tag == self.capture_stack[-1][0]:
            close_tag, parts = self.capture_stack.pop()
            text = clean("".join(parts))
            if text:
                self.blocks.append((close_tag, text))

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return
        if self.capture_stack:
            self.capture_stack[-1][1].append(data)


def clean(value: str | None) -> str:
    return (value or "").strip()


def is_heading_tag(tag: str) -> bool:
    return bool(re.fullmatch(r"h[1-6]", clean(tag).lower()))


def flatten_whitespace(value: str) -> str:
    return " ".join(value.split())


def parse_month_day(date_str: str, year: int) -> datetime:
    for fmt in ("%b %d", "%B %d"):
        try:
            dt = datetime.strptime(f"{clean(date_str)} {year}", f"{fmt} %Y")
            return dt
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse Date='{date_str}'. Expected like 'Mar 17' or 'March 17'."
    )


def parse_row_date_for_inference(date_str: str, fallback_year: int | None) -> date | None:
    """Parse a row date with optional year fallback for seasonal inference logic."""
    text = clean(date_str)
    if not text:
        return None

    dated_formats = ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y")
    for fmt in dated_formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    if fallback_year is None:
        return None

    for fmt in ("%b %d", "%B %d"):
        try:
            return datetime.strptime(f"{text} {fallback_year}", f"{fmt} %Y").date()
        except ValueError:
            continue
    return None


def infer_year_from_filename(path: Path) -> int | None:
    """Extract a 4-digit year from a filename (for example acna-prayers-2026.csv)."""
    match = re.search(r"(?:^|[^0-9])((?:19|20)\d{2})(?:[^0-9]|$)", path.name)
    if not match:
        return None
    return int(match.group(1))


def easter_sunday(year: int) -> date:
    """Return Gregorian Easter Sunday for the provided year."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def is_holy_week_span(current_date: date | None) -> bool:
    """Palm Sunday through Holy Saturday, inclusive."""
    if current_date is None:
        return False
    easter = easter_sunday(current_date.year)
    palm_sunday = easter - timedelta(days=7)
    return palm_sunday <= current_date < easter


def observance_is_holy_week_span(observance: str) -> bool:
    """Text fallback for Holy Week span detection when date is unavailable."""
    text = clean(observance).lower()
    if not text:
        return False

    if "holy week" in text:
        return True

    tokens = (
        "palm sunday",
        "maundy thursday",
        "maunday thursday",
        "good friday",
        "holy saturday",
        "easter eve",
    )
    return any(token in text for token in tokens)


def lent_rotation_index(current_date: date | None) -> int | None:
    """
    Return zero-based day index from Ash Wednesday through the Saturday before Palm Sunday.
    """
    if current_date is None:
        return None
    easter = easter_sunday(current_date.year)
    ash_wednesday = easter - timedelta(days=46)
    palm_sunday = easter - timedelta(days=7)
    if current_date < ash_wednesday or current_date >= palm_sunday:
        return None
    return (current_date - ash_wednesday).days


def normalize_liturgical_color(raw_color: str) -> str:
    """
    Normalize site color labels into canonical dataset values.
    Canonical values are White, Green, Purple, Pink, Red.
    """
    text = clean(raw_color).lower()
    if not text:
        return ""

    # Choose the earliest matching known color word in the source text.
    candidates: list[tuple[int, str]] = []
    aliases = {
        "White": ("white", "gold"),
        "Green": ("green",),
        "Purple": ("purple", "violet"),
        "Pink": ("pink", "rose"),
        "Red": ("red",),
    }
    for canonical, words in aliases.items():
        for word in words:
            idx = text.find(word)
            if idx != -1:
                candidates.append((idx, canonical))
                break
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # Fallback: preserve as title case.
    return clean(raw_color).title()


def extract_observance_color_remembrance(html: str) -> tuple[str, str, str]:
    """
    Parse one day page and return:
    (primary observance, primary liturgical color, remembrance/secondary observance)
    """
    parser = LiturgicalDayPageParser()
    parser.feed(html)

    observances = [text for tag, text in parser.blocks if tag == "h2"]
    primary_observance = observances[0] if observances else ""
    remembrance = " / ".join(observances[1:]) if len(observances) > 1 else ""

    colors: list[str] = []
    for idx, (tag, text) in enumerate(parser.blocks):
        if is_heading_tag(tag) and text.lower().startswith("liturgical colors"):
            for _, next_text in parser.blocks[idx + 1 :]:
                if next_text:
                    colors.append(next_text)
                    break

    primary_color = normalize_liturgical_color(colors[0]) if colors else ""
    return (primary_observance, primary_color, remembrance)


def extract_primary_collect(html: str) -> str:
    """
    Parse one day page and return the first collect text for the primary observance.
    """
    parser = LiturgicalDayPageParser()
    parser.feed(html)

    h2_count = 0
    within_primary_observance = False
    awaiting_collect_text = False
    for tag, text in parser.blocks:
        if tag == "h2":
            h2_count += 1
            within_primary_observance = h2_count == 1
            awaiting_collect_text = False
            continue

        if not within_primary_observance:
            continue

        if is_heading_tag(tag):
            heading = clean(text).lower()
            if heading.startswith("collect"):
                awaiting_collect_text = True
                continue
            if awaiting_collect_text:
                # Another heading started before collect content.
                awaiting_collect_text = False
            continue

        if awaiting_collect_text and tag in {"p", "li"}:
            return clean(text)

    return ""


def classify_office_label(text: str) -> str:
    """Classify a field label from office sections."""
    token = re.sub(r"[^a-z0-9]+", "", clean(text).lower())
    if not token:
        return ""

    if "psalm" in token or "psalter" in token:
        return "psalms"

    if token in {"lessoni", "lesson1", "otlesson", "first"}:
        return "first_lesson"
    if token in {"lessonii", "lesson2", "ntlesson", "second"}:
        return "second_lesson"

    if "first" in token and ("lesson" in token or "reading" in token):
        return "first_lesson"
    if "second" in token and ("lesson" in token or "reading" in token):
        return "second_lesson"

    return ""


def parse_office_line(line: str) -> tuple[str, str]:
    """
    Parse one office content line into (field_kind, value).

    Field kinds:
    - psalms
    - first_lesson
    - second_lesson
    """
    raw = clean(line)
    if not raw:
        return ("", "")

    if ":" in raw:
        label, value = raw.split(":", 1)
        kind = classify_office_label(label)
        if kind and clean(value):
            return (kind, clean(value))

    dash_match = re.match(r"^(?P<label>.+?)\s+[-\u2013\u2014]\s+(?P<value>.+)$", raw)
    if dash_match:
        kind = classify_office_label(dash_match.group("label"))
        value = clean(dash_match.group("value"))
        if kind and value:
            return (kind, value)

    lower = raw.lower()
    prefix_map = [
        ("first lesson", "first_lesson"),
        ("first reading", "first_lesson"),
        ("lesson i", "first_lesson"),
        ("lesson 1", "first_lesson"),
        ("second lesson", "second_lesson"),
        ("second reading", "second_lesson"),
        ("lesson ii", "second_lesson"),
        ("lesson 2", "second_lesson"),
        ("psalms", "psalms"),
        ("psalm", "psalms"),
    ]
    for prefix, kind in prefix_map:
        if not lower.startswith(prefix):
            continue
        if len(lower) > len(prefix):
            next_char = lower[len(prefix)]
            if next_char not in {" ", ":", "-", "\u2013", "\u2014", "("}:
                continue
            value = clean(raw[len(prefix) :]).lstrip(" :-\u2013\u2014")
            if not value:
                continue
            # Keep label-only forms (for example "(60 day cycle)") for pairwise fallback.
            if value.startswith("(") and value.endswith(")"):
                continue
            return (kind, value)

    return ("", "")


def parse_office_entries(entries: list[str]) -> dict[str, str]:
    """Parse office section entries into psalms + first/second lesson values."""
    result = {
        "psalms": "",
        "first_lesson": "",
        "second_lesson": "",
    }
    normalized_entries = [clean(entry) for entry in entries if clean(entry)]

    for entry in normalized_entries:
        for line in [clean(part) for part in entry.splitlines() if clean(part)]:
            kind, value = parse_office_line(line)
            if kind and value and not result[kind]:
                result[kind] = value

    # Fallback for table-like label/value rows split across adjacent cells.
    for idx in range(len(normalized_entries) - 1):
        label_kind = classify_office_label(normalized_entries[idx])
        if not label_kind or result[label_kind]:
            continue
        value = normalized_entries[idx + 1]
        if not classify_office_label(value):
            result[label_kind] = value

    if all(result.values()):
        return result

    def looks_like_psalm_entry(value: str) -> bool:
        lower = clean(value).lower()
        return lower.startswith("psalm ") or lower.startswith("psalms ")

    def looks_like_scripture_reference(value: str) -> bool:
        text = clean(value)
        if not text:
            return False
        return bool(re.match(r"^(?:[1-3]\s*)?[A-Za-z][A-Za-z .'-]*\d", text))

    unlabeled_candidates: list[str] = []
    for entry in normalized_entries:
        if classify_office_label(entry):
            continue
        kind, _ = parse_office_line(entry)
        if kind:
            continue
        if looks_like_psalm_entry(entry) or looks_like_scripture_reference(entry):
            unlabeled_candidates.append(entry)

    if unlabeled_candidates:
        if not result["psalms"]:
            psalm_candidates = [value for value in unlabeled_candidates if looks_like_psalm_entry(value)]
            if psalm_candidates:
                result["psalms"] = psalm_candidates[0]

        reading_candidates = [
            value for value in unlabeled_candidates if not looks_like_psalm_entry(value)
        ]
        if reading_candidates and not result["first_lesson"]:
            result["first_lesson"] = reading_candidates[0]
        if len(reading_candidates) > 1 and not result["second_lesson"]:
            result["second_lesson"] = reading_candidates[1]

    return result


def extract_office_readings(html: str) -> dict[str, str]:
    """
    Parse one day page and return available Daily Office fields from MP/EP sections.
    """
    parser = LiturgicalDayOfficeParser()
    parser.feed(html)

    section_entries = {
        "mp": [],
        "ep": [],
    }
    current_section = ""
    for tag, text in parser.blocks:
        if is_heading_tag(tag):
            heading = clean(text).lower()
            if "morning prayer" in heading:
                current_section = "mp"
                continue
            if "evening prayer" in heading:
                current_section = "ep"
                continue
            if current_section:
                # Keep subsection headings (for example "60 day cycle") within section capture.
                if not any(token in heading for token in ("cycle", "psalm", "lesson", "reading")):
                    current_section = ""
                    continue
        if current_section in section_entries:
            section_entries[current_section].append(text)

    mp_fields = parse_office_entries(section_entries["mp"])
    ep_fields = parse_office_entries(section_entries["ep"])

    return {
        "mp_first_lesson": mp_fields["first_lesson"],
        "mp_second_lesson": mp_fields["second_lesson"],
        "mp_psalms": mp_fields["psalms"],
        "ep_first_lesson": ep_fields["first_lesson"],
        "ep_second_lesson": ep_fields["second_lesson"],
        "ep_psalms": ep_fields["psalms"],
    }


def fetch_calendar_day(
    *,
    base_url: str,
    province: str,
    year: int,
    month: int,
    day: int,
    timeout_sec: float = 20.0,
) -> dict[str, str]:
    """
    Fetch one day from liturgical-calendar.com and parse day-page fields.
    """
    url = f"{base_url.rstrip('/')}/{province}/{year:04d}-{month:02d}-{day:02d}"
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=timeout_sec) as resp:
        content_type = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
        html = resp.read().decode(charset, errors="replace")
    observance, color, remembrance = extract_observance_color_remembrance(html)
    seasonal_collect = extract_primary_collect(html)
    office_readings = extract_office_readings(html)
    return {
        "observance": observance,
        "liturgical_color": color,
        "remembrance": remembrance,
        "seasonal_collect": seasonal_collect,
        **office_readings,
    }


def infer_common_type(remembrance: str, observance: str) -> str:
    """Infer common prayer category from remembrance/observance text."""
    text = f"{remembrance} {observance}".strip().lower()
    if not text:
        return ""

    # Priority matters for multi-role titles (for example "bishop and missionary").
    if "martyr" in text:
        return "common of a martyr"

    missionary_hints = (
        "missionary",
        "apostle",
        "evangelist",
        "illuminator",
    )
    if any(hint in text for hint in missionary_hints):
        return "common of a missionary or evangelist"

    if "teacher of the faith" in text or "doctor of the church" in text:
        return "common of a teacher of the faith"

    if "reformer of the church" in text or "reformer" in text:
        return "common of a reformer of the church"

    if "ecumen" in text:
        return "common of an ecumenist"

    monastic_hints = ("abbot", "abbess", "monastic", "religious")
    if any(hint in text for hint in monastic_hints):
        return "common of a monastic or religious"

    renewer_hints = ("justice", "renewer", "social", "abolition")
    if any(hint in text for hint in renewer_hints):
        return "common of a renewer of society"

    pastor_hints = ("bishop", "priest", "pastor", "archbishop", "deacon")
    if any(hint in text for hint in pastor_hints):
        return "common of a pastor"

    return "common of any commemoration"


def infer_seasonal_blessing(observance: str, current_date: date | None = None) -> str:
    """
    Infer seasonal blessing/prayer-over-the-people from observance text.
    """
    text = clean(observance).lower()

    if is_holy_week_span(current_date) or observance_is_holy_week_span(text):
        return SEASONAL_BLESSING_TEXT["holy_week"]

    if not text:
        return ""

    # Specific feast/day cases first.
    if "day of pentecost" in text or text == "pentecost":
        return SEASONAL_BLESSING_TEXT["pentecost"]

    if "nativity" in text or "christmas day" in text:
        return SEASONAL_BLESSING_TEXT["nativity"]

    # Feast of Epiphany only, not the whole Epiphany season.
    if text in {"epiphany", "the epiphany"} or "feast of the epiphany" in text:
        return SEASONAL_BLESSING_TEXT["epiphany_feast"]

    # Lent prayers over the people: rotate daily when date context is available.
    if "lent" in text or "ash wednesday" in text or "penitential" in text:
        idx = lent_rotation_index(current_date)
        if idx is not None:
            option_keys = ("lent_1", "lent_2", "lent_3", "lent_4", "lent_5")
            return SEASONAL_BLESSING_TEXT[option_keys[idx % len(option_keys)]]

    # Fallback for textual week labels when date context is unavailable.
    if "week of lent" in text:
        week_patterns = [
            (r"\b(first|1st)\b", "lent_1"),
            (r"\b(second|2nd)\b", "lent_2"),
            (r"\b(third|3rd)\b", "lent_3"),
            (r"\b(fourth|4th)\b", "lent_4"),
            (r"\b(fifth|5th)\b", "lent_5"),
        ]
        for pat, key in week_patterns:
            if re.search(pat, text):
                return SEASONAL_BLESSING_TEXT[key]
        return SEASONAL_BLESSING_TEXT["lent_note"]

    if "lent" in text:
        return SEASONAL_BLESSING_TEXT["lent_note"]

    if "advent" in text:
        return SEASONAL_BLESSING_TEXT["advent"]

    if "faithful departed" in text:
        return SEASONAL_BLESSING_TEXT["eastertide"]

    if "easter" in text or "eastertide" in text:
        return SEASONAL_BLESSING_TEXT["eastertide"]

    return ""


def infer_mp_opening_sentence(observance: str, current_date: date | None = None) -> str:
    """Infer MP Opening Sentence of Scripture from observance text."""
    text = clean(observance).lower()

    if is_holy_week_span(current_date) or observance_is_holy_week_span(text):
        return MP_OPENING_SENTENCES["holy_week"]

    if not text:
        return MP_OPENING_SENTENCES["at_any_time"]

    if "day of pentecost" in text or text == "pentecost":
        return MP_OPENING_SENTENCES["pentecost"]

    if "trinity sunday" in text:
        return MP_OPENING_SENTENCES["trinity_sunday"]

    if "ascension" in text:
        return MP_OPENING_SENTENCES["ascension"]

    if "advent" in text:
        return MP_OPENING_SENTENCES["advent"]

    if "nativity" in text or "christmas" in text or "christmastide" in text:
        return MP_OPENING_SENTENCES["christmas"]

    if "epiphany" in text:
        return MP_OPENING_SENTENCES["epiphany"]

    if "lent" in text or "ash wednesday" in text or "penitential" in text:
        idx = lent_rotation_index(current_date)
        options = [MP_OPENING_SENTENCES["lent"], *MP_OPENING_ALTERNATES.get("lent", [])]
        if idx is None:
            return options[0]
        return options[idx % len(options)]

    if "easter" in text or "eastertide" in text:
        return MP_OPENING_SENTENCES["easter"]

    if "thanksgiving" in text:
        return MP_OPENING_SENTENCES["thanksgiving"]

    return MP_OPENING_SENTENCES["at_any_time"]


def infer_ep_opening_sentence(observance: str, current_date: date | None = None) -> str:
    """Infer EP Opening Sentence of Scripture from observance text."""
    text = clean(observance).lower()

    if is_holy_week_span(current_date) or observance_is_holy_week_span(text):
        return EP_OPENING_SENTENCES["holy_week"]

    if not text:
        return EP_OPENING_SENTENCES["at_any_time"]

    if "day of pentecost" in text or text == "pentecost":
        return EP_OPENING_SENTENCES["pentecost"]

    if "trinity sunday" in text:
        return EP_OPENING_SENTENCES["trinity_sunday"]

    if "ascension" in text:
        return EP_OPENING_SENTENCES["ascension"]

    if "advent" in text:
        return EP_OPENING_SENTENCES["advent"]

    if "nativity" in text or "christmas" in text or "christmastide" in text:
        return EP_OPENING_SENTENCES["christmas"]

    if "epiphany" in text:
        return EP_OPENING_SENTENCES["epiphany"]

    if "lent" in text or "ash wednesday" in text or "penitential" in text:
        idx = lent_rotation_index(current_date)
        options = [EP_OPENING_SENTENCES["lent"], *EP_OPENING_ALTERNATES.get("lent", [])]
        if idx is None:
            return options[0]
        return options[idx % len(options)]

    if "easter" in text or "eastertide" in text:
        return EP_OPENING_SENTENCES["easter"]

    if "thanksgiving" in text:
        return EP_OPENING_SENTENCES["thanksgiving"]

    return EP_OPENING_SENTENCES["at_any_time"]


def infer_antiphon(observance: str, remembrance: str) -> str:
    """Infer seasonal antiphon from observance/remembrance text."""
    observance_text = clean(observance).lower()
    remembrance_text = clean(remembrance).lower()
    text = f"{observance_text} {remembrance_text}".strip()
    if not text:
        return ""

    if "presentation" in text or "annunciation" in text:
        return SEASONAL_ANTIPHONS["presentation_annunciation"]

    if "transfiguration" in text:
        return SEASONAL_ANTIPHONS["epiphany"]

    if "day of pentecost" in text or observance_text == "pentecost":
        return SEASONAL_ANTIPHONS["day_of_pentecost"]

    if "trinity sunday" in text:
        return SEASONAL_ANTIPHONS["trinity_sunday"]

    if "ascension" in text:
        return SEASONAL_ANTIPHONS["ascension_until_pentecost"]

    if "easter" in text or "eastertide" in text:
        return SEASONAL_ANTIPHONS["easter_until_ascension"]

    if (
        "lent" in text
        or "ash wednesday" in text
        or "holy week" in text
        or "palm sunday" in text
        or "maundy thursday" in text
    ):
        return SEASONAL_ANTIPHONS["lent"]

    if "nativity" in text or "christmas" in text or "christmastide" in text:
        return SEASONAL_ANTIPHONS["christmas"]

    if "advent" in text:
        return SEASONAL_ANTIPHONS["advent"]

    if "epiphany" in text:
        return SEASONAL_ANTIPHONS["epiphany"]

    if "all saints" in text:
        return SEASONAL_ANTIPHONS["all_saints_major"]

    major_saint_hints = (
        "apostle",
        "evangelist",
        "martyr",
        "bishop",
        "priest",
        "missionary",
        "teacher of the faith",
    )
    if any(hint in remembrance_text for hint in major_saint_hints):
        return SEASONAL_ANTIPHONS["all_saints_major"]

    return ""


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"No header row found in {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"No data rows found in {path}")
    return rows


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]], delimiter: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def ensure_canonical_schema(row: dict[str, str]) -> dict[str, str]:
    # Ensure all canonical keys exist and values are strings.
    for col in CANONICAL_COLUMNS:
        row.setdefault(col, "")
    for key, value in list(row.items()):
        if value is None:
            row[key] = ""
        elif not isinstance(value, str):
            row[key] = str(value)
    return row


def load_seasonal_map(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"No header row found in seasonal map: {path}")
        if "Observance" not in reader.fieldnames:
            raise ValueError("Seasonal map must include an 'Observance' column")

        result: dict[str, dict[str, str]] = {}
        for raw in reader:
            observance = clean(raw.get("Observance"))
            if not observance:
                continue
            key = observance.lower()
            result[key] = {
                col: clean(raw.get(col))
                for col in SEASONAL_DEFAULT_COLUMNS
            }
    return result


def apply_seasonal_defaults(
    row: dict[str, str],
    seasonal_map: dict[str, dict[str, str]],
    mode: str,
) -> None:
    observance = clean(row.get("Observance"))
    if not observance:
        return

    defaults = seasonal_map.get(observance.lower())
    if not defaults:
        return

    for col, value in defaults.items():
        if not value:
            continue
        if mode == "overwrite" or not clean(row.get(col)):
            row[col] = value


def apply_calendar_day_data(
    row: dict[str, str],
    *,
    year: int,
    base_url: str,
    province: str,
    mode: str,
    fill_remembrance: bool,
) -> None:
    dt = parse_month_day(clean(row.get("Date")), year)
    calendar_data = fetch_calendar_day(
        base_url=base_url,
        province=province,
        year=dt.year,
        month=dt.month,
        day=dt.day,
    )
    observance = clean(calendar_data.get("observance"))
    color = clean(calendar_data.get("liturgical_color"))
    remembrance = clean(calendar_data.get("remembrance"))
    if observance and (mode == "overwrite" or not clean(row.get("Observance"))):
        row["Observance"] = observance
    if color and (mode == "overwrite" or not clean(row.get("Liturgical Color"))):
        row["Liturgical Color"] = color
    if fill_remembrance and remembrance and (
        mode == "overwrite" or not clean(row.get("Remembrance"))
    ):
        row["Remembrance"] = remembrance

    office_field_map = [
        ("mp_first_lesson", "MP First Lesson"),
        ("mp_second_lesson", "MP Second Lesson"),
        ("mp_psalms", "Psalms (MP, 60-day)"),
        ("ep_first_lesson", "EP First Lesson"),
        ("ep_second_lesson", "EP Second Lesson"),
        ("ep_psalms", "Psalms (EP, 60-day)"),
        ("seasonal_collect", "Seasonal Collect"),
    ]
    for source_key, target_col in office_field_map:
        value = clean(calendar_data.get(source_key))
        if value and (mode == "overwrite" or not clean(row.get(target_col))):
            row[target_col] = value


def process(
    input_path: Path,
    output_path: Path,
    fmt: str,
    flatten: bool,
    acna_year: int | None,
    acna_base_url: str,
    acna_province: str,
    calendar_mode: str,
    fill_remembrance_from_calendar: bool,
    ignore_fetch_errors: bool,
    seasonal_map_path: Path | None,
    seasonal_mode: str,
    mp_opening_mode: str,
    ep_opening_mode: str,
    antiphon_mode: str,
    seasonal_blessing_mode: str,
    special_collect_mode: str,
    include_common_type: bool,
) -> None:
    rows = read_rows(input_path)

    if "Date" not in rows[0]:
        raise ValueError("Input CSV must contain a 'Date' column")
    if "Remembrance" not in rows[0]:
        raise ValueError("Input CSV must contain a 'Remembrance' column")

    seasonal_map: dict[str, dict[str, str]] = {}
    if seasonal_map_path is not None:
        seasonal_map = load_seasonal_map(seasonal_map_path)

    inference_year = acna_year if acna_year is not None else infer_year_from_filename(input_path)

    for row in rows:
        ensure_canonical_schema(row)
        row_date = parse_row_date_for_inference(clean(row.get("Date")), inference_year)

        if acna_year is not None:
            try:
                apply_calendar_day_data(
                    row,
                    year=acna_year,
                    base_url=acna_base_url,
                    province=acna_province,
                    mode=calendar_mode,
                    fill_remembrance=fill_remembrance_from_calendar,
                )
            except (ValueError, HTTPError, URLError, TimeoutError) as exc:
                message = f"Calendar fetch warning for Date={row.get('Date', '')}: {exc}"
                if ignore_fetch_errors:
                    print(message)
                else:
                    raise RuntimeError(message) from exc

        if seasonal_map:
            apply_seasonal_defaults(row, seasonal_map, mode=seasonal_mode)

        if mp_opening_mode != "off":
            inferred_mp_opening = infer_mp_opening_sentence(
                clean(row.get("Observance")),
                current_date=row_date,
            )
            if inferred_mp_opening:
                if mp_opening_mode == "overwrite" or not clean(row.get("MP Opening Sentence of Scripture")):
                    row["MP Opening Sentence of Scripture"] = inferred_mp_opening

        if ep_opening_mode != "off":
            inferred_ep_opening = infer_ep_opening_sentence(
                clean(row.get("Observance")),
                current_date=row_date,
            )
            if inferred_ep_opening:
                if ep_opening_mode == "overwrite" or not clean(row.get("EP Opening Sentence of Scripture")):
                    row["EP Opening Sentence of Scripture"] = inferred_ep_opening

        if antiphon_mode != "off":
            inferred_antiphon = infer_antiphon(
                clean(row.get("Observance")),
                clean(row.get("Remembrance")),
            )
            if inferred_antiphon:
                if antiphon_mode == "overwrite" or not clean(row.get("Antiphon")):
                    row["Antiphon"] = inferred_antiphon

        if seasonal_blessing_mode != "off":
            inferred_blessing = infer_seasonal_blessing(
                clean(row.get("Observance")),
                current_date=row_date,
            )
            if inferred_blessing:
                if seasonal_blessing_mode == "overwrite" or not clean(row.get("Seasonal Blessing")):
                    row["Seasonal Blessing"] = inferred_blessing

        remembrance = clean(row.get("Remembrance"))
        observance = clean(row.get("Observance"))
        if remembrance:
            common_type = infer_common_type(remembrance, observance)
            common_prayer = COMMON_PRAYERS.get(common_type, "")

            if include_common_type:
                row["Common Type"] = common_type

            if special_collect_mode != "off":
                if special_collect_mode == "overwrite" or not clean(row.get("Special Collect")):
                    row["Special Collect"] = common_prayer
        elif include_common_type:
            row["Common Type"] = ""

        if flatten:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = flatten_whitespace(value)

    fieldnames = list(CANONICAL_COLUMNS)
    if include_common_type:
        fieldnames.append("Common Type")

    delimiter = "\t" if fmt == "tsv" else ","
    write_rows(output_path, fieldnames, rows, delimiter=delimiter)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare month rows in canonical Daily Office schema."
    )
    parser.add_argument("--in", dest="input_csv", required=True, help="Input CSV path")
    parser.add_argument("--out", dest="output_csv", required=True, help="Output CSV/TSV path")
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=("csv", "tsv"),
        default="csv",
        help="Output format (default: csv). Use tsv for easier Google Sheets paste.",
    )
    parser.add_argument(
        "--flatten-whitespace",
        action="store_true",
        help="Collapse embedded newlines/multiple spaces inside fields.",
    )
    parser.add_argument(
        "--acna-year",
        type=int,
        help=(
            "If set, fetch day-page fields from liturgical-calendar.com for this year "
            "(Observance, Liturgical Color, Seasonal Collect, and available MP/EP psalms/readings)."
        ),
    )
    parser.add_argument(
        "--acna-base-url",
        default="https://liturgical-calendar.com/en",
        help="Base URL for liturgical calendar site.",
    )
    parser.add_argument(
        "--acna-province",
        default="ACNA2019",
        help="Calendar province segment in URL (default: ACNA2019).",
    )
    parser.add_argument(
        "--calendar-mode",
        choices=("fill", "overwrite"),
        default="fill",
        help="When fetching calendar fields: fill empty values or overwrite existing values.",
    )
    parser.add_argument(
        "--fill-remembrance-from-calendar",
        action="store_true",
        help="Also fill Remembrance from secondary observance headings on day pages.",
    )
    parser.add_argument(
        "--ignore-fetch-errors",
        action="store_true",
        help="Continue if a day page cannot be fetched; otherwise fail fast.",
    )
    parser.add_argument(
        "--seasonal-map",
        help="Optional CSV mapping by Observance for liturgical defaults.",
    )
    parser.add_argument(
        "--seasonal-mode",
        choices=("fill", "overwrite"),
        default="fill",
        help="When applying seasonal map: fill empty fields or overwrite existing values.",
    )
    parser.add_argument(
        "--mp-opening-mode",
        choices=("fill", "overwrite", "off"),
        default="fill",
        help="Infer MP Opening Sentence from Observance.",
    )
    parser.add_argument(
        "--ep-opening-mode",
        choices=("fill", "overwrite", "off"),
        default="fill",
        help="Infer EP Opening Sentence from Observance.",
    )
    parser.add_argument(
        "--antiphon-mode",
        choices=("fill", "overwrite", "off"),
        default="fill",
        help="Infer seasonal antiphon from Observance/Remembrance.",
    )
    parser.add_argument(
        "--seasonal-blessing-mode",
        choices=("fill", "overwrite", "off"),
        default="fill",
        help="Infer Seasonal Blessing from Observance (using Advent/Lent/Easter/etc. rules).",
    )
    parser.add_argument(
        "--special-collect-mode",
        choices=("fill", "overwrite", "off"),
        default="fill",
        help="How to write Special Collect from remembrance mapping.",
    )
    parser.add_argument(
        "--include-common-type",
        action="store_true",
        help="Add a debug column with the inferred common category.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process(
        input_path=Path(args.input_csv),
        output_path=Path(args.output_csv),
        fmt=args.fmt,
        flatten=args.flatten_whitespace,
        acna_year=args.acna_year,
        acna_base_url=args.acna_base_url,
        acna_province=args.acna_province,
        calendar_mode=args.calendar_mode,
        fill_remembrance_from_calendar=args.fill_remembrance_from_calendar,
        ignore_fetch_errors=args.ignore_fetch_errors,
        seasonal_map_path=Path(args.seasonal_map) if args.seasonal_map else None,
        seasonal_mode=args.seasonal_mode,
        mp_opening_mode=args.mp_opening_mode,
        ep_opening_mode=args.ep_opening_mode,
        antiphon_mode=args.antiphon_mode,
        seasonal_blessing_mode=args.seasonal_blessing_mode,
        special_collect_mode=args.special_collect_mode,
        include_common_type=args.include_common_type,
    )
    print(f"Wrote month file: {args.output_csv} ({args.fmt})")


if __name__ == "__main__":
    main()
