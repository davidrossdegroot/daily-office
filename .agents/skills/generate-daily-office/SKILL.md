---
name: generate-daily-office
description: Generate or regenerate Daily Office prayer CSVs and HTML in this repository, investigate review findings, and guide the maintainer through editorial selections. Use for monthly/yearly prayer generation and collect-review work; not for unrelated site styling or general theology questions.
---

# Generate and review Daily Office prayers

Work from the repository root. Read `docs/calendar-inference.md` for current
liturgical choices and publication policy, and `docs/monthly-workflow.md` for
source-generation commands. Inspect the current CLI help when composing commands.
Use the existing Python pipeline; do not recreate calendar calculations in chat.

## Generate evidence

- Establish the requested year/month, current branch, and intended source. Keep
  new drafts in `data/drafts/` and HTML previews in a separate output directory.
  Preserve unrelated working-tree changes. Branch, commit, push, and open PRs
  within the user's requested scope; generating a draft does not authorize a
  live deployment.
- Fetch through the existing calendar source or use recorded source fixtures.
  Prefer fail-fast fetching. If a draft intentionally continues after a source
  failure, retain its `Source Error` and report the failure; do not clear it to
  obtain a passing build.
- Regenerate local fields using the current reviewed mappings. Read both the
  CSV review report and the HTML review report; a successful draft build alone
  does not establish publication readiness. Compare with an identified prior
  draft/PR at cell level, preserving readings and psalms unless evidence warrants
  a correction.

## Resolve findings with the maintainer

Group repeated findings by their underlying decision. Reuse approved selections
from `REVIEWED_COMMEMORATION_COLLECTS` and `REVIEWED_COMMEMORATION_GROUPS` rather
than asking again. Read the actual prayer text and commemoration context before
proposing a change.

Distinguish implementation defects from new editorial decisions. Fix authorized
implementation defects with regression tests. For unapproved prayer wording,
ministry/place substitutions, common choices, plural adaptations, or treatment
of combined commemorations:

1. Investigate the evidence. Prefer the BCP 2019 and connected primary sources;
   cite supporting sources and disclose inaccessible pages. Distinguish a proper
   collect from a reviewed adaptation of a common. Never invent history or claim
   that proposed wording is an official proper collect.
2. Prompt with a small batch of related decisions (usually up to three). Show
   affected dates/people, exact proposed clauses or prayer alternatives, a clear
   recommendation with its reason, and the meaningful alternatives. Label options
   consistently, for example A/B. Allow a custom response. Include the full prayer
   when a summary would conceal a meaningful difference.
3. Wait for an actual answer before applying a new editorial choice. Interpret
   “A for all” against the current displayed batch, not unpresented decisions.
   Explain genuinely ambiguous scope and keep those dependent edits pending.
4. Encode the approved choice durably by commemoration identity or explicit
   combination, not a one-off CSV patch or a fixed year/date. Record the selection
   and rationale in the policy docs. Apply a combined selection only to the exact
   reviewed group; one saint's reviewed prayer cannot approve another commemoration.
5. Add a failing behavioral test, implement the choice, and test regeneration in
   the requested year and another relevant year (including 2028 when appropriate).
   Retain negative tests using explicitly unreviewed examples after approvals make
   previous examples clean. Avoid silent auto-approval or editing validators merely
   to suppress a real finding.

Repeat until requested findings are resolved or explicitly awaiting a decision.
Do not independently choose the remaining editorial answers to finish faster.

## Verify and report

Regenerate the requested CSV, reports, and HTML after approvals. Run the full
unit suite and `ruff check generate.py bin tests`. When annual rules change,
rerun `bin/audit_years.py` against the recorded 2027/2028 source snapshots and
refresh the corresponding reports; distinguish unresolved dates outside the
requested month from that month's readiness.

Use `generate.py --publish` for the final local publication check. Keep its staged
output behavior. Preserve every selected year, year-switcher entries, and existing
day URLs. The deliberate **2026-only exemption** retains findings as non-blocking;
it does not remove 2026 from the site or permit skipping checks. Every other year
remains strict, including complete-year coverage unless an explicit month is
requested. Rendered findings use build-produced page ownership, including root
summary pages, rather than guessing the year from a finding's date label. Unknown
page ownership fails closed. Do not broaden this exemption.

Finish with the preview/report locations, exact content differences, test results,
remaining findings, and commit/push status. Describe 2026 as exempt, not clean.
Never treat publication eligibility as authorization to deploy.
