# τ²-bench domain-removal coverage validation

Run command: `python coverage/validate_coverage.py --matched-samples 5 --seed 42`.
The input is the committed `data/processed/tasks.jsonl` τ²-bench **base** split:
278 tasks (retail 114, airline 50, telecom 114). The scorer is
`coverage/vendi_score.py` using `all-MiniLM-L6-v2` sentence embeddings. All
scenarios reuse the same embeddings. The full-set VS of 23.0133 matches the
score in `coverage/vendi_scores.csv`.

| Tasks scored | n | Vendi Score | VS/n | Change in VS/n from full | Equal-size full-set sample mean VS/n |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full τ²-bench base split | 278 | 23.0133 | 0.0828 | — | — |
| Without airline | 228 | 16.0157 | 0.0702 | -0.0125 | 0.0997 |
| Without retail | 164 | 7.8406 | 0.0478 | -0.0350 | 0.1209 |
| Without telecom | 164 | 36.1993 | 0.2207 | +0.1379 | 0.1221 |

The airline and retail removals lower normalized coverage. Removing telecom
**raises** normalized coverage, so the proposed claim that removing *any*
domain must lower VS/n is not supported by these results. The equal-size
comparisons point in the same directions. Each comparison mean uses five
random samples from the full task set with the same n as the domain-removed
set; these are exploratory comparisons, not a formal significance test.

The input data helps explain telecom's behavior: its 114 tasks contain only
three distinct `description` strings. The loader uses `reason_for_call` as
the description. The score therefore measures diversity of those description
strings, and may not reflect diversity in the full telecom workflows.

Files for further analysis:

- `coverage_results.csv`: all 19 individual scores, including each sample.
- `coverage_summary.csv`: the three domain-removal comparisons.
- `run_tasks.csv`: exact task IDs used in each run.
- `run_metadata.json`: model, input checksum, counts, and seed.

This experiment uses task descriptions only. It does not run agents or
measure whether agents complete the tasks successfully.
