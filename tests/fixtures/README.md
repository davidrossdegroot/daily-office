# Calendar source fixtures

`february-2027-pr51.csv` records the parsed content of the February draft from
PR #51, head commit `6010b84fc44fafb7a46defc7ee2be250d510b5a0`. It is the fixed
comparison baseline, not a corrected source or an expected publishable book.

`calendar-source-2027.csv` and `calendar-source-2028.csv` were captured on
2026-11-08 through the existing calendar-fetch/parser boundary from:

```
https://liturgical-calendar.com/en/ACNA2019/YYYY-MM-DD
```

They contain 365 and 366 dated source entries respectively, including the
primary observance/color, secondary headings, primary collect, and six Office
reading/psalm fields. Locally inferred opening sentences, antiphons, special
collects, and blessings are blank. Failed requests were retried using cached
successful responses; the final snapshots contain no fetch errors.

The fixtures keep regression tests independent of the network. Tests use a
local HTTP server only when checking fetch-failure behavior. Annual reports
record each source snapshot's SHA-256 so changes to the evidence are visible.
Refresh fixtures deliberately rather than as a side effect of running tests.

Texts and readings retain the project's Book of Common Prayer (2019)
attribution. These are snapshots of a third-party calendar, not a statement
that every row has been independently verified against the printed BCP.
