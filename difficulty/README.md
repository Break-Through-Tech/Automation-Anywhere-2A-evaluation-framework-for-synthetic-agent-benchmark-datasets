# LLM-judge difficulty

`llm_judge.py` evaluates synthetic agent transcripts against the expected outcomes and
milestones in `data/<domain>/test_cases.json`, using
[`docs/evaluation/synthetic_milestone_rubric.md`](../docs/evaluation/synthetic_milestone_rubric.md)
as its grading reference. The rubric distinguishes `met`, `unmet`, and `unverifiable`
judgments, requires evidence for met/unmet outcomes, and treats tool sequence as context
rather than an exact-match key.

The rubric is version `synthetic_milestones_v0.1_draft` and is proposed for team review
under #45; it is not approved policy. Difficulty currently follows its proposed denominator
rule: only task-level met/unmet judgments are eligible, while unverifiable and invalid
trials are excluded. The output reports these counts and labels the denominator policy.
Review and approve the rubric/denominator before using these scores as final empirical
difficulty results.

Save a trial transcript and run the judge:

```powershell
python data/run_test_cases.py --agents banking_accounts_deposits --save-results results/difficulty/agent_trials.jsonl
python difficulty/llm_judge.py --trials results/difficulty/agent_trials.jsonl
```

For repeated runs, use a separate JSONL file and a distinct `--trial` number for each run,
then pass all files to `--trials`.

The judge uses `OPENAI_API_KEY` and optional `BASE_URL` from `.env`. The model is selected
from `JUDGE_MODEL`, then `MODEL_NAME`, then `gpt-4.1-mini`. It writes per-trial judgments,
including milestone evidence and contradictions, and task-level difficulty under
`results/difficulty/llm_judge/`. Review traces for sensitive data before sending them to an
external judge provider.
