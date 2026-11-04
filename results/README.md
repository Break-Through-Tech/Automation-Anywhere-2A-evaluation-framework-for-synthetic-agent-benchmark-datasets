# Results and saved evidence

`framework/` is the primary combined report. `baseline/v2_full/` contains the
saved tau2 run and `baseline/v2_synthetic_full/` contains the original synthetic
run, including traces, reference checks, retry history, and source snapshots.

Standalone metric exports and validation files live in `coverage/` and
`difficulty/`. Generated labeling exports and review sheets live in `labeling/`;
the reviewed labels consumed by the framework remain in `coverage/labels/` at
the repository root. Label generation does not overwrite those reviewed inputs.

`experiments/onboarding_state_v1/` contains the separate revised onboarding
pilot. Its original manifest and traces are preserved. `source_snapshot/`
contains every source file hashed by its original manifest. `relocation.json`
records the old and new package paths and source hashes, allowing the relocated
runner to check the saved results without rewriting historical provenance.

`archive/` contains earlier runs; none are automatically included by
`run_all.py`. Their saved paths describe the layout at execution time. Trace
paths within trial CSVs remain relative to each run directory. Archived source
hashes describe the original execution, not today's refactored files.

The repository cleanup moved saved evidence without recomputing scores. Existing
framework metadata and reproducibility hashes therefore document the earlier
execution. Future framework runs will record the current source hashes.
