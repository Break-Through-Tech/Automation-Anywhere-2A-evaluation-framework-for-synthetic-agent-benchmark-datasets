# Results — current reports first

## Current deliverables

- [Designed difficulty v1.1](difficulty/designed_final_v27/README.md): all 342 tasks, dataset/domain scores, charts, uncertainty and replay archive. τ² **64.15/100**; synthetic **63.75/100**.
- [Coverage/Difficulty weight trials](scoring/weekend_weight_trials_v1/README.md): frozen workflow coverage inputs and five candidate settings, with Vendi separate. These are exploratory index candidates, not final selected weights or a universal quality ranking.
- [Mila’s completed 30/70 review](scoring/mila_weight_review_v1/README.md): checked scores and comparison with 50/50.
- [Side-by-side comparison (#63)](comparison/side_by_side_v1/README.md): tables and figures for the selected 50/50 combined index, Coverage and Difficulty, plus all five sensitivity settings.

## Retained supporting evidence

`difficulty/native_crosschecks_v20` and `difficulty/native_semantic_v25` contain complementary structural diagnostics, not replacement numeric scores. `difficulty/structural_v1`, `designed_v1`, `designed_v2`, `designed_v3` and `design_review_run_v1` are retained because supported modules/tests consume those fixtures. Root-level difficulty CSVs and `framework/` describe the earlier structural/empirical report mode.

`coverage/` contains historical coverage exports. The workflow coverage release used by the weekend trials is copied into their frozen `inputs/` directory with source provenance; these files do not silently replace the earlier attribute/Vendi outputs.

`baseline/v2_full/` and `baseline/v2_synthetic_full/` are the original saved attempt evidence, including trial CSVs and relative trace paths. `judge_review/`, `rubric_review/` and `evaluability/` support the separate saved-execution analysis. `labeling/` contains generated review exports; active reviewed labels remain in `coverage/labels/` at repository root. `experiments/` is the revised onboarding pilot, kept separate from the original benchmark.

## Superseded runs

Older difficulty trials and original-protocol final reports moved to [archive/results/difficulty](../archive/results/difficulty), with byte-preserving path mappings in [the archive guide](../archive/README.md). Earlier baseline and cost pilots remain in [results/archive](archive/README.md). Historical manifests retain original paths and hashes. Do not blend protocols or interpret archived failures as current designed difficulty.
