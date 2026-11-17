# Paid judge test spending guard

The user requested on 2026-11-08 that a run showing another all-failed or
all-unverifiable pattern stop for diagnosis instead of spending credits on
the whole sample. Apply this guard to future paid judge experiments.

Start with a sequential diagnostic sample of at most three requests. Inspect
and validate each response before issuing another. Stop after any API or
validation error, or after two consecutive unmet/unverifiable judgments.
The latter is a conservative spending signal, not proof of a grader defect or
agent failure. There is no automatic expansion to sixteen or the full dataset.
`difficulty/judge_canary.py` implements this decision rule and has offline tests.

For separately authored diagnostic controls, compare the returned label to the
private expected label after the response. Stop immediately on a mismatch, even
when response format and citations pass. Never include that private label in
the judge request or treat passing simple authored controls as benchmark accuracy.

Before another paid request after a stop, diagnose offline: check actual
agent-visible inputs, tool schemas, workflow/reference conflicts, evidence
validation, policy interpretation, and genuine environmental blockers. Keep
raw responses and all input/prompt/source hashes. Reuse saved responses when
requests are identical, and never disguise old responses as a new policy run.

Do not weaken grading, fabricate evidence, or tune until a task passes merely
to create outcome variation. If the pattern is legitimate, report it and its
limits; do not continue a broad paid run without a concrete reason to do so.
Keep human labels out of judge requests. A human-labeled successful example
can be a diagnostic candidate, not assumed ground truth or a forced pass.

No automatic API retries. Preserve unknown outcomes and quota/transport errors
as judge/infrastructure problems, not task failures. Record requests attempted,
skipped requests, stop reason, and the diagnostic conclusion.
