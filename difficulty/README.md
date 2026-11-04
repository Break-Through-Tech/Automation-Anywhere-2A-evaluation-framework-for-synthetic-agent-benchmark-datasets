# Difficulty

This folder contains structural difficulty based on **write-action counts**, empirical
difficulty from baseline pass rates, and an LLM-judge-based difficulty measure.

## What is “write-action difficulty”?

- We label each tool as **read** vs **write**.
- For each task we count how many expected tool calls are *write* actions.
- The intuition: tasks requiring more write actions tend to be harder for agents.

### Files

- `difficulty/write_counts.py`: computes write-action counts for **synthetic** tasks.
- `difficulty/write_counts.csv`: output for synthetic tasks (committed).
- `difficulty/synthetic_tool_labels.csv`: tool → read/write labels for synthetic.
- `difficulty/tau2_tool_labels.csv`: tool → read/write labels for τ²-bench tasks.

## LLM-judge difficulty

`difficulty/llm_judge.py` evaluates each agent trial against the task's expected outcome
and milestones in `data/<domain>/test_cases.json`. The reference tool sequence is supplied
as context, but exact sequence matching is **not** required. A valid trial passes only when
the judge finds evidence for the requested outcome and every milestone. Task difficulty is
`1 - (LLM-judge passes / valid trials)`, so it is directly comparable to empirical
difficulty while using milestone-based grading.

Save traces from the synthetic runner and judge them:

```powershell
python data/run_test_cases.py --agents banking_accounts_deposits --save-results results/difficulty/agent_trials.jsonl
python difficulty/llm_judge.py --trials results/difficulty/agent_trials.jsonl
```

For repeated runs, write each run to a separate JSONL file with a distinct `--trial`
number, then pass all files to `--trials`.

The judge reads `OPENAI_API_KEY` and optional `BASE_URL` from `.env`. It uses
`JUDGE_MODEL`, then `MODEL_NAME`, then `gpt-4.1-mini` as its model. Results are written to
`results/difficulty/llm_judge/llm_judge_trials.csv` and
`results/difficulty/llm_judge/llm_judge_difficulty.csv`. Trials recorded with an execution
error are retained in the trial output and excluded from the difficulty denominator.
Review task traces for sensitive data before sending them to an external judge provider.

## Plots / summaries (Issue #19)

`difficulty/summarize_difficulty.py` generates:

- Distributions of `num_write` for τ²-bench and synthetic.
- Distributions of **empirical difficulty** (requires baseline run outputs).
- Scatter plot of `num_write` vs empirical difficulty.

### Run (τ² only; works with what’s in `main`)

```powershell
python difficulty/summarize_difficulty.py --tau-empirical results/difficulty/empirical_difficulty.csv
```

Outputs go to:
- `results/difficulty/summaries/`

### Run (τ² + synthetic empirical difficulty)

To plot empirical difficulty for **synthetic**, you need a saved synthetic `trials.csv`
from a baseline run (not currently committed on `main`). Once you have it:

```powershell
python baseline/compute_difficulty.py --trials path/to/synthetic/trials.csv --out results/difficulty/synthetic
python difficulty/summarize_difficulty.py \
  --tau-empirical results/difficulty/empirical_difficulty.csv \
  --synthetic-empirical results/difficulty/synthetic/empirical_difficulty.csv
```

## Compatibility

`difficulty/plot_difficulty.py` is kept as a wrapper that calls
`difficulty/summarize_difficulty.py`.
