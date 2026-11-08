# Issue #50: February comparison with PR #51

Baseline: [PR #51](https://github.com/davidrossdegroot/daily-office/pull/51),
commit `6010b84fc44fafb7a46defc7ee2be250d510b5a0`, retained in a test fixture.
February was regenerated from the recorded 2027 source snapshot with all local
inference modes set to `overwrite`.

## Content differences

There are exactly two changed CSV cells across all 28 days:

| Date | Field | PR #51 | Regenerated draft |
| --- | --- | --- | --- |
| February 9 | Antiphon | Empty | The Lord has shown forth his glory: * O come, let us adore him. |
| February 24 | Seasonal Blessing | Empty | The existing Lenten Prayer over the People beginning “Look with compassion, O Lord…” |

All dates, observances, colors, readings, psalms, and collects match the baseline.
Saint Matthias retains red and its proper Collect of the Day. February 7 remains
green under the existing local Last Sunday of Epiphany policy.

## Remaining editorial review

The draft now has 18 CSV findings across 11 dates, all explicit publication
blockers, rather than silently accepted generic prayer text:

- February 3, 14, 15, 21: ministry/place blanks and unselected alternatives.
- February 4: unclassified Cornelius commemoration and generic alternatives.
- February 5, 14: singular common wording for multiple people.
- February 13, 27: unselected pastor-common alternatives.
- February 17: Janani Luwum and Ember Day need distinct reviewed treatment;
  one generic common cannot stand in for both.
- February 19, 20: unselected Ember Day alternatives.

The rendered preview adds six file findings for remaining blanks, including
repetitions in print-all and monthly pages. This does not mean six additional
unrelated prayer errors. The raw report is stored beside the draft CSV.

## Annual evidence

Offline source-to-CSV-to-HTML audits cover all 365 days of 2027 and 366 days of
2028. The recorded reports contain 360 and 354 findings respectively, including
repeated rendered-page findings. There are no missing dates, duplicated dates,
missing readings, or source-fetch errors in the final snapshots.

The principal annual blockers are generic prayer choices, ministry/place blanks,
plural or ambiguous commemorations, and missing ordinary-day antiphons. The
maintainer explicitly requires an antiphon every day; those unmapped dates
remain blocked until a general-use rule is selected. Full reports are in
[2027.review.json](reports/2027.review.json) and
[2028.review.json](reports/2028.review.json).

Tests exercise the production CLIs and the deployment build command. They cover
the February fixes, January regressions, 2028 leap day and Baptism Sunday, moving
Lent boundaries, overwritten stale blessings, failed/empty source responses,
name substitution, malformed content, and refusal to replace published output
with unresolved rendered prayers.
