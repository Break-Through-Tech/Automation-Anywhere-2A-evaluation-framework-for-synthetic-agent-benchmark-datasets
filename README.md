# Agent Benchmark Evaluation Framework

Evaluate **workflow coverage** and **designed task difficulty** for synthetic tasks and τ²-bench. Task designs are assessed without running task agents. Historical execution experiments are supplementary evidence.

## Start here

- **Current difficulty results:** [dataset scores, domain charts and all task scores](results/difficulty/designed_final_v27/README.md). τ²-bench **64.15/100** (278 tasks); synthetic **63.75/100** (64 tasks).
- **Method:** [designed-difficulty v1.1](docs/evaluation/designed_difficulty_metric_v1.1.md). Five evidence-backed dimensions, 20% each. These are interpretive complexity scores, not correctness or universal quality scores.
- **Coverage and combined weighting:** [frozen workflow coverage inputs and five trial weights](results/scoring/weekend_weight_trials_v1/README.md). Vendi remains a separate diagnostic. The selected project reporting convention is 50% Coverage / 50% Difficulty; see [the combined scores and rationale](results/scoring/final_index_v1/README.md).
- **Your completed review:** [Mila’s 30% Coverage / 70% Difficulty comparison](results/scoring/mila_weight_review_v1/README.md).
- **Team handoff:** [weekend scoring plan](docs/evaluation/weekend_scoring_plan.md) and [report template](docs/evaluation/weekend_final_report_template.md).

## Reproduce current difficulty without API credits

Install the dependencies in `requirements.txt`, then run from the repository root. The original synthetic sources and the native τ²-bench checkout at the recorded revision are required; see the current results guide for provenance. Choose fresh output directories.

```bash
python -m difficulty.reproduce_clarified_design \
  --report-dir results/difficulty/designed_final_v27 \
  --out .cache/replayed_clarified_v27
python run_all.py --difficulty-mode source-only \
  --design-clarified-packet .cache/replayed_clarified_v27 \
  --output-dir .cache/framework_clarified_v27
```

These commands replay saved judgments and verify the same scores. They do not run agents, call an API or download embeddings. New model judgments require separate approval; no past API allowance is renewed by this cleanup.

## Repository layout

- `run_all.py`: framework entry point; source-only replay and historical coverage/execution modes.
- `difficulty/`: current numeric judge, source adapters, evidence validation, replay and weighting calculator. Some supporting modules remain for existing optional framework flags and complementary structural checks; see [the code guide](difficulty/README.md).
- `coverage/`: coverage calculations and reviewed labels. Latest workflow coverage used by the weight trials is frozen under `results/scoring/weekend_weight_trials_v1/inputs/`.
- `data/`: supplied tasks and processed framework input; unchanged by this cleanup.
- `baseline/`: saved-attempt tooling and historical empirical metrics.
- `tests/`: maintained offline checks for the current framework and supported options.
- `results/`: [current reports and retained supporting evidence](results/README.md).
- `docs/evaluation/`: [current methods and project handoffs](docs/evaluation/README.md).
- `archive/`: [superseded runs, guides and retired helpers](archive/README.md), preserved for audit rather than presented as current results.
- `experiments/`: separate revised onboarding pilot; it is not the original synthetic benchmark.
- `labeling/`: label preparation tools. `tau2-bench/`, local credentials and caches remain ignored.

The historical full report mode is still available with `python run_all.py --seed 42 --output-dir results/framework_fresh`. That mode may download the pinned embedding model on first use and reports the earlier coverage/empirical metrics; it does not select the new Coverage/Difficulty headline weights. Its original instructions and optional flags are retained in [the historical framework guide](archive/guides/previous_root_README.md).
