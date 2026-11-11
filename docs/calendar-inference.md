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

## Approved April selections

- Anselm and William Law: the Teacher of the Faith common, which their BCP titles name.
- Henry Budd: the pastor common without bishop wording.
- George Augustus Selwyn: missionary common, the people of New Zealand, following
  his BCP title.
- James Lloyd Breck: missionary common, the people of Wisconsin, Minnesota, and
  California. His title names no place; these are the regions of his missions
  according to secondary sources.
- A transferred Annunciation keeps its own antiphon (BCP 2019, p. 29) rather than
  the Easter antiphon, matching the feast on its usual date.
- "Annunciation Sunday" is the calendar's name for the Fourth Sunday in Advent, not the
  feast. It keeps the Advent antiphon.

## Approved May selections and category rules

- **Teacher of the Faith default** (maintainer-approved category rule). A commemoration
  titled "Teacher of the Faith" takes the Teacher of the Faith common instead of the
  pastor common. Categories checked earlier, such as martyr or missionary, still come
  first. This is a deliberate exception to approving each person separately.
- Rogation Days: the first common prayer only, for the harvests, matching Ember Days.
- Josephine Butler, Mary Sumner, Mother Teresa of Calcutta, and Elizabeth of Hungary:
  the renewer of society common with "her" for the BCP's "his". Other commemorations
  keep the BCP's wording.
- The Martyrs of the Sudan: the martyr common with plural servants.
- Julian of Norwich: the monastic common, from her title "Anchoress".
- Dunstan with Ember Day and Helena with Ember Day: two complete, separately labeled
  collects, using the reformer common for Dunstan and the first commemoration common
  with "her" for Helena, followed by the selected Ember common.
- Jackson Kemper: missionary common, the people of the American West, narrower than
  his title's "United States" because the 1835 appointment was to the expanding West.
- Augustine of Canterbury: missionary common, the English people, the mission on which
  Gregory the Great sent him. Augustine of Hippo is a separate identity. Their history
  comes from secondary sources, not a direct reading of Bede.

**Missionary place wording** is delegated: the maintainer accepts the recommended
"people of" clause without a separate approval, based on evidence and listed in each
month's report so it can be vetoed. Other decisions still need an explicit answer.

## Approved June selections

- Blandina and Her Companions: the martyr common with plural servants, as for
  Perpetua and her companions.
- The Martyrs of Uganda: the martyr common with plural servants, capitalized from the
  BCP title.
- Thomas Ken: the pastor common with "Bishop and"; he was Bishop of Bath and Wells
  until his removal as a non-juror.
- Sundar Singh: the missionary common, since his title puts "Evangelist in India"
  before "Teacher of the Faith".
- Delegated place wording:
  - William Grant Broughton: the people of Australia, from the BCP title. The
    Australian Dictionary of Biography entry could not be read.
  - Columba: the people of Scotland. The title says "the Scots", but secondary sources
    describe a mission to the Picts from the Gaelic kingdom of Dál Riata, and
    "Scotland" covers both.
  - Sundar Singh: the people of India and Tibet, from secondary sources.

## July to December selections

The maintainer asked for July through December to be completed on the agent's
recommendations and reviewed as one set, rather than in batches. Every entry remains
open to veto. Other than the BCP texts named below, these are adaptations of the BCP
commons, not proper collects.

- **BCP texts used as printed.** Canada Day, Independence Day, Thanksgiving Day, and
  Remembrance Day use the national-day collects (pp. 636-637). All Souls' Day uses
  occasional prayer 114, "For all faithful departed" (p. 679), as the BCP has no
  collect for that day; the choice of that prayer is editorial.
- **Great O Antiphons** (Dec 16-23). These name no person, so they take no commemoration
  collect. The heading stays on the page, the Advent collect stands, and on Ember Days the
  selected Ember collect is the only special collect.
- **Christmas Day** says "this day" for the BCP's optional "[this day]".
- **Shared days** use two complete, labeled collects: Cyprian, Edward Bouverie Pusey with
  Ember Day; Philip with Canadian Thanksgiving; Martin with Remembrance Day; Catherine of
  Alexandria with United States Thanksgiving.
- **Plural martyrs:** the Martyrs of Papua New Guinea, Constance and her companions, Hugh
  Latimer and Nicholas Ridley, John Coleridge Patteson and his companions, James Hannington
  and his companions.
- **Pastor common with "Bishop and":** William White, Charles Inglis, Theodore of Tarsus,
  Robert Grosseteste, Samuel Isaac Joseph Schereschewsky, Samuel Seabury (for his
  Consecration), Nicholas, Martin.
- **Monastic or religious common:** Dominic, founder of a religious order, and Nicholas
  Ferrar, whose Little Gidding household kept a strict life of prayer without vows or a rule.
- **Teacher of the Faith common:** the Bible translators Jerome and John Wyclif.
- **Martyr common:** The Beheading of John the Baptist, from the Gospel's account of his
  death at Herod's order.
- **First commemoration common:** Olga and Vladimir, the Parents of the Virgin Mary, Lazarus,
  Mary, and Martha of Bethany, and Elizabeth and Zechariah (plural, "with them"); Joseph of
  Arimathea, Louis, and Edward the Confessor; Monica ("with her").
- **Renewer common with "her":** Hannah More.
- **Delegated place wording,** from BCP titles and secondary sources: Aidan and Paulinus,
  the people of Northumbria; Birinus, the people of Wessex; Allen Gardiner, the people of
  South America; Alexander Crummell, the people of Liberia; Ninian, the Pictish people;
  Wilson Carlile, the people of England; Remigius, the Frankish people; Philip, the people of
  Samaria (Acts 8:5); Henry Martyn, the people of India and Persia; Willibrord, the people of
  Frisia; Charles Simeon, the people of Cambridge, where he spent his ministry; Herman, the
  Native people of Alaska; Channing Moore Williams, the people of China and Japan.

## Agent workflow

The repository skill at `.agents/skills/generate-daily-office/SKILL.md` defines
monthly generation, evidence-backed recommendations in small batches, explicit
maintainer choices, durable mappings, regression tests, and regeneration. It
reuses existing approvals and leaves new editorial decisions pending until
answered. Invoke it as `$generate-daily-office`. Skill instructions guide the
agent; the Python publication checks enforce the release policy.
