# Monthly Data Workflow (TSV-First)

This is the default monthly pipeline for producing and shipping Daily Office data.

## Default 5-Step Flow

1. Generate a month TSV in one command with `bin/map_common_prayers.py --year ... --month ...`.
2. Paste TSV into Google Sheets and do manual verification.
3. Export from Google Sheets to CSV.
4. Merge that month into the canonical repo CSV (`data/acna-prayers-2026.csv`).
5. Commit and open a PR.

## Step 1: Generate Month TSV

```bash
python bin/map_common_prayers.py \
  --year 2026 \
  --month 3 \
  --out /tmp/2026-03.generated.tsv \
  --format tsv \
  --flatten-whitespace \
  --acna-year 2026 \
  --fill-remembrance-from-calendar \
  --ignore-fetch-errors
```

This single command first generates internal month input rows:

- `Date` (formatted like `Mar 1`)
- `Remembrance` (required input column; starts blank unless `--fill-remembrance-from-calendar` is used)

Then it fills canonical fields from mapping rules plus calendar day pages:

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
- `Remembrance` (recommended via `--fill-remembrance-from-calendar`)

If `Seasonal Collect` is still blank for any date, fill manually in Sheets or provide a
seasonal map CSV via `--seasonal-map` as an override source.

If you need to prefill custom remembrance values before mapping, use:

1. `python bin/make_month_skeleton.py --year 2026 --month 3 --out /tmp/2026-03.input.csv`
2. Edit `Remembrance` values in the input CSV.
3. Run `python bin/map_common_prayers.py --in /tmp/2026-03.input.csv --out /tmp/2026-03.generated.tsv --format tsv ...`

## Step 2: Verify in Google Sheets

1. Open a blank Google Sheet.
2. Paste `/tmp/2026-03.generated.tsv` directly.
3. Verify at least:
   - row count matches month length
   - one row per date, no missing dates
   - MP/EP readings and psalms look complete
   - observance/color align with calendar expectations
   - seasonal/special collects look correct for feast/fast days

If you need manual edits, make them in Sheets.

## Step 3: Export from Sheets to CSV

1. Download as CSV from Google Sheets.
2. Save as something like `/tmp/2026-03.sheet-export.csv`.
3. Keep header names unchanged.

## Step 4: Merge Into Canonical Repo CSV

Target file:

- [`data/acna-prayers-2026.csv`](./data/acna-prayers-2026.csv)

Merge rule:

1. Replace only the target month rows in the canonical file.
2. Preserve canonical header order.
3. Keep one row per date.

Columns to update for the month:

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

## Step 5: Commit and Open PR

```bash
git checkout -b data/2026-03
git add data/acna-prayers-2026.csv
git commit -m "Update March 2026 Daily Office data"
git push -u origin data/2026-03
```

Then open a PR to merge into your main branch and deploy.

## Fallback: Manual Backfill for Missing Readings

If calendar fetch misses any MP/EP fields:

1. Use BCP monthly MP/EP tables to fill only missing cells.
2. Keep formatting consistent with the existing dataset:
   - preserve `†`
   - preserve comma-separated psalm lists
   - keep reference abbreviations consistent (`Gen`, `Matt`, etc.)

## Canonical Schema (Reference)

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
