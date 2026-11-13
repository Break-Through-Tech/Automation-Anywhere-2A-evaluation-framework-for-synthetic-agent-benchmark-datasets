# Current synthetic result: 64.30 / 100

The final computed synthetic result now covers **64/64 tasks**, with no exclusions.
Use [the final report](../../results/difficulty/synthetic_final_v15/README.md),
[the readable task CSV](../../results/difficulty/synthetic_final_v15/task_scores_readable.csv)
and [the chart](../../results/difficulty/synthetic_final_v15/score_overview.png).
All scores use one evidence-reference format; older-format scores are not pooled.
The result is provisional in validity, based on one judgment per task. Native tau2
whole-dataset scoring and Coverage/overall-quality outputs remain separate.

The API blocker is resolved: IDs replace natural-language schema enum values, and exact
source excerpts are resolved deterministically without changing scores. 153 offline
tests passed and the real framework reproduced the final report exactly. Earlier stop
gates/plans below describe historical stages; the final report supersedes their status.

---

# Reporting handoff: source-only numeric designed difficulty

Start with `results/difficulty/numeric_design_calibration_v13/README.md` and its complete
task CSV. This is an LLM assessment of task designs. It does not run an agent, measure
execution success, or replace the separate Coverage metric.

## What the number means

Five source-backed levels (0–4) describe workload, reasoning, tool use,
dependencies/coordination and information discovery. Each contributes 20%:
`score = 5 × sum(levels)`, on a provisional 0–100 scale. Scenario-specific workflow
steps, milestones, tool contracts and intended exit requirements support the ratings.
Milestones do not automatically add operations. Alternative paths are not all charged
at once, and equal step counts or equal numeric scores can be legitimate.

For each task, average all planned usable judgments. If any planned judgment is missing,
unscorable or erroneous, retain that status instead of averaging only the convenient
responses. For a dataset, average the usable task means with equal weight per task.
Missing tasks are not zero. State scored/total coverage and whether a mean describes a
selected subset. Never present a small calibration subset as the final dataset score.

## Files to consume

- `task_scores.csv`: every original task, score or missingness reason, domain/workflow,
  planned/saved judgment counts and repeat range.
- `task_scores.json` and `summary.json`: dataset/domain/workflow means, median, IQR,
  range, histogram and coverage.
- `reliability.json`: observed repeat ranges, frozen tolerances and bounded go/no-go.
- `judgment_evidence.json` and `source_bindings.json`: raw responses, exact input/source
  provenance, unit assessments, evidence diagnostics, model settings and versions.
- `crosschecks.json`: structural-feature and supplied-label comparisons after scoring.
- `run_manifest.json`: API-call accounting, token usage and the exact scoring protocol.

Keep schema/validator/rubric/model versions visible. Historical reports remain available
but their scores must not be silently pooled with a different generation schema. The
new task-bound schema restricts unit IDs; evidence validation recognizes literal or
decoded source quotations and explicitly flagged canonical tool-signature renderings.
This checks provenance and format, not independent semantic correctness.

## Handoff to existing report tasks

For #59, review coverage and exclusions before calling a number final. For #63, compare
Coverage and Difficulty as separate measures; do not invent an overall-quality result
from this calibration alone. For #65, airline/retail examples are case comparisons until
there are enough scored tasks to support domain summaries. For #69, include the formula,
source/input limits, repeatability, scoring coverage and complementary checks. For #26,
use `difficulty/design/README.md` for preparation, bounded runs and reporting commands.

The historical structural 40/40/20 candidate is not this metric. The five 20% difficulty
weights are also not the separate Coverage-plus-Difficulty overall-quality weights.
Supplied easy/medium/hard tags are withheld during generation and compared afterward;
they are annotations, not independently verified gold labels. Do not change weights or
thresholds simply to make tau2 scores higher than synthetic scores.

## Current run and comparison scope

The final synthetic primary result is 64.296875/100 (64/64 original tasks), one
judgment each. Use `results/difficulty/synthetic_final_v15`. The subsequent v16
calibration repeats are diagnostics; they do not replace primary synthetic judgments.
Current-format practical checks passed: ten cross-domain tasks repeated three times,
maximum range 5 and mean range 2.5; four controls passed frozen tolerances. This
supports bounded provisional scoring, not independent difficulty validity.

The native adapter now projects selected task-relevant original database records and
linked dependencies, includes environment assertions and static setup/assertion
semantics, and distinguishes baseline state from initialization overrides/actions.
Setup is not charged as agent workload. Original data are unchanged. The task agent
must still retrieve facts shown only as judge context. Missing essential state remains
unscorable. Retail 57 lacks explicit completion references; this is flagged, with stated
user goal/policy usable only if a defensible assessment is possible.

The frozen tau2 base run covers 278 tasks: airline 50, retail 114, telecom 114. Three
native pilots have three planned judgments; all other tasks have one. Average each
pilot first, then weight all tasks equally. Controls and synthetic diagnostic repeats
never enter primary dataset means. Do not average the three domain means equally for
the headline: the domains have different task counts.

Native easy/medium/hard labels and equivalent precomputed structural feature values
are unavailable; retain missingness rather than inventing values. The same rubric and
model do not remove differences in policy length, domain mix, source granularity, or
reference completeness. Equal dataset scores can be legitimate; greater difficulty is
not evidence of greater quality. Do not force a desired synthetic/native ordering.
