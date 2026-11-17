# Difficulty code — current and supporting modules

## Current deliverable

Start with [the finalized 342-task results](../results/difficulty/designed_final_v27/README.md) and [v1.1 method](../docs/evaluation/designed_difficulty_metric_v1.1.md). τ²-bench: **64.15/100**; synthetic: **63.75/100**. This is designed complexity, not agent correctness.

- `design/`: task adapters, numeric rubric, source evidence, model-response validation and report utilities. [Source-only guide](design/README.md).
- `clarified_design_run.py`: v1.1 request validation, bounded execution and saved-judgment reporting.
- `clarified_framework.py`: source-only integration with `run_all.py`.
- `reproduce_clarified_design.py`: restore the published archive and verify exact scores offline.
- `combined_weight_trials.py`: offline Coverage/Difficulty sensitivity calculations; no final combined weights have been chosen.
- `required_path_calibration.py`, `required_path_probe.py`, `required_path_repeatability.py`: shared clarification/prompt and calibration checks used by the current release. Despite their development names, they remain dependencies and must not be removed.

The source files inside `design/`, the rubric and prompt addendum retain the bytes needed by the frozen replay. Documentation refreshes do not redefine the scoring anchors.

## Supported complementary and historical procedures

`native_design_crosschecks.py`, `native_semantic_profiles.py`, `designed_profiles_v2.py`, `designed_profiles_v3.py`, `compare_designed_scoring.py` and their annotations support source-backed structural comparisons. `designed_difficulty.py` and `structural_features.py` also support existing optional `run_all.py` flags. Their saved fixtures remain in `results/difficulty/` because code and tests read them; their scores do not replace v1.1.

`llm_judge.py`, `environment_policy.py`, `judge_evidence.py`, `judge_review.py`, `saved_trials.py`, `compare_judge_reviews.py`, `judge_canary.py` and `audit_evaluability.py` concern saved execution attempts. They serve a different purpose from designed difficulty and remain supported. `write_counts.py` and the tool-label CSVs support the historical framework.

`reproduce_numeric_design.py` replays the superseded original prompt; pass the relocated report explicitly:

```bash
python -m difficulty.reproduce_numeric_design \
  --report-dir archive/results/difficulty/tau2_final_v19 \
  --out .cache/replayed_original_protocol
```

Current replay instructions are in the root README. Historical execution-judge commands and review history are in [the archived judge guide](../archive/guides/previous_difficulty_README.md); its time-sensitive pending-status statements describe earlier stages. Archived helper scripts and their tests are historical source snapshots, not maintained package entry points.
