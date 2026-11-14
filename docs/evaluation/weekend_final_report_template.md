# Evaluation report — working scaffold

Status: template for #69; not a completed report or submission. Fatma and Zayd can work on this structure while scoring reviews and analysis proceed.

## Executive summary

[Insert the selected scoring convention and headline results after #62. Distinguish designed complexity, relative workflow coverage, and any exploratory composite from independently validated dataset quality.]

## Dataset scope and reproducibility

- τ²-bench: 278 base tasks (50 airline, 114 retail, 114 telecom).
- Synthetic: 64 tasks across seven agent categories.
- [Record the frozen source versions, task-ID alignment, score versions and input hashes from #59/#60.]

## Coverage findings

Source: main/results/coverage/workflow/README.md and frozen CSVs.

- τ²-bench: 21/21 declared workflows represented.
- Synthetic: 51/59 represented; 8 missing, and 38 represented workflows have one task.
- [Add group-level coverage, normalized entropy and sampling-depth findings.]
- [Explain separate catalogs, curated native labels, group weighting, and why Vendi is a diagnostic rather than a workflow-coverage substitute.]

## Designed difficulty

Source: results/difficulty/designed_final_v27/README.md.

- τ²-bench: 64.15/100; synthetic: 63.75/100.
- Same five 20% dimensions and clarified applicable-path convention.
- [Insert domain chart, distributions, interpretation, scoring coverage and source/LLM uncertainty. This is not an execution-success rate.]

## Combined scoring convention — #60–#62

[Record the chosen outer weight, Coverage definition, normalization, intended use and why those assumptions were selected. Include all five tested weight settings. Do not treat ranking stability as independent validation or choose weights to force a winner.]

[Insert the checked per-dataset component contributions, selected candidate result and input provenance. No final selection is made by this template.]

## Side-by-side comparison — #63/#64, due Sunday November 15

[Figures and interpretation of Coverage, Difficulty and exploratory combined results. State what can and cannot be compared across the two catalogs.]

## Within-dataset analysis — #65/#66, due Sunday November 15

[Airline, retail and telecom profiles; group catalogs and counts; meaningful contrasts; limits from shared sources, task variants, unequal group sizes and judge variation.]

## Synthetic weaknesses — #67, due Monday November 16

[Evidence-linked gaps in breadth, depth, balance and designed difficulty. Distinguish supplied-design problems from observed agent failures, which this difficulty metric does not measure.]

## Improvement recommendations — #68, due Tuesday November 17

[For each recommendation: supporting finding, proposed change, expected impact, feasibility, priority, responsible reviewer and how to evaluate it. Propose changes without modifying supplied data.]

## Limitations and unresolved questions

[Catalog comparability, curated labels, small groups, descriptive entropy, shared-source dependence, interpretive difficulty ratings, unvalidated weights and any remaining coverage/review gaps.]

## Final review and submission — #69/#70

[Check that every figure matches the frozen numbers, every claim has evidence, the selected weights are justified, uncertainty and missingness are visible, teammate sections are integrated, and the November 18 submission requirements are met. Record actual review/submission separately; do not mark complete in this scaffold.]

## Appendix

[Input hashes, code/source revisions, reproduction commands, all sensitivity settings, score CSVs, source links and supporting diagnostics.]
