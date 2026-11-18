# Weight trial review: Coverage 70% / Difficulty 30% (#78)

Reviewer: Zayd (@zaydn4321). Part of #61; handoff to #62. Offline arithmetic and interpretation review with zero API calls, agent runs, embeddings or LLM reruns. This is one of five sensitivity trials and does not select the final weights.

## Command

Run on `codex/weekend-scoring-plan` at commit `9cc1814`. The calculator and frozen inputs are byte-identical to `eedbab7`, the base the other reviewers used.

```bash
python -m difficulty.combined_weight_trials \
  --labels results/scoring/weekend_weight_trials_v1/inputs/workflow_labels.csv \
  --catalog results/scoring/weekend_weight_trials_v1/inputs/workflow_catalog.csv \
  --difficulty results/difficulty/designed_final_v27/task_scores.json \
  --coverage-weight 0.70 --out results/scoring/weight_trial_zayd_70_30
python results/scoring/weight_trial_zayd_70_30/verify_review.py
```

SHA-256 fingerprints, from `provenance.json`:

- labels: `78a25ddf…`
- catalog: `5afaa14e…`
- `task_scores.json` (v1.1): `a4563611…`
- calculator: `ac692c82…`

## Results

`Q = 100 × (0.70 C + 0.30 D)`, `C = 0.5 A + 0.5 E`.

| Dataset | A | E | C | D | Coverage contrib. | Difficulty contrib. | **Q** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tau2 | 21/21 = 1.0000 | 0.9037 | 0.9518 | 0.6415 | 66.63 | 19.25 | **85.87** |
| synthetic | 51/59 = 0.8644 | 0.8947 | 0.8795 | 0.6375 | 61.57 | 19.12 | **80.69** |

In each row, Q equals the Coverage contribution plus the Difficulty contribution to full precision (within 1e-12; see `trials.csv`). Because each displayed value is rounded separately, the displayed contributions can sum to 0.01 more or less than the displayed Q.

## Compared with the 50/50 baseline

| | 50/50 | 70/30 | Change |
| --- | ---: | ---: | ---: |
| tau2 | 79.67 | 85.87 | +6.21 |
| synthetic | 75.85 | 80.69 | +4.84 |
| Gap (tau2 − synthetic) | 3.82 | 5.18 | +1.36 |

- **Ordering does not change.**
- **Both scores rise** because each dataset's C is higher than its D. This is an effect of the weights, not of better data.
- **The gap is linear in the weight:** `gap = 100 × (w ΔC + (1 − w) ΔD)`, with ΔC = 0.0723 and ΔD = 0.0040. It runs from 0.40 points at all-difficulty to 7.23 at all-coverage. Both differences favour tau2, so tau2 leads under every convex weighting.
- **Not a statistical test:** five policy settings are not independent samples, and a stable ranking is not independent validation.

## Independent checks (`verify_review.py` → `verification.json`)

The check script recomputes everything from the raw files and does not import the calculator.

- **Inputs match main.** The frozen labels, catalog and coverage-score snapshots parse to the same rows and values as `origin/main`'s coverage files.
- **Task inventory.** All 342 task identities match exactly between coverage and difficulty, after stripping the tau2 domain prefix.
- **Coverage.** A and E were recomputed per group from the labels and catalog. All 10 workflow groups match the published rounded `workflow_coverage_scores.csv`. Telecom conditions are excluded from E, so they stay a separate diagnostic. Vendi is not used.
- **Difficulty.**
  - The release is `designed_difficulty_v1.1_required_path` and all 342 tasks are scored.
  - The means are exactly 64.15467625899281 for tau2 and 63.75 for synthetic, not the older 65.35/64.30.
  - Every task score equals 5 × the sum of its five 0–4 ratings, so the five internal dimensions are confirmed at 20% each.
- **Scores.**
  - Contributions and Q match `100 × (0.7C + 0.3D)` for both datasets.
  - Each Q lies between its C and D.
  - The prepared `zayd` 70/30 and `divya` 50/50 candidate rows were reproduced independently. They were checked, not copied.
- **No min–max normalisation** is applied.

## Rationale and limitations

A 70/30 setting fits an index whose main purpose is to show whether a benchmark spans the workflows it declares, and spans them evenly, with designed challenge as a secondary signal. The tradeoff is that it puts most of the weight on the component that separates these two datasets, so the gap widens from 3.82 to 5.18 points with no new evidence about quality. Each group's coverage is scored against its own declared catalog, and the 50/50 split of C into A and E is a trial assumption, not the coverage author's scalar. As a result, a dataset with a small or loosely defined catalog can score high, and the two catalogs are not directly comparable. Difficulty here is a designed LLM rating, not measured agent performance, and harder does not always mean better. Q should be read as an exploratory, relative coverage-and-challenge comparison of these two datasets, not a validated quality ranking. I would keep 70/30 as the coverage-heavy sensitivity bound rather than the headline weighting.
