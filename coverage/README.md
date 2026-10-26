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
