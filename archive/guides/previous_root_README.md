# Evaluation Framework for Agent Benchmark Datasets

## Numeric LLM designed difficulty (current roadmap)

The source-only numeric judge is implemented; paid calibration and scoring are pending.
Start with [the short guide](difficulty/design/README.md) and [the provisional rubric](docs/evaluation/numeric_design_rubric_v1.md).
It scores each test case from its scenario, workflow steps, milestones, tools and intended endpoint.
Historical feature profiles and execution results below remain separate supplementary work.

## Current designed difficulty workflow

Start with the [v0.3 profile guide](results/difficulty/designed_v3/README.md).
All 64 tasks now have source-backed global-rule applicability decisions as well
as operational units, repetition and coordination. Twelve task profiles gain
22 explicit operations/checks. Covered work is not counted twice, and uncertain
infrastructure duties remain separate. Earlier profiles and v0.1 scores are preserved.

```bash
python -m difficulty.designed_profiles_v3 --out results/difficulty/designed_v3_fresh
```

The [scope-clarified rules](docs/evaluation/design_counting_rulebook_v0.2.md)
apply to these profiles. There is no new combined score or new paid review.
The [earlier three-request LLM experiment](results/difficulty/design_review_run_v1/README.md)
used the previous frozen rulebook; it helped identify scope gaps but did not
validate v0.3. Its source-only review packets and outcome judge remain separate.
A future review of v0.3 needs a new explicit packet version, not reuse of old responses.

## Provisional designed difficulty for synthetic tasks

The first designed-complexity index covers all 64 synthetic tasks without API
calls or agent runs. Start with the [short results guide](results/difficulty/designed_v1/README.md)
and [64-task scores](results/difficulty/designed_v1/scores.csv).
The equal-weight 0–100 index combines task milestone action groups, reference
business-tool interactions and assistant-annotated business-check groups. It is
provisional, not independently validated, and not a failure probability. Exact
atomic action and independent decision counts are not claimed.

```bash
python -m difficulty.designed_difficulty --out results/difficulty/designed_fresh
```

Use a new output directory. Full evidence, source hashes and alternative-weight
ranks are saved with the scores. See the [method and counting rules](docs/evaluation/designed_difficulty_v0.1.md).
This command does not run embeddings, coverage or an outcome grader.

Optional attachment to the full framework uses
`--synthetic-designed-scores results/difficulty/designed_v1/scores.json` and adds
separate `designed_index_` columns. Historical empirical and write-count metrics
remain distinct. The older structural-feature-only option below does not compute
this combined index.

## Run the evaluation framework (issue #15)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py --seed 42
```

This computes **coverage** (normalized Vendi Score and Attribute Diversity)
and **structural difficulty** (ground-truth write-action counts) for the
committed 278-task τ²-bench base split and all 64 synthetic tasks.
It also recomputes empirical difficulty and Spearman validation using the
saved v2 τ²-bench baseline trials. It does not rerun agents or require an API key.
The public sentence-transformer model downloads on first use; its revision
is pinned and inference runs on CPU.

Outputs are saved under `results/framework/`:

- `metrics_summary.json`: overall scores, task counts, and limitations.
- `metrics_by_domain.csv`: overall and per-domain/category scores.
- `coverage_vendi.csv`, `coverage_attribute_scores.csv`,
  `coverage_attribute_counts.csv`: coverage scores and counts.
- `difficulty_tasks.csv`: structural and empirical scores for every task.
- `difficulty_validation.json`, `difficulty_scatter.png`: validation results.
- `run_metadata.json`: input/source hashes, seed, model revision, and versions.

Use `--output-dir` to keep runs separate. For example:

```bash
python run_all.py --seed 42 --output-dir /tmp/framework-repeat
```

Optionally attach the proposed synthetic designed-complexity features to a new
framework run:

```bash
python run_all.py --seed 42 --synthetic-structural-features results/difficulty/structural_v1/task_features.json --output-dir results/framework/structural_v1
```

This adds `designed_` columns to `difficulty_tasks.csv` for synthetic tasks and
records the feature file and its supplied-source hashes in `run_metadata.json`.
The input must match all synthetic task IDs exactly once and its source hashes
must still match. τ²-bench receives blank designed-feature columns. Existing
metrics and write-count correlations are unchanged; no new feature correlations
or combined difficulty score are computed. The summary marks new-signal validation
as awaiting validated outcomes. The seven AI-reviewed structural examples do not
replace the independent judge-review study. See the
[counting rules](docs/evaluation/structural_feature_rules.md) for limitations.

The synthetic baseline runner and evaluation protocol are documented in
[`baseline/SYNTHETIC_BASELINE.md`](baseline/SYNTHETIC_BASELINE.md).
When `results/baseline/v2_synthetic_full/trials.csv` exists, the framework
automatically includes its empirical scores. Invalid-reference tasks remain
unscored, not zero. `--synthetic-trials path/to/trials.csv` selects another
saved run using the same fixed baseline settings.
Trial columns are `domain,task_id,trial,reward,passed` (additional columns
are allowed). Use the original synthetic agent-category domain and processed
task ID. Only trials with rewards enter the empirical denominator; duplicate
trials and unknown task IDs are rejected. Do not combine the old v1 pilot
with the v2 full baseline. `--tau-trials` selects a different saved tau run.

Synthetic Attribute Diversity uses four broad domains, while its Vendi and
write-count breakdowns use seven agent categories. Tool entropy retains the
existing observed-vocabulary definition. Vendi VS/n depends on sample size
and repeated descriptions; higher difficulty does not imply higher quality.

Run the focused checks with `python -m unittest discover -s tests -v`.
The framework reads the committed task file, so a local tau2-bench clone
is not needed for this command.


## Repository layout

- `data/`: supplied synthetic tasks and tools, data loaders, and the committed unified task file.
- `coverage/` and `difficulty/`: metric implementations and reviewed input labels.
- `baseline/`: original baseline runners, synthetic reference grader, and evaluation protocol.
- `labeling/`: tools for generating and reviewing coverage labels.
- `tests/`: core framework and original synthetic baseline tests.
- `experiments/onboarding_pilot/`: separate revised six-scenario environment, outcome grader, and its tests. See [the pilot guide](experiments/onboarding_pilot/README.md).
- `results/framework/`: combined framework outputs.
- `results/baseline/`: current full tau2 and original synthetic baseline evidence.
- `results/coverage/` and `results/difficulty/`: standalone metric outputs and validation evidence.
- `results/labeling/`: generated label exports, review sheets, and local labeling cache. Reviewed framework inputs remain in `coverage/labels/`.
- `results/experiments/`: onboarding pilot results, kept outside the benchmark comparison.
- `results/archive/`: earlier baseline runs and the initial runtime/cost pilot. See [the archive guide](results/archive/README.md).

The standalone metric scripts now write into `results/coverage/` or
`results/difficulty/`, rather than beside their source code. Existing result
files were relocated without recomputing their scores. Recorded manifests
retain historical paths and hashes; see [the results guide](results/README.md).

Run the optional pilot checks separately, without API calls:

```bash
python -m unittest discover -s experiments/onboarding_pilot/tests -v
python -m experiments.onboarding_pilot.run --validate-only
python -m experiments.onboarding_pilot.run --regrade
```

The pilot uses revised fixtures and is not a replacement for the original
synthetic benchmark. Its recorded results must not be merged with the original
64-task comparison. Local virtual environments and the tau2 checkout are
ignored by Git and are not repository deliverables.

## Synthetic grading rubric review

Issue #45's proposed rubric is in
[the milestone rubric](docs/evaluation/synthetic_milestone_rubric.md).
[The evidence review](results/rubric_review/v1/review.md) covers 16 saved attempts
across all seven synthetic categories and records open adjudication questions.
It is an author draft awaiting independent team review, not a replacement grader
or a new set of empirical scores.

Reproduce the offline diagnostics without API calls:

```bash
python -m baseline.review_synthetic_rubric
```

The diagnostics replay supplied reference calls for execution checks and inspect
saved trace metadata. A reference matching itself does not independently verify
outcome correctness. Original data, rewards, traces, and framework outputs are
preserved. Named reviewers and final rubric/denominator decisions remain pending.
