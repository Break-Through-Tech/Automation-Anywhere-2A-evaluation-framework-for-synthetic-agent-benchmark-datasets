# Weekend weight trials — review candidates, not final selected weights

Five settings are prepared for teammate review, using zero API calls. The 342 coverage task IDs match the finalized difficulty inventory exactly after stripping the native domain prefix.

The proposed index is `Q = 100 × [wC + (1 − w)D]`, where:

- `C = 0.5 × catalog completeness + 0.5 × mean group workflow entropy`.
- Catalog completeness uses all represented/declared workflows; entropy is averaged equally across groups, matching the coverage README's descriptive convention. This C formula is a new trial assumption, not a claim that the coverage author already defined this scalar.
- `D = finalized v1.1 difficulty / 100`, using unrounded saved task means. The five internal difficulty weights remain 20% each.

Coverage catalogs differ between datasets, and difficulty is not a quality theorem. Treat Q as an **exploratory relative coverage-and-challenge index**, not a validated universal dataset-quality ranking. Vendi and telecom conditions remain separate diagnostics. No per-dataset min–max rescaling or desired-winner tuning is used.

## Assignments and handoffs

1. Zayd: 70% C / 30% D.
2. Ronnit: 60% / 40%.
3. Divya: 50% / 50%, the neutral comparison baseline.
4. Sana: 40% / 60%.
5. Mila: 30% / 70%.

Formula/input freeze: Saturday November 14 noon. Reviewer handoff: Saturday 6 PM, America/New_York. Mila consolidates the selected convention and scores under #62 by Saturday end of day. The JSON/CSV contains illustrative calculated candidates so reviewers can check arithmetic consistently; it does not mean reviewers have completed their work or that final weights have been selected.

Each reviewer must run their parameter, verify exact inputs and contributions, compare to 50/50, and supply a brief rationale, practical sensitivity and limitations. With only two datasets and five policy choices, do not invent a statistical significance test or call stable rankings proof of validity. Choose weights from the intended use, not which dataset wins.

## Reproduce your setting

Example for Zayd (change 0.70 and output suffix for another setting):

```bash
python -m difficulty.combined_weight_trials \
  --labels results/scoring/weekend_weight_trials_v1/inputs/workflow_labels.csv \
  --catalog results/scoring/weekend_weight_trials_v1/inputs/workflow_catalog.csv \
  --difficulty results/difficulty/designed_final_v27/task_scores.json \
  --coverage-weight 0.70 --out .cache/weight_trial_zayd
```

Omit `--coverage-weight` to calculate all five settings into a fresh output directory. The module rejects incomplete/mismatched task inventories, duplicate/unknown workflow labels, nonfinite scores and wrong difficulty releases. It never calls an LLM, runs agents or downloads an embedding model.

Deliver `trials.csv`, `provenance.json`, and a short review note. Keep full precision in the saved calculation; round only presentation to two decimals. Each score must equal its separate Coverage and Difficulty contributions.

## Sources and verification

Coverage inputs are frozen snapshots of main's `coverage/labels/workflows/workflow_labels.csv`, `workflow_catalog.csv` and `results/coverage/workflow/workflow_coverage_scores.csv`. Source README: https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/blob/main/results/coverage/workflow/README.md.

We recompute unrounded completeness/entropy from the labels/catalog and check them against the rounded published coverage CSV. No supplied source data, coverage definitions or finalized difficulty values are changed. All five settings share one snapshot and normalization. Six focused offline tests passed.

Use `verification.json` for recomputation and identity checks, `inputs.json` for actual components, `trials.csv/json` for candidate results, and `provenance.json` for input/code fingerprints. See the [weekend plan](../../../docs/evaluation/weekend_scoring_plan.md) and [report scaffold](../../../docs/evaluation/weekend_final_report_template.md).
