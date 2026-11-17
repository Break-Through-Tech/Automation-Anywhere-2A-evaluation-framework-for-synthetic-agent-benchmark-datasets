# Designed complexity profiles version 0.3

## Start here

All 64 tasks have been reviewed against their global guidelines as well as their
milestones. 12 tasks gain 22 explicit operations/checks in total.
Original sources, v0.1 scores, v0.2 profiles and model responses are preserved.
No API calls or agent runs were made. This remains a provisional interpretation,
not a validated final score; there is no new combined number.

Open changes.csv to see before/after counts. profiles.csv gives the current
profiles. profiles.json retains exact evidence and a disposition for every global
guideline: covered, added, not applicable, conditional branch not selected,
uncertain, or constraint only. Covered rules are not counted a second time.

## The insurance update example

Operations increase from 8 to 11; checks increase from 2 to 5.
The added work is initial field validation, validation after the update, and
duplicate detection. Access logging stays an uncertain infrastructure/compliance
obligation, not an invented fourth agent operation. One patient response is
coordination; ordinary payer API returns are not extra response events. Passing
patient/provider IDs for normal booking does not add a linked-record obligation.

## Consistent treatment across domains

Banking and fraud prerequisites already covered by identity, screening and risk
operations are not added again. The risk tool already returns a recommended action;
its result selecting a route does not automatically create another check.
Missing explicit global work is included in two PA paths and early-payment
eligibility. Whether a global duty is relevant, already covered or ambiguous is
recorded per task. Unsupported infrastructure steps, unused branches and missing
environmental material are not converted into complexity penalties.

Explicit linking/merging/synchronization requirements are retained; routine ID
arguments alone are insufficient. External responses mean additional human or
asynchronous dependencies, not ordinary synchronous tool results. Shared event
keys avoid counting one AP review twice when tagged as approval and handoff.
Category counts overlap and must not be summed into a difficulty score.

## What remains uncertain

Some guidelines leave authority checks, human escalation or audit/logging actor
boundaries unclear. These stay visible without invented operations. Source
applicability and operation granularity remain assistant interpretations. Exact
atomic actions and independent decisions remain unknown. No new weights, cutoff
labels or independent-validation claim are introduced.

Rules: docs/evaluation/design_counting_rulebook_v0.2.md.

    python -m difficulty.designed_profiles_v3 --out results/difficulty/designed_v3_fresh
