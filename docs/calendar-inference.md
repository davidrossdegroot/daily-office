# Calendar inference and publication review

The generator resolves a date's season separately from its primary observance
and secondary commemorations. A shared calendar context feeds the opening
sentences, antiphon, blessing, and color rules. A feast name is not a season:
Matthias during Lent keeps Lenten office material, and the Nativity of John in
June does not select Christmas opening sentences.

## Local precedence and editorial policy

- Use the calendar date for seasons, including movable Easter, Ash Wednesday,
  Ascension, Pentecost, Trinity Sunday, and Advent boundaries. Heading-based
  fallback remains available to callers without date context.
- Apply known proper collects before selecting generic commons. Feast colors
  and explicitly configured feast antiphons override seasonal defaults; an
  optional commemoration cannot replace the primary day's seasonal antiphon.
- Keep the existing local green policy for the Last Sunday of Epiphany, even
  when its heading includes Transfiguration. Baptism of Our Lord and the
  Epiphany feast are white. This preserves existing repository decisions;
  changes to these conventions require an explicit editorial decision.
- Retain the Lenten Prayer over the People on named feasts during Lent,
  including Saint Matthias. The existing five prayers rotate from Ash
  Wednesday. The Epiphany blessing belongs to January 6, not the whole season.
  These separate blessings are not inferred from another site's Office grace.
- Classify a commemoration from its own information, not words in the primary
  observance. Temporal secondary headings do not generate saints' collects.
- Preserve supplied special collects in `fill` mode. Explicit `overwrite`
  recomputes them from the configured proper/common rules. It is intended for
  regeneration before editorial corrections, not for preserving manual choices.
- Generic commons remain visible in drafts. Missing ministry/place wording,
  bracketed alternatives, unknown categories, plural people with singular
  wording, and multiple commemorations sharing one common require review.
  A complete reviewed proper collect can be supplied directly; prayer wording
  is not invented to make validation pass.
- **An antiphon is required every day**, as confirmed by the maintainer for
  issue #50. Ordinary-day blanks without a configured mapping therefore block
  publication. The [BCP Morning Prayer rubric](https://bcp2019.anglicanchurch.net/wp-content/uploads/2019/08/06-Daily-Morning-Prayer.pdf)
  permits optional antiphons; this daily-summary requirement is a stricter
  local content policy.
- **Antiphons after Pentecost** (maintainer choice, issue #56). Seasonal antiphons
  still come first. The BCP 2019 (p. 30) gives "The Lord is glorious in his saints"
  for "All Saints' and other Major Saints' Days" without listing those days. Locally
  it is used on All Saints' Day, the Visitation, Barnabas, the Nativity of John the
  Baptist, Peter and Paul, Mary Magdalene, James, Mary the Virgin, Bartholomew,
  Matthew, Michael and All Angels, Luke, James of Jerusalem, Simon and Jude, and
  Andrew in years when November 30 comes before Advent.
  Every other day after Pentecost, including Holy Cross Day and optional
  commemorations, rotates the three general antiphons on BCP 2019 p. 14 in printed
  order, one per calendar day, counted from the Monday after Pentecost. Feast days
  interrupt the display without shifting the count.

## Drafts and publication

CSV generation writes a sibling `*.review.json` report, including direct
canonical month updates. Supply `--year` if an input filename has no year:

```bash
python bin/map_common_prayers.py --in month.csv --year 2027 --out draft-2027.csv
```

An ignored fetch error is persisted in an optional `Source Error` CSV column.
It survives regeneration without fetching and blocks publication even if old
readings are still populated. A successful refetch clears it. HTTP 200 responses
without the required calendar data are also source failures.

HTML generation creates a draft by default and writes `OUTPUT_DIR.review.json`.
Its report includes final decoded HTML checks after name substitution,
including pages in every yearly subdirectory. Multi-year builds aggregate CSV
findings for all selected years before rendering. A raw
`N.` token is allowed only where it can be resolved as a special-collect name;
none may remain in the final pages of strict years. Underscore blanks and literal placeholders
are rejected for strict years, and bracketed prayer alternatives require editorial review.

```bash
python generate.py --year 2027 --month 2 \
  --csv data/drafts/acna-prayers-2027-02.csv \
  --output-dir /tmp/february-preview

# The same build with publication enforcement:
python generate.py --publish --year 2027 --month 2 \
  --csv data/drafts/acna-prayers-2027-02.csv \
  --output-dir /tmp/february-published
```

`--publish` requires a full year unless `--month` explicitly selects a complete
month. Missing/duplicate/invalid dates, malformed CSV rows, missing required
readings or prayers, and unresolved review findings block publication. Special
Collect, Remembrance, and Seasonal Blessing are not universally required:
blessings are required when the configured calendar rules call for one, and
commemorations require an appropriate selected collect.

Publication builds in a temporary directory and checks final HTML before
replacing the requested output directory. Rejected content leaves existing
output untouched; successful publication removes stale preview pages.

Deployment runs `python generate.py --publish`. **2026 is the sole legacy
exemption**: its CSV and rendered findings remain in the report with
`year: 2026` and `blocking: false`; they never block publication. This is not a
claim that 2026 content has been corrected. Every other year remains strict,
including the full-year requirement unless `--month` explicitly selects a month.
The report's `publishable` value depends on blocking findings, not whether the
findings list is empty.

No year is removed to obtain a passing build. Multi-year builds retain 2026's
`/2026/` calendar and day pages, both switcher entries, and existing root day URLs.
A single-year 2026 build keeps its existing flat layout. The build returns an
explicit HTML-page-to-year manifest: this identifies ownership of root summary
pages (`index.html`, `all.html`, monthly pages, and `about.html`), yearly directory
pages, and legacy day redirects. Rendered review uses that manifest, not the
finding's date string. When the root repeats 2026 its findings are non-blocking;
when it repeats 2027 they remain strict. Unknown ownership is always blocking.

Strict CSV checks run before building; strict rendered checks run in the staged
output before replacement. A 2027 finding therefore leaves existing published
output untouched, regardless of any 2026 exemptions. PR preview builds remain
drafts; both workflows retain review reports as artifacts.

## Reproducible annual checks

Recorded source CSVs retain the fetched observances, colors, readings, psalms,
primary collects, and secondary headings. The audit command recomputes local
fields offline, builds yearly HTML previews, and reports every blocker:

```bash
python bin/audit_years.py \
  tests/fixtures/calendar-source-2027.csv \
  tests/fixtures/calendar-source-2028.csv \
  --output-dir /tmp/daily-office-audit
```

Reports include a source SHA-256 and row count. The recorded reports in
`docs/reports/` are reproducible from these fixtures. A finding count is not a
day count: a prayer can have multiple findings, and aggregate HTML pages can
repeat a placeholder already reported on an individual day.

See [the February comparison](issue-50-february-comparison.md) for the comparison
with PR #51. The annual checks report unresolved editorial choices; passing
structural checks is not a full liturgical certification of every reading.

## Approved February collect selections

Maintainer-approved selections are keyed by normalized commemoration name,
independent of year, before the generic common fallback:

- Anskar: missionary common, naming the people of Denmark and Sweden.
- Cyril and Methodius: missionary common, plural servants, naming the Slavic people.
- Thomas Bray: pastor common without the optional bishop wording.
- Billy Graham: missionary common adapted to name the peoples of the world.
- Cornelius the Centurion: the first commemoration common, naming Cornelius.
- Martyrs of Japan: the martyr common with plural servants.
- Absalom Jones and George Herbert: pastor common without bishop wording.
- Ember Day: the first common, without optional “now” or the second alternative.
- Janani Luwum with Ember Day: two complete, separately labeled collects, using
  the named martyr common followed by the selected Ember common. An individual
  reviewed collect cannot approve an unreviewed combination of commemorations.

These are reviewed adaptations of the existing commons, not newly sourced
proper collects. Unapproved commemorations retain their review findings.

## Approved March selections and precedence

- Optional commemorations stay in the draft on Sundays and in Holy Week and
  Easter Week. They are added beside the day's own collect and do not replace its
  fixed propers (BCP 2019, pp. 689–690).
- A commemoration listed after a seasonal heading, such as Easter Eve, receives
  its own collect and review.
- When March 25 falls in Holy Week or Easter Week, the Annunciation moves to the
  Monday after the Second Sunday of Easter. BCP 2019 forbids replacing those
  weeks' fixed propers but names no transfer date, and the source calendar does
  not move the feast. The date is a maintainer choice following older Anglican
  custom. Other holy days are not covered by this choice.
- Perpetua and Her Companions: the martyr common with plural servants.
- Missionary common, naming each person and people. David: the people of Wales.
  Patrick: the Irish people. Gregory the Illuminator: the Armenian people.
  Charles Henry Brent: the people of the Philippines. These follow the BCP 2019
  calendar titles. Felix: the people of East Anglia, narrower than the title's
  "the Angles" because he was first bishop of the East Angles. Chad: the people
  of Mercia. Cuthbert: the people of Northumbria. Their titles name only Lichfield
  and Lindisfarne, so the wider region of their ministry was chosen. The history
  behind the last three comes from secondary summaries, not a direct reading of Bede.
- John and Charles Wesley: the reformer common, fully plural ("your servants",
  "burning and shining lights").
- Gregory the Great and Cyril of Jerusalem: the Teacher of the Faith common, which
  their BCP titles name, rather than the pastor common. This covers only these
  two, not every bishop titled a teacher; Cyril of Alexandria is a separate identity.
- Robert Machray: the pastor common with "Bishop and". His BCP title says only
  "First Primate of Canada"; he was consecrated Bishop of Rupert's Land in 1865.
- James DeKoven and John Donne: the pastor common without bishop wording.

## Approved January selections

- Hilary of Poitiers and Thomas Aquinas: the Teacher of the Faith common, which
  their BCP titles name, rather than the pastor common.
- Vedanayagam Samuel Azariah: missionary common, the people of South India.
- Kentigern: missionary common, the people of Strathclyde and Cumbria. Both places
  follow the BCP 2019 calendar titles.
- Anthony: the monastic common, from his title "Hermit in Egypt".
- Wulfstan: the pastor common with "Bishop and".
- Timothy and Titus: the pastor common, plural and without bishop wording, because
  Paul left them to oversee existing churches at Ephesus and Crete (1 Timothy 1:3;
  Titus 1:5).
- Lydia, Dorcas, and Phoebe: the first commemoration common, plural. The title names
  them helpers of the apostles, not missionaries (Acts 9:36; 16:14-15; Romans 16:1-2).

## Agent workflow

The repository skill at `.agents/skills/generate-daily-office/SKILL.md` defines
monthly generation, evidence-backed recommendations in small batches, explicit
maintainer choices, durable mappings, regression tests, and regeneration. It
reuses existing approvals and leaves new editorial decisions pending until
answered. Invoke it as `$generate-daily-office`. Skill instructions guide the
agent; the Python publication checks enforce the release policy.
