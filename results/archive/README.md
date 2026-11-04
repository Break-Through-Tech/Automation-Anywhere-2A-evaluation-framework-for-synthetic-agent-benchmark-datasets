# Archived experiments

These saved runs are retained for provenance and are not current framework inputs.

- `baseline/v1_20261014T023653Z/`: early baseline manifest.
- `baseline/v1_20261014T140213Z/`: early baseline trials and manifest.
- `baseline/parsed_v1_20261014T023653Z_airline/`: parsed early airline results.
- `baseline/v2_synthetic_pilot/`: two-task synthetic smoke run preceding the full baseline.
- `tau2_cost_pilot/`: initial ten-task runtime and cost experiment, formerly `pilot/`.

The first four directories previously lived in `results/baseline/`. Run manifests,
CSV contents, prompts, and traces retain their original bytes. Relative trace
paths still resolve within each relocated run. Historical manifests may include
old repository-relative paths; interpret them using this relocation guide.

Current full runs remain under `results/baseline/`. Revised onboarding results
are under `results/experiments/`, with implementation in `experiments/`.
