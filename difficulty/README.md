# LLM-judge difficulty

## Current source-only numeric mode

Use [`difficulty.design`](design/README.md) for the numeric designed-difficulty roadmap (#71).
The implementation and offline checks are ready; paid calibration and actual scores are pending.
The execution judge and historical structural index below are separate procedures.

Offline source-consistency triage for all 64 original tasks is documented in
[`results/evaluability/source_v1/`](../results/evaluability/source_v1/README.md).
Run `python -m difficulty.audit_evaluability` into a fresh output directory to
reproduce it. Triage flags do not assign outcomes or difficulty eligibility and
do not authorize another broad paid run.

The offline working interpretation of completion evidence and input sufficiency
is in [evaluation expectations](../docs/evaluation/evaluation_expectations_v0.1.md).
The two-case context test stopped early and its source-backed follow-up remains
unverifiable/excluded; do not resume broad paid judging just to obtain variation.

Paid experiments must follow the user's
[spending guard](../docs/evaluation/api_spending_guard.md): begin with at most
three sequential requests; stop after a technical failure or two consecutive
non-success judgments and diagnose before spending more. Never automatically
expand a uniform failure/unverifiable pattern to the entire sample.

The user's current grading clarification is
[provisional outcome policy v0.2](../docs/evaluation/provisional_outcome_policy_v0.2.md).
It requires evidence of mandatory prerequisites as well as the outcome, and
classifies attempts blocked by necessary missing environmental material as
unverifiable, outside difficulty. Correct blocker recognition is a separate
positive diagnostic. The earlier v0.1 run is preserved. A fresh sixteen-attempt
v0.2 assessment is under `results/judge_review/v4/`, with separate blocker and
recognition reports. All sixteen were proposed unverifiable, leaving no eligible
difficulty observations. The input audit found missing authoritative tool/workflow
context in judge requests, so these exclusions do not establish dataset defects
or agent failure. An offline context supplement is prepared for the next check.

For a separate extraction of designed-complexity signals, see
[the structural feature counting rules](../docs/evaluation/structural_feature_rules.md).
`structural_features.py` extracts all 64 task records without model calls. The
generated features and seven-example review guide are under
`results/difficulty/structural_v1/`. These signals are not success-based difficulty
scores and are not combined into a single score.

The framework accepts `--synthetic-structural-features` with the generated
`task_features.json`. It checks an exact task-ID join and source hashes before
embedding or scoring. The optional `designed_` output columns are descriptive
features; historical success scores do not validate them. See the root README
for a command that writes to a new framework output directory.

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

## Exact evidence checks and the next small retry

Groups 2–4 submitted task-level answers in issue comments. These are transcribed
with provenance under `results/judge_review/v1/submissions/` and in the matching
review sheets. Group 1 remains pending. No human milestone judgments have been
inferred from first-pass answers.

Use `compare_judge_reviews.py --level task` for first-pass task-label agreement;
the default `--level full` still requires milestone labels. Task-only mode accepts
submitted human evidence prose and explicitly reports that it is not exact-excerpt
validated. It still checks every model judgment's structure and exact citations.
It computes no milestone agreement. Both modes require all expected human labels
and matching task/rubric identities before computing agreement. No API test may
run until group 1 / issue 51 is complete, per the user's instruction.

```bash
python difficulty/compare_judge_reviews.py --human results/judge_review/v1/sample/human_reviews.json --packet results/judge_review/v1/sample/review_packet.json --level task --out results/judge_review/v1/submissions/task_comparison_readiness.json
```

Prompt `synthetic_judge_v0.2_exact_evidence` distinguishes task requirements from
execution evidence. It requires exact, contiguous excerpts at transcript-relative
JSON pointers, and includes illustrative citation examples. Task-reference pointers,
payload-wrapper prefixes, paraphrased excerpts, and empty citation placeholders
are not execution evidence. Unverifiable judgments can have empty evidence lists.
The normal model-call path and the human comparison now share the same citation
checker in `judge_evidence.py`. Rejected responses raise a validation error; they
must not become agent failures or difficulty scores. Outputs record the prompt
version and hash separately from the unchanged draft rubric version.

The checker also accepts a whole JSON object or array quoted with different
serialization whitespace, provided its full contents and order are unchanged.
Whitespace inside strings is significant; omitted or changed values, reordered
arrays, duplicate keys, and paraphrases remain invalid. This corrected an R10
false rejection without another model request. The completed sixteen-attempt
development comparison and its validation history are under
`results/judge_review/v3/full_sample_revalidated/`. Human labels are unchanged;
agreement under the provisional policy is descriptive, not final accuracy.

The next prompt-development retry selects only R01, R06, and R07 across banking
accounts, fraud monitoring, and healthcare onboarding. These are already-inspected
development cases, not a held-out validation sample. Validate the selection offline:

```bash
python difficulty/llm_judge.py --trials results/baseline/v2_synthetic_full/trials.csv --selection results/judge_review/v2/retry_selection.json --dry-run --out .cache/judge_review/v2/retry_dry_run
python -m unittest discover -s tests -p 'test*judge*.py'
```

A local recorded GPT-6 Astra retry runner is prepared at
`.cache/judge_review/v2/retry_gpt6_astra/run_sample.py`. It is ignored by Git and
has not been run. After credits are restored, that runner can make the three
requests with medium reasoning, no temperature setting, a completion-token cap,
and no automatic retries. It saves exact requests, raw responses, metadata,
and validation results in a fresh private folder. Keep the earlier runs intact.

Review all three responses and their evidence before expanding to the full sample.
Passing citation checks alone does not establish semantic correctness. Compare
with actual human labels only after independent reviews are submitted, and keep
model answers out of the human review issues. A changed prompt must be recorded
as a new experiment, not pooled silently with the earlier prompt's results.
