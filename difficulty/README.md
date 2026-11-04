# LLM-judge difficulty

`llm_judge.py` evaluates synthetic agent transcripts against the expected outcomes and
milestones in `data/<domain>/test_cases.json`. Expected tool calls are provided as context,
but an exact sequence match is not required. A task passes only when the judge finds the
requested outcome and evidence for every milestone. Difficulty is `1 - pass_rate` over
valid trials.

Save a trial transcript and run the judge:

```powershell
python data/run_test_cases.py --agents banking_accounts_deposits --save-results results/difficulty/agent_trials.jsonl
python difficulty/llm_judge.py --trials results/difficulty/agent_trials.jsonl
```

For repeated runs, use a separate JSONL file and a distinct `--trial` number for each
run, then pass all files to `--trials`.

The judge uses `OPENAI_API_KEY` and optional `BASE_URL` from `.env`. The model is selected
from `JUDGE_MODEL`, then `MODEL_NAME`, then `gpt-4.1-mini`. It writes per-trial judgments
and task-level difficulty under `results/difficulty/llm_judge/`. Trial errors are recorded
but excluded from the difficulty denominator. Review traces for sensitive data before
sending them to an external judge provider.
