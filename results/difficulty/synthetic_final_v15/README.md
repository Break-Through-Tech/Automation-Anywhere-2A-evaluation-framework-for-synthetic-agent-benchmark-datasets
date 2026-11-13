# Synthetic designed difficulty: 64.30 / 100

**All 64 original synthetic tasks were scored. No tasks were excluded.** This is the
final computed dataset result under the current provisional rubric, using GPT-6 Sol
and source documents only. No task agent was executed.

## How to use this result

Use **64.30/100** as this run's synthetic designed-difficulty index. Open
[the chart](score_overview.png) for the distribution and domain means, or
[the readable task CSV](task_scores_readable.csv) to inspect any of the 64 task scores.
The complete audit is in [audit/run_manifest.json](audit/run_manifest.json) and the
adjacent raw-output/source-binding files. These files preserve evidence and versions.

## Calculation

Each task receives five integer levels from 0 to 4: workload, reasoning, tool use,
dependencies/coordination, and information discovery. Each dimension contributes 20%:

`task score = 5 × (workload + reasoning + tool use + dependencies + information)`

The dataset score is the equal-weight arithmetic mean of all 64 task scores:

`4,115 ÷ 64 = 64.296875`, reported as **64.30**.

The median is **65**; task scores range from **40 to 75**; the middle 50% range from
**60 to 70**. The scale describes anticipated design complexity, not an execution-success
percentage or a percentile rank. For context, five level-2 ratings give 50, and five
level-3 ratings give 75. No task or domain is rescaled to force a desired dataset ordering.

## Domain summaries

- Accounts/deposits: **66.25**, 8 tasks.
- Customer onboarding: **69.17**, 6 tasks.
- Fraud monitoring: **64.23**, 13 tasks.
- Patient onboarding: **64.44**, 9 tasks.
- Prior authorization: **60.00**, 9 tasks.
- Insurance claims: **67.00**, 10 tasks.
- Manufacturing purchase-to-pay: **60.56**, 9 tasks.

Every task has equal weight in the dataset mean; domains have different numbers of tasks.
The chart's lines span scores across tasks, not confidence intervals.

A status-reporting PA task scored **40**, because the selected path mainly retrieves
and communicates an approved decision. Document-remediation and address-reconciliation
onboarding examples scored **75**, reflecting linked work, tool bindings, required
external documents and reconciliation. Equal scores can be legitimate even where the
underlying task descriptions differ.

## What resolved the grader failures

The API rejection was diagnosed: natural-language excerpt values containing quote
characters were rejected inside strict schema enums. The corrected schema uses short
evidence IDs. The judge selects IDs from a source-bound index; the application expands
them to exact source IDs and excerpts. **No numerical judgments are changed.** Original
wire responses and resolved judgments are both retained. Unknown IDs, invented units,
invalid arithmetic, missing required assessments and inconsistent evidence are rejected.

All **64/64 responses** passed these checks in the final run. The first three calls were
the pilot and count toward 64, rather than being repeated. No older-format task scores
were pooled into this result. **153 offline tests passed.** The real framework command
regenerated exactly the same complete task report, without API calls. Raw wire scores
sum to the same 4,115 points as the canonical saved scores. Source hashes were verified
again after scoring, and supplied task/fixture files were not edited.

## Interpretation limits and complementary checks

The rubric and five equal weights remain provisional; there are no independent gold
numeric difficulty labels. This run uses **one judgment per task**, so it does not
estimate repeated-run uncertainty for every final score. Earlier repeat/controlled
experiments used previous generation formats and remain separately labeled evidence.
This score does not verify that tools execute successfully or that environments are
feasible. Judge source-quality notes are observations for review, sometimes including
general evaluation boundaries; they are not adjudicated defect counts.

Supplied easy/medium/hard tags were hidden during grading and joined afterward. Their
association with these scores is weak: Spearman **ρ=0.187**, n=64, approximate p=0.138.
Associations with operations, reference calls, business checks and coordination are
**0.426, 0.622, 0.375 and 0.467**. These checks share source information with the judge;
ties, workflow clustering and multiple comparisons limit inference. Tags are annotations,
not verified truth. No weights were tuned after viewing these associations. See
[crosschecks.json](crosschecks.json) for within-workflow comparisons and full missingness.

This report contains the synthetic dataset result only. A final native τ²-bench score
and a complete cross-dataset comparison are separate work.

## Audit and reproduction

The run uses schema `design_schema_v1.4_source_evidence_refs`, prompt
`design_prompt_v1.3`, evidence validator `design_evidence_validation_v1.3` and rubric
`design_numeric_v1.0_provisional`, with model `gpt-6-sol`, low reasoning effort and a
10,000-token output cap. Exact input/model/raw-response hashes and usage are retained.
The run made 64 model-generation calls; the separate diagnostic HTTP 400 attempt is
preserved outside this cohort. No dollar charge or API-account ownership is inferred.

`task_scores.json`/`summary.json` contain machine-readable scores and coverage;
`audit/judgment_evidence.json` contains raw model output, model-selected IDs and exact
resolved source excerpts. `audit/source_bindings.json` retains source pointers and frozen
implementation fingerprints. Use the recorded implementation revision for regeneration;
do not rewrite old manifests to bypass a fingerprint mismatch.
