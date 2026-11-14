# Archive — historical work, not current results

Start at [the current project guide](../README.md). Current designed-difficulty scores are **τ² 64.15 and synthetic 63.75**, under v1.1. Original-protocol scores, early structural indices and execution failures here describe different methods; do not mix them into current means.

## What is stored here

- `results/difficulty/`: superseded numeric runs, calibration experiments, exploratory reviews and original-protocol full results. These retain source evidence, raw responses, requests, charts and manifests.
- `docs/evaluation/`: older methods, policy drafts, review notes and reporting handoffs. Their pending-status statements and proposed rules reflect their date; the current specification supersedes them.
- `difficulty/` and `tests/`: retired meeting-summary and initial structural-audit helper snapshots with their original tests. They are historical source, not maintained/importable package entry points in this layout.
- `guides/`: the previous long root, execution-judge and numeric-development READMEs, kept out of the main navigation.

**Nothing was deleted.** `relocation.json` maps each moved file from its original path to its archived path, with a SHA-256 fingerprint. All 372 moved files retain their original bytes. Historical manifests and requests deliberately retain original path strings and hashes; those strings are provenance, not instructions to create or overwrite active output. Old Markdown links and example commands inside archived material can therefore refer to the pre-cleanup layout. Use the relocation map to locate a moved artifact.

The source-only v1.1 archive remains at `results/difficulty/designed_final_v27/` and is self-contained for replay. The retained `results/difficulty/designed_v1`, `designed_v2`, `designed_v3`, `structural_v1` and `design_review_run_v1` directories are fixtures read by supported modules/tests, not competing final results. Native structural and semantic crosschecks remain available as complementary diagnostics. Existing earlier baseline archives stay under [results/archive](../results/archive/README.md); the revised onboarding pilot stays under [experiments](../experiments/README.md).

To rerun a retired helper in its original package layout, use a separate checkout of the pre-cleanup scoring revision recorded in `relocation.json`. Do not copy old scripts over current modules or treat historical API authorizations as permission to spend again.
