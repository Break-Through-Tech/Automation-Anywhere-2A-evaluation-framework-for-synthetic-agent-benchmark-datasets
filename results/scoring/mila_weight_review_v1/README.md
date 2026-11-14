# Mila’s 30% Coverage / 70% Difficulty review — #82

Completed on Mila’s request with assistant support; this is an arithmetic and interpretation review, not independent human validation. No API credits were used. This completes the assigned sensitivity trial; it does not select the final project weights.

## Results and comparison

- **τ²-bench: 73.46/100** = Coverage contribution 28.56 + Difficulty contribution 44.91 (rounded separately). At 50/50 it is 79.67, so this setting lowers it by **6.21 points**.
- **Synthetic: 71.01/100** = Coverage contribution 26.39 + Difficulty contribution 44.63 (rounded separately). At 50/50 it is 75.85, so this setting lowers it by **4.84 points**.
- The τ²-minus-synthetic gap narrows from **3.82 to 2.45 points** (a reduction of **1.36 points**). Ordering does not change.

Calculations use full precision; sums of separately rounded displayed contributions may differ by 0.01 from the displayed total. Exact contributions and the comparison are in `trials.csv` and `comparison.csv`.

## Rationale for the team handoff

This 30/70 setting suits an index that prioritizes designed challenge while retaining a smaller reward for workflow coverage and balance. Both scores decrease relative to 50/50 because their normalized difficulty components are lower than their coverage components, not because either dataset changed. The smaller gap reflects their similar finalized difficulty means, 64.15 and 63.75. τ² is higher on both components, so its lead under every convex weighting is mathematically expected and does not validate these weights or establish universal dataset quality. I recommend retaining 30/70 as the challenge-heavy sensitivity option and selecting headline weights only after consolidating all five reviews against the intended project use.

## Inputs and independent checks

The shared trial convention is `Q = 100 × (0.30 C + 0.70 D)`, with `C = 0.5 A + 0.5 E`: A is pooled represented/declared workflows, and E is mean normalized workflow entropy across groups. D is the finalized v1.1 equal-task difficulty mean divided by 100; its five internal weights stay at 20% each. Vendi and telecom conditions remain separate diagnostics.

- τ²: 278 tasks, 21/21 workflows, mean entropy 0.9036736543110052, C = 0.9518368271555027.
- Synthetic: 64 tasks, 51/59 workflows, mean entropy 0.8946841960730232, C = 0.8795454878670201.
- Independently recomputed counts, entropy, dataset difficulty means, 30/70 contributions, 50/50 totals, changes and gaps without importing the shared calculator. All 342 task identities match exactly; all 10 coverage groups match the published rounded coverage CSV. Contributions sum to the shared output within floating-point tolerance; totals lie between their component scores.
- `verification.json` records the checks, `provenance.json` fingerprints source files and the shared calculator, and `verify_review.py` reproduces the independent arithmetic check from the repository root. The snapshots are preserved byte-for-byte; trailing blank lines have no effect on parsed CSV calculations.

Different workflow catalogs, group counts and aggregation units limit cross-dataset comparisons: completeness is pooled over workflows, entropy averages groups equally, and difficulty averages tasks equally. Small synthetic groups and curated labels affect coverage interpretation; LLM difficulty judgments remain interpretive. The 50/50 reference is a comparison convention, not an approved optimal weighting. Five policy settings are not independent observations for a statistical significance test, and none should be chosen to produce a preferred winner.

## Reproduce

From the repository root, with the code and frozen inputs on `codex/weekend-scoring-plan`:

```bash
python -m difficulty.combined_weight_trials \
  --labels results/scoring/weekend_weight_trials_v1/inputs/workflow_labels.csv \
  --catalog results/scoring/weekend_weight_trials_v1/inputs/workflow_catalog.csv \
  --difficulty results/difficulty/designed_final_v27/task_scores.json \
  --coverage-weight 0.30 --out .cache/mila_weight_trial_fresh
python results/scoring/mila_weight_review_v1/verify_review.py
```

Choose a fresh output directory for the shared calculator. Review handoff: #82 → #61 → #62. All files here are offline calculations; no supplied tasks or finalized difficulty judgments were altered.
