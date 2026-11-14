# Justifying scoring weights: 50% Coverage / 50% Difficulty (#80)

Parent: #61 · Formula/inputs: #60 · Handoff: #62
Branch checked: `codex/weekend-scoring-plan` @ `eedbab7` · Calculator: `difficulty/combined_weight_trials.py` · API calls: 0

## Result (Q = 100 × [0.5 C + 0.5 D])

| Dataset | Tasks | A (rep/decl) | E (mean group entropy) | C | D | Coverage contrib. | Difficulty contrib. | **Q** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| τ²-bench | 278 | 21/21 = 1.0000 | 0.9037 | 0.9518 | 0.6415 | 47.59 | 32.08 | **79.67** |
| Synthetic | 64 | 51/59 = 0.8644 | 0.8947 | 0.8795 | 0.6375 | 43.98 | 31.87 | **75.85** |

Unrounded values are in `trials.csv`. For both datasets, score = Coverage contribution + Difficulty contribution.

## What was verified (recomputed separately from the shared calculator)

- Coverage recomputed from the frozen labels/catalog matches the published `workflow_coverage_scores.csv` for all 10 groups (4 d.p.). Telecom conditions excluded from C.
- D uses FINAL v1.1 equal-task means: 64.15467625899281 (τ², 278) and 63.75 (synthetic, 64); all 342 tasks scored; internal weights 0.2 each.
- All 342 coverage task IDs match the difficulty task IDs.
- Frozen input snapshots have identical content to `main`, but each adds one trailing blank line, so their sha256 hashes differ from `main`'s files.
- Output matches the prepared 50/50 candidate row exactly.

## Comparison across the five settings

| Coverage / Difficulty | Synthetic Q | τ² Q | Gap (τ² − syn) | Change vs. 50/50 (syn / τ²) |
|---|---:|---:|---:|---:|
| 70 / 30 | 80.69 | 85.87 | 5.18 | +4.84 / +6.21 |
| 60 / 40 | 78.27 | 82.77 | 4.50 | +2.42 / +3.10 |
| **50 / 50** | **75.85** | **79.67** | **3.82** | — |
| 40 / 60 | 73.43 | 76.57 | 3.13 | −2.42 / −3.10 |
| 30 / 70 | 71.01 | 73.46 | 2.45 | −4.84 / −6.21 |

- Ordering never changes: τ² is higher on both C and D, so it leads at every weight. This follows from the inputs and is not validation.
- At 50/50, coverage accounts for 3.61 of the 3.82-point gap and difficulty for 0.20. Within coverage, the 8 of 59 declared synthetic workflows with no tasks cost 3.39 points; entropy costs 0.22.
- Five weight settings are policy choices, not independent samples, so no significance test applies.

## Rationale and limitations

50/50 is the neutral setting: it gives coverage and challenge equal standing because we have no validated evidence that one matters more, and it was not chosen because it favors either dataset. Its intended use is an exploratory, relative coverage-and-challenge summary shown alongside the component scores, not a replacement for them. The trade-off is that equal nominal weights are not equal influence: C differs between datasets far more than D, so even at 50/50 the gap is about 95% coverage-driven, mainly by synthetic's unfilled declared workflows. Limitations: catalogs are dataset-specific, synthetic entropy is inflated by singleton workflows (38 of 51 have one task), D is an LLM-designed index with `independent_validation: false`, the 0.5A/0.5E split is a trial assumption, and a stable ranking across weights is not independent validation.
