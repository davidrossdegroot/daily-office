# Monthly Data Workflow (Reusable)

This document captures the repeatable process for building one month of Daily Office data from source material and preparing sheet-ready CSV rows.

## Goal

For each day in a month, produce:

- `Date`
- Morning fields:
  - `MP First Lesson`
  - `MP Second Lesson`
  - `Psalms (MP, 60-day)`
- Evening fields:
  - `EP First Lesson`
  - `EP Second Lesson`
  - `Psalms (EP, 60-day)`
- `Remembrance`
- `Common Type`
- `Common Prayer`

These map directly into the main project CSV schema in [`data/acna-prayers-2026.csv`](/Users/daviddegroot/workspace/daily-office/data/acna-prayers-2026.csv).

## Source Inputs

- BCP 2019 PDF tables for Morning/Evening prayer readings.
- ACNA liturgical calendar month page (example pattern):
  - `https://liturgical-calendar.com/en/ACNA2019/2026-03`
- The common prayer texts (from BCP “Common of …” section).

## Monthly Procedure

1. Build a date skeleton for the month.
2. Fill Morning Prayer columns from the PDF table.
3. Fill Evening Prayer columns from the PDF table.
4. Fill `Remembrance` from the liturgical calendar page.
5. Auto-map remembrance rows to common prayer text.
6. QA and then merge into the project CSV.

## Step 1: Date Skeleton

Create a sheet/CSV with one row per day:

```csv
Date,MP First Lesson,MP Second Lesson,"Psalms (MP, 60-day)",EP First Lesson,EP Second Lesson,"Psalms (EP, 60-day)",Remembrance
Mar 1,,,,,,,
Mar 2,,,,,,,
...
Mar 31,,,,,,,
```

Tip: Keep date format exactly like `Mar 1` to match the current dataset style.

## Step 2: Morning Prayer Ingestion

From the BCP monthly MP table, capture for each day:

- `MP First Lesson`
- `MP Second Lesson`
- `Psalms (MP, 60-day)`

Normalization rules:

- Preserve `†` markers.
- Use `-` for ranges if copied text uses long dashes.
- Keep comma-separated psalm lists exactly as printed.
- Leave empty if a field is genuinely blank.

## Step 3: Evening Prayer Ingestion

From the BCP monthly EP table, capture for each day:

- `EP First Lesson`
- `EP Second Lesson`
- `Psalms (EP, 60-day)`

Use the same normalization rules as Morning.

## Step 4: Remembrance Ingestion

For each day in the month, pull remembrance title from the ACNA calendar page.

- If no remembrance is listed, leave blank.
- Keep the site’s wording (including commas/years) so audit is easy.

Optional automation:

- The script can fetch day-page fields from `liturgical-calendar.com`: `Observance`, `Liturgical Color`, available MP/EP psalms/readings, and optionally `Remembrance`.
- Enable with `--acna-year YEAR`.

## Step 5: Map Remembrances to Common Prayers

Use the helper script:

```bash
python bin/map_common_prayers.py --in month.csv --out month.with-prayers.csv
```

To fetch calendar day metadata from ACNA calendar pages while processing:

```bash
python bin/map_common_prayers.py \
  --in month.csv \
  --out month.with-prayers.tsv \
  --format tsv \
  --flatten-whitespace \
  --acna-year 2026 \
  --ignore-fetch-errors
```

`Seasonal Blessing` is also inferred automatically from `Observance` (mode: `fill` by default). Control it with:

- `--seasonal-blessing-mode fill` (default)
- `--seasonal-blessing-mode overwrite`
- `--seasonal-blessing-mode off`

If you also want remembrance auto-filled from secondary observances on day pages:

```bash
python bin/map_common_prayers.py \
  --in month.csv \
  --out month.with-prayers.tsv \
  --format tsv \
  --flatten-whitespace \
  --acna-year 2026 \
  --fill-remembrance-from-calendar \
  --ignore-fetch-errors
```

For Google Sheets paste reliability (recommended):

```bash
python bin/map_common_prayers.py --in month.csv --out month.with-prayers.tsv --format tsv --flatten-whitespace
```

Then paste the TSV directly into Sheets; tabs are handled cleanly and avoid comma/quote parsing issues.

This script now enforces the full canonical schema:

- `Date`
- `Liturgical Color`
- `Observance`
- `MP Opening Sentence of Scripture`
- `Antiphon`
- `MP First Lesson`
- `MP Second Lesson`
- `Psalms (MP, 60-day)`
- `EP Opening Sentence of Scripture`
- `EP First Lesson`
- `EP Second Lesson`
- `Psalms (EP, 60-day)`
- `Seasonal Collect`
- `Special Collect`
- `Seasonal Blessing`
- `Remembrance`

### Seasonal Mapping (optional but recommended)

To auto-fill liturgical season fields by observance, provide a mapping file:

```bash
python bin/map_common_prayers.py \
  --in month.csv \
  --out month.with-prayers.tsv \
  --format tsv \
  --flatten-whitespace \
  --seasonal-map data/mappings/seasonal-defaults.csv
```

Create starter map from your month input (unique observances extracted automatically):

```bash
python bin/map_common_prayers.py \
  --in month.csv \
  --out month.preview.tsv \
  --format tsv \
  --seasonal-template-out data/mappings/seasonal-defaults.csv \
  --special-collect-mode off
```

Template header is available at:

- [`data/mappings/seasonal-defaults.template.csv`](/Users/daviddegroot/workspace/daily-office/data/mappings/seasonal-defaults.template.csv)

Input requirements:

- CSV includes at least `Date` and `Remembrance` columns.
- If `Observance` exists, script can use it as an extra hint.

Output:

- Adds/updates:
  - `Special Collect` (from remembrance/common-prayer mapping)
  - optional debug column: `Common Type` via `--include-common-type`

## Step 6: QA Checklist

Before merging:

1. Row count matches number of days in month.
2. Every date appears exactly once.
3. MP and EP fields are present for each date (unless intentionally blank).
4. `Remembrance` blanks only where calendar has no entry.
5. `Special Collect` present for remembrance days where a common prayer should apply.
6. Spot-check at least 3 special days (for example: major feasts, martyrs, reformers).

## Merge Into Canonical CSV

Update rows in [`data/acna-prayers-2026.csv`](/Users/daviddegroot/workspace/daily-office/data/acna-prayers-2026.csv) for the month:

- `Liturgical Color`
- `Observance`
- `MP Opening Sentence of Scripture`
- `Antiphon`
- `MP First Lesson`
- `MP Second Lesson`
- `Psalms (MP, 60-day)`
- `EP Opening Sentence of Scripture`
- `EP First Lesson`
- `EP Second Lesson`
- `Psalms (EP, 60-day)`
- `Seasonal Collect`
- `Special Collect`
- `Seasonal Blessing`
- `Remembrance`

If you enable `--include-common-type`, that debug column is only for QA and does not need to be merged into the canonical CSV.

## Year-Scale Strategy

To complete a full year quickly:

1. Process one month at a time in a consistent template.
2. Reuse the same normalization and QA checklist each month.
3. Commit monthly batches (`March`, `April`, etc.) for easy rollback.
4. Keep a lightweight “exceptions” log for unusual feast/observance cases.

## Next-Year Rollover (2027+)

The process is unchanged. Only swap:

- Source month URL year segment (for example `2027-03`).
- Destination CSV file name/year fields.

The remembrance-to-common mapping script is year-agnostic.
