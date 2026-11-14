# Weight trial review: Coverage 60% / Difficulty 40% (#79)

Reviewer: Ronnit (@ronnitrana). Part of #61, handoff to #62.

## Command

Run from `codex/weekend-scoring-plan` (commit `eedbab7`), zero API calls:

```bash
python -m difficulty.combined_weight_trials \
  --labels results/scoring/weekend_weight_trials_v1/inputs/workflow_labels.csv \
  --catalog results/scoring/weekend_weight_trials_v1/inputs/workflow_catalog.csv \
  --difficulty results/difficulty/designed_final_v27/task_scores.json \
  --coverage-weight 0.60 --out results/scoring/weight_trial_ronnit_60_40
```

Input fingerprints (SHA-256, from `provenance.json`):

- `workflow_labels.csv`: `78a25ddf9142d3c9…`
- `workflow_catalog.csv`: `5afaa14e13efa4d1…`
- `task_scores.json` (difficulty v1.1): `a4563611e88ae82c…`

## Results

| Dataset | A (workflows) | E (mean entropy) | C | D | Coverage contribution | Difficulty contribution | Q |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tau2 | 21/21 = 1.0000 | 0.9037 | 0.9518 | 0.6415 | 57.11 | 25.66 | **82.77** |
| synthetic | 51/59 = 0.8644 | 0.8947 | 0.8795 | 0.6375 | 52.77 | 25.50 | **78.27** |

In both rows, Q equals the Coverage contribution plus the Difficulty contribution, to full precision.

## Checks I ran independently

To verify the calculator’s output, I recomputed the values independently from the input files and compared them with it.

- **Inputs match main.** The frozen labels and catalog snapshots have the same 342 rows, 80 workflows and every value as main's `coverage/labels/workflows/` files. The SHA-256 hashes differ from main's files at the byte level only, not in content. The snapshot `workflow_coverage_scores.csv` is identical to main's.
- **Coverage.** I recomputed A and E from the labels and catalog (a task with several workflows counts once per workflow; zero-task workflows stay in the catalog). All 10 groups match the published rounded coverage CSV. The tau2 E averages airline, retail and telecom workflows; telecom conditions are excluded, as specified.
- **Difficulty.** I recomputed D from the 342 task scores: tau2 64.15467625899281 and synthetic 63.75, matching FINAL v1.1 (not the older 65.35/64.30). All tasks are scored, and the five internal weights are 0.2 each.
- **Scores.** Q = 100 × (0.6C + 0.4D) matches the calculator exactly for both datasets. It also matches the prepared candidate row for this setting.

## Compared with the 50/50 baseline

| Dataset | 50/50 | 60/40 | Change |
| --- | ---: | ---: | ---: |
| tau2 | 79.67 | 82.77 | +3.10 |
| synthetic | 75.85 | 78.27 | +2.42 |
| Gap (tau2 − synthetic) | 3.82 | 4.50 | +0.68 |

The ordering does not change. The gap equals 100 × (w × ΔC + (1 − w) × ΔD), where ΔC = 0.0723 and ΔD = 0.0040. Both differences favor tau2, so tau2 scores higher for every coverage weight from 0 to 1. The gap grows steadily from 0.40 points (all difficulty) to 7.23 points (all coverage). Almost all of the separation comes from coverage, since the two datasets' difficulty means differ by only 0.4 points.

Both scores rise at 60/40 because each dataset's C is higher than its D. The rise reflects the change in weights, not better datasets, so only the relative positions are meaningful.

With two datasets and five weight choices, these results are a sensitivity check, not a statistical test. The ranking staying the same is not independent evidence that the index is valid.

## Rationale and limitations

A 60/40 setting fits an index meant to show whether a benchmark tests the workflows it declares, while still giving difficulty a meaningful share. The tradeoff is that it gives the most weight to the component that separates these two datasets, so the gap widens (4.50 vs 3.82 points) without any new evidence about quality. Coverage scores each group against its own declared catalog, and the 50/50 split of C into A and E is a trial assumption, so a dataset with a small or incomplete catalog can still score well. Difficulty is a designed LLM rating rather than agent performance, and harder does not always mean better. This index should be read as an exploratory relative coverage-and-challenge comparison between these two datasets, not a validated quality ranking.
