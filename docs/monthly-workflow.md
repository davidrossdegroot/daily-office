# Monthly Data Workflow (Direct CSV Update)

This is the default monthly pipeline for producing and shipping Daily Office data.

## Default 5-Step Flow

1. Update the target month directly in the canonical repo CSV.
2. Review the generated month changes with `git diff`.
3. Apply any manual corrections directly in the canonical CSV (if needed).
4. Regenerate the static site.
5. Commit and open a PR.

## Step 1: Update Canonical CSV In Place

Target file:

- `data/acna-prayers-2026.csv`

Recommended command:

```bash
python bin/map_common_prayers.py \
  --update-canonical data/acna-prayers-2026.csv \
  --year 2026 \
  --month 3 \
  --acna-year 2026 \
  --flatten-whitespace \
  --fill-remembrance-from-calendar \
  --ignore-fetch-errors \
  --calendar-mode overwrite \
  --mp-opening-mode overwrite \
  --ep-opening-mode overwrite \
  --antiphon-mode overwrite \
  --seasonal-blessing-mode overwrite \
  --special-collect-mode overwrite
```

What this does:

- replaces/adds all rows for the target month in `data/acna-prayers-2026.csv`
- keeps canonical column order
- fetches observance/readings/collect data from the ACNA calendar source
- recomputes inferred fields (opening sentences, antiphon, seasonal blessing, special collect)

If you want a preview file instead of writing in place, add:

```bash
--out /tmp/acna-prayers-2026.preview.csv
```

## Step 2: Review Changes

```bash
git diff -- data/acna-prayers-2026.csv
```

Verify at least:

- row count for the target month matches calendar length
- one row per date, no missing days
- MP/EP readings and psalms look complete
- observance/color align with calendar expectations
- seasonal/special collects look correct for feast/fast days

## Step 3: Optional Manual Corrections

If a day needs manual correction, edit `data/acna-prayers-2026.csv` directly.

If you changed `Remembrance` values and want `Special Collect` to be recalculated, rerun Step 1 with:

```bash
--special-collect-mode overwrite
```

## Step 4: Regenerate Site

```bash
python generate.py
```

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
