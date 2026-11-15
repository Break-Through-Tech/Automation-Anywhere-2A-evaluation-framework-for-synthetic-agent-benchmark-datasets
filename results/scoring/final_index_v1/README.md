# Selected Coverage-and-Challenge Index — #61 / #62

**Reporting convention: 50% Coverage / 50% designed Difficulty.**

- **τ²-bench: 79.67/100** = 47.5918413578 Coverage contribution + 32.0773381295 Difficulty contribution.
- **Synthetic: 75.85/100** = 43.9772743934 Coverage contribution + 31.875 Difficulty contribution.
- Gap: **3.82 points**. Approximately 95% of this gap comes from Coverage. Separately rounded contributions can differ by 0.01 from displayed totals.

This operational selection follows Mila’s instruction to use the most appropriate convention and the completion of all five reviews. Equal nominal weights give coverage and challenge equal standing when no validated priority is established. This is a project reporting choice, **not** reviewer consensus, Sandra approval, an empirically optimal weighting or independently validated universal dataset quality. Keep component scores and all sensitivity settings visible.

## What was consolidated

- Zayd, #78 / [PR #83](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/pull/83): 70/30, τ² 85.87 and synthetic 80.69. He recommends retaining this as the coverage-heavy sensitivity bound.
- Ronnit, #79: 60/40, τ² 82.77 and synthetic 78.27; coverage-priority rationale and catalog limitations.
- Divya, #80: 50/50, τ² 79.67 and synthetic 75.85; equal-standing rationale and coverage-dominated gap.
- Sana, #81: 40/60, τ² 76.57 and synthetic 73.43; challenge-priority rationale and reduced separation. Her issue comment supplies rounded totals/rationale rather than an attached raw CSV; that distinction is retained.
- Mila, #82: 30/70, τ² 73.46 and synthetic 71.01; assistant-supported challenge-heavy sensitivity review, not independent human validation.

`review_sources.json` preserves the retrieved review texts, source URLs and Git blob IDs where available. Zayd’s full PR is not merged here: its changed-file list contains substantial earlier branch history. His seven review files are evidence for consolidation, not authorization to merge unrelated changes.

## Frozen calculation

Use `Q = 100 × (0.5 C + 0.5 D)`.

`C = 0.5 A + 0.5 E`, where A is pooled represented/declared workflows and E is unweighted mean normalized workflow entropy across groups. This internal Coverage split remains an explicit project convention. `D` is the finalized v1.1 equal-task designed-difficulty mean divided by 100; the five internal difficulty weights remain 20% each. Vendi and telecom conditions stay separate diagnostics. No two-dataset min–max normalization is used.

τ² C = 0.9518368271555027, D = 0.641546762589928; synthetic C = 0.8795454878670201, D = 0.6375. Underlying Difficulty remains **64.15** and **63.75**, respectively; combined scores are a different measure.

## Sensitivity and limitations

Moving Coverage weight from 30% to 70% changes τ² Q from 73.46 to 85.87, synthetic from 71.01 to 80.69, and the gap from 2.45 to 5.18. τ² is higher on both components, so it leads at every convex weighting by arithmetic. This is not validation, a significance test or a reason to select a preferred winner. Five choices are policies, not independent observations.

Equal weights do not mean equal observed influence: Coverage differs much more between these datasets than Difficulty. Catalog definitions and group counts differ; entropy weights groups equally while Difficulty weights tasks equally. Synthetic has 8/59 unrepresented workflows and 38 singleton represented workflows. LLM-designed complexity is interpretive; higher difficulty does not establish higher quality or actual agent failure. These limits remain in downstream figures and recommendations.

## Files and reproduce

`scores.csv/json` contain the selected index and contributions. `trials.csv/json` retain all five recalculated sensitivity settings; their candidate status describes the alternatives, while `scores.json` records the selection. `inputs.json` and `provenance.json` retain component values and fingerprints. `verification.json` distinguishes exact CSV checks from comment-only checks.

Run the shared calculator with the frozen inputs from `results/scoring/weekend_weight_trials_v1/inputs/`, the finalized `results/difficulty/designed_final_v27/task_scores.json`, and a fresh output directory. Then `python results/scoring/final_index_v1/consolidate.py` reproduces this selection and verifies the retrieved CSVs. All work is offline: no agents, embeddings or API calls.

## Downstream handoff

#61’s five-setting review and #62’s combined-score calculation are complete under this reporting convention. #63–#66 can use these outputs for comparison and domain analysis, while preserving component scores and task counts. Final advisor endorsement and independent metric validity are not claimed. The original trial reports are retained unchanged.
