# Lab difficulty metrics prepared on 11 November 2026

Difficulty is the project metric. Pass/fail/unverifiable are logged observations,
with environmental causes and eligibility kept separate. See
`docs/evaluation/difficulty_methodology_v0.3.md` for the proposed operational rule,
email provenance limitation, historical-policy boundary and pending decisions.

Computed without API or mock calls:

- 64 designed profiles, seven domains: 43 supplied easy labels, 18 medium and 3 hard.
- Shared workflow steps range 5–11; median 7. Expected domain interactions range
  1–23; median 7. Full profiles, domain and label summaries preserve exact counts.
- Designed labels are not monotonically ordered by shared workflow length:
  mean easy 7.35 steps, medium 6.94, hard 6.67. This descriptive pooled pattern
  does not invalidate the labels; task paths, domain mix and the small hard group
  limit interpretation. No combined weights or causal claims are made.
- All 256 original trial slots are retained. The selected historical development
  source supplies 16 unverifiable assessments and zero eligible attempts. The
  other 240 are not assessed under that source policy. There is no defensible
  numeric execution difficulty from this log, and no new-policy regrading is claimed.
- Three additional original tasks were inspected with exact evidence citations:
  a rejected reference input, a missing PA status identifier, and a denial branch
  inconsistent with inherited mock responses. Inspection findings are not new labels.

`summary.json` contains summaries and source fingerprints. `designed_profiles.json`
and `.csv` contain per-task features. `attempt_outcomes.json` preserves original
attempt identities, source policy, trace hashes, logged outcomes and lifecycle status.
`execution_by_task.json` and `.csv` expose denominators and unavailable scores.
`meeting_examples.json` contains the additional source/trace examples.

The earlier baseline, judge outputs, human answers, original dataset and optional
revised onboarding pilot remain separate and unchanged. Keep runtime correlations
undefined until reliable eligible outcomes vary. No new API credits were spent.
