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

## Task identifiers

The canonical task ID is the supplied Python class's `test_case_id` field, matching
the original baseline CSV and traces. The runner uses that value for its internal
`test_id` and saves it as `task_id`; judge outputs use the same canonical value.
Class names are implementation metadata, not new task IDs.

For compatibility, the judge accepts old class names and JSON reference IDs at
input and resolves them to the canonical Python ID. Each JSON reference must map
to exactly one Python case within its domain; missing, duplicate, or ambiguous
mappings fail rather than silently choosing a task. Repeated aliases of the same
task/trial are rejected before model calls so one attempt cannot be counted twice.
Existing source annotations and historical results are not rewritten.

## Reuse the original baseline attempts

The judge accepts transcript JSONL, a saved baseline run directory, or a baseline
`trials.csv` whose `trace_file` column points to compressed JSON traces. It validates
trace identities, required evidence fields, duplicate slots, saved evaluation
provenance, and available run-manifest counts before judging. Conversation and
tool-event arrays (including arguments, outputs, and errors) are retained exactly.
The original simulator scenario is included as task context. Old grader labels
are kept only in provenance and are not sent to the model or the human packet.
An old `invalid_reference` label does not automatically exclude an attempt under
the new rubric. Actual recorded baseline infrastructure errors remain unassessed;
individual tool errors are evidence for the judge, not automatic exclusions.

Validate the full run without credentials or model calls:

```bash
python difficulty/llm_judge.py --trials results/baseline/v2_synthetic_full/trials.csv --dry-run --out results/judge_review/v1/full_audit
```

This has validated all 256 attempts across 64 tasks and seven categories, with
four trials per task. The audit records source hashes and counts; it assigns no
new outcome rewards or difficulty scores.

Prepare a blind human-review packet from the issue #45 development sample:

```bash
python difficulty/llm_judge.py --trials results/baseline/v2_synthetic_full/trials.csv --selection results/rubric_review/v1/sample.json --prepare-review --out results/judge_review/v1/sample
```

The 16 selected attempts cover 15 tasks and all seven categories. Read
`results/judge_review/v1/sample/REVIEW.md`, inspect `review_packet.json`, and fill
`human_reviews.json` independently. The form starts with blank judgments and
reviewer names. Review packets cannot be overwritten; use a new directory for a
new packet. This is a purposive development sample, not held-out validation.

After human review, the same selection can be judged without rerunning agents:

```bash
# Calls the configured judge model; outputs remain separate from original scores.
python difficulty/llm_judge.py --trials results/baseline/v2_synthetic_full/trials.csv --selection results/rubric_review/v1/sample.json --out results/judge_review/v1/model_sample
python difficulty/compare_judge_reviews.py --human results/judge_review/v1/sample/human_reviews.json --packet results/judge_review/v1/sample/review_packet.json --judgments results/judge_review/v1/model_sample/llm_judge_trials.csv --out results/judge_review/v1/sample/comparison.json
```

The comparison refuses mismatched identities/rubrics and checks evidence locators
and excerpts. It reports task/milestone agreement only after real human labels
exist. Before then it reports `awaiting_human_review` and computes no agreement
metrics. The reviewer must remain independent of model answers; software cannot
certify that independence. Judge calibration and held-out examples remain #48.

The judge uses `OPENAI_API_KEY` and optional `BASE_URL` from `.env`. The model is selected
from `JUDGE_MODEL`, then `MODEL_NAME`, then `gpt-4.1-mini`. It writes per-trial judgments,
including milestone evidence and contradictions, and task-level difficulty under
`results/difficulty/llm_judge/`. Review traces for sensitive data before sending them to an
external judge provider.
