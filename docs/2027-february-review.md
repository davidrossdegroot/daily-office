# February 2027 draft review

Draft: `data/drafts/acna-prayers-2027-02.csv`. This is review data, not a published calendar.

Generated from the existing ACNA2019 source with fetch failures treated as errors:

```bash
python bin/map_common_prayers.py --year 2027 --month 2 --acna-year 2027 \
  --out data/drafts/acna-prayers-2027-02.csv --flatten-whitespace \
  --fill-remembrance-from-calendar --calendar-mode overwrite \
  --mp-opening-mode overwrite --ep-opening-mode overwrite \
  --antiphon-mode overwrite --seasonal-blessing-mode overwrite \
  --special-collect-mode overwrite
```

## Findings before publication

- **February 9, Shrove Tuesday:** Antiphon is empty. The opening sentences correctly resolve Epiphany from the date, but antiphon inference relies on headings and does not recognize Shrove Tuesday. Add equivalent season/date context before publication.
- **February 24, Saint Matthias:** Seasonal Blessing is empty during Lent. Opening sentences and antiphon are Lenten, but blessing inference does not use the date to recover the season for this named feast. Decide and implement the intended Lenten Prayer over the People here, retaining Matthias's proper Collect of the Day.
- **February 3, 14, 15, 21:** Missionary/evangelist common collects contain literal underscore blanks for the people or place of ministry. Resolve these editorially or choose an appropriate complete collect before publication. `N.` is an intentional name-substitution token handled by the HTML generator; the underscore blanks are not substituted.
- **February 7, Last Sunday of Epiphany (Transfiguration Sunday):** Green follows the repository's explicit existing policy and regression test. Confirm that this is the desired local practice; this draft does not change it to white.
- **February 14, Cyril and Methodius:** The generic common uses singular wording for two commemorated people. Review the rendered name substitution and choose appropriate wording before publication.

## Validation

- Exactly 28 unique dates, February 1–28; no out-of-month rows or malformed CSV fields.
- All observances, colors, MP/EP opening sentences, four lessons, both psalm fields, and seasonal collects are populated.
- No `PLACEHOLDER` tokens remain; intentional common-collect blanks are listed above.
- Presentation (February 2) is white with its proper collect. Ash Wednesday (February 10) is purple; its date agrees with Easter minus 46 days. Matthias (February 24) is red with its proper collect and Lenten openings.
- All 33 existing unit tests and Ruff checks pass.
- Separate HTML preview builds 28 day pages plus index, monthly, print-all, and about pages with 2027 headings. February 1 renders as Monday.
- This is a structural and targeted content review, not a line-by-line verification of every reading against the printed BCP.

```bash
python generate.py --year 2027 --csv data/drafts/acna-prayers-2027-02.csv \
  --output-dir /tmp/daily-office-2027-february-preview
```
