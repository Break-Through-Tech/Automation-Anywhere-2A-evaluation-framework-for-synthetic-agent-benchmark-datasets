# Coverage validation (issue #27)

`validate_coverage.py` reads `data/processed/tasks.jsonl`
and calls `embed()` and `vendi_score()` from
`coverage/vendi_score.py`. It selects all `tau2` tasks in that file, scores the
full set, then scores the set with each domain removed. It does not execute
the agents or use an API key. It embeds descriptions once and reuses those
embeddings for every comparison.

Run from the repository root with the project's virtual environment active:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python coverage/validate_coverage.py --matched-samples 5 --seed 42
```

The sentence-transformer model downloads on its first use. No local
`tau2-bench` clone is needed for this script because the unified task file is
already committed. The task file uses the τ²-bench `base` split.

The output directory is `results/coverage/` by default:

- `coverage_results.csv`: one score per run, with task count and domains.
- `run_tasks.csv`: the task IDs in every run, so results can be reproduced.
- `coverage_summary.csv`: one row per removed domain, with changes relative
  to the full score and the mean equal-sized comparison score.
- `run_metadata.json`: task file checksum, model, task counts, and random seed.

`--matched-samples 5` draws five equal-sized samples from the full set for
each removed domain. Because embeddings are reused, these comparisons do not
make additional model calls. To run only the full and domain-removal scores:

```bash
python coverage/validate_coverage.py --matched-samples 0
```

The full base split currently has 278 tasks (retail 114, airline 50, telecom
114). The script reports the actual change: normalized `VS/n` is **not
mathematically guaranteed** to drop when a domain is removed, especially
because the task count changes.

Each run replaces the CSV and metadata files in the output directory. Use
`--output-dir` to keep separate experiments. If you supply a different task
file with `--tasks`, set `--split-label` to describe its split; this label does
not change which tasks are selected.

## Coverage summaries (issue #18)

With the virtual environment active and requirements installed, run:

```bash
python coverage/plot_coverage.py
```

This reads the merged `coverage/labels/labels_tau2.csv` and
`coverage/labels/labels_synthetic.csv`, along with `attribute_scores.csv`
and `vendi_scores.csv` in this folder. It uses the existing scores and makes
no API calls. The current inputs contain 278 tau2 base tasks and 64 synthetic
tasks. Labels from other splits or expanded datasets should not be combined
with these scores; update the task file, labels, and scores together first.

The script checks task IDs, Vendi totals, and saved attribute counts before
plotting. These checks do not establish whether embeddings were recomputed
after a description edit, so rerun scoring when the source text changes.

Outputs go to `results/coverage/summaries/`:

- Nine charts in PNG and SVG: domain and task-type distributions, top 15
  tools for each dataset, task-type and tool heatmaps within each domain,
  overall scores side by side, and Vendi scores by group.
- `distribution_counts.csv`: counts and percentages for every category,
  including zero-count task types and all tools, not just the top 15.
- Copies of `attribute_scores.csv` and `vendi_scores.csv` used in the plots.
- `plot_metadata.json`: input checksums, dataset sizes, and plotting versions.
- [README with findings](../results/coverage/summaries/README.md): interpretation
  of the committed snapshot. Review this text when regenerating the charts.

Use `--output-dir PATH` to save another run. Existing generated files in that
directory are replaced. Domain/task-type percentages use the number of tasks
in the group as the denominator. Each tool is counted once per task; tool
percentages can add up to more than 100%.

The synthetic labels use four broad domains, while the existing Vendi scores
use seven agent categories. The figures retain those groupings explicitly.
The two datasets also use different domain and tool vocabularies, so the
shared task-type labels provide the most direct category comparison.
