# Difficulty methodology for the lab review

Version: `difficulty_lab_v0.3_proposed`
Scope: difficulty only. Pass/fail/unverifiable are attempt observations used to
support execution difficulty, not a separate correctness metric.
Status: implementation and source-derived reporting prepared for review;
Sandra has not approved a final scalar score, thresholds or adjudications.

## Guidance and its provenance

Sandra's 2026-11-09 email was verified in the project Gmail thread through the
browser on 2026-11-11 and matches the message supplied by the user. It distinguishes an
observed incomplete result caused by conflicting environmental material from
eligibility for execution difficulty, and suggests using designed difficulty
as the final metric if environment problems occur too frequently. Runtime
results would then be supplementary. The Gmail connector failed with
`mail_service_not_enabled`, but browser access succeeded. No later reply was
visible in that project thread when checked. This verifies the email's content,
not approval of every operational rule below. A follow-up request was sent to
Sandra on 2026-11-11 to confirm decisions at the lab and arrange more time if needed;
no additional meeting time has been agreed.

## Designed difficulty

The primary lab deliverable is a per-task profile: supplied class and explicit
difficulty labels, shared YAML workflow step count, reference domain-tool call
count and distinct count, milestone count, and separately labeled wording cues.
All 64 tasks and seven domains remain in the inventory. Report distributions by
domain and supplied label. Exact scenario-path and decision counts stay unknown
when unsupported. A shared workflow is not necessarily an executed path.
Supplied labels are annotations rather than independently validated truth.

There is no arbitrary weighted sum or numeric encoding of easy/medium/hard.
A final single-number metric needs an agreed definition, scaling, weights and
validation; the multi-feature profile is computed, not evidence that these
choices have been settled. Decision cues are supplementary and never described
as exact branch counts. Any future validation must account for shared workflows,
domain composition and the small hard-label group.

## Three outcome labels with separate eligibility

- Pass: the trace supports the requested outcome and mandatory prerequisites
  for the correct entity and task branch. Equivalent valid workflows are allowed.
- Fail: clear execution evidence establishes a required violation or that the
  requested outcome was not achieved. This observation alone does not attribute
  fault or make the attempt eligible for execution difficulty.
- Unverifiable: requirements or evidence do not support a reliable determination.
  Environment conflict is not an automatic global label; it can prevent assessment,
  or coexist with an observable incomplete result. Document the distinction.

Log environmental findings, attribution, evidence and execution eligibility
separately. A supported blocker preventing necessary execution or assessment,
unresolved material conflict, unverifiable result, judge failure or corrupt trace
stays outside execution difficulty. Correctly recognizing a real blocker is a
separate positive diagnostic, not partial success. An agent claim alone does not
establish a blocker. Schema acceptance does not prove semantic sufficiency.

Nonassessed slots have a null outcome and `assessment_status=not_assessed`.
That is a lifecycle state, not a fourth outcome, and must not be called unverifiable.
Infrastructure errors also remain separate; they are not automatically failed tests.

## Execution difficulty

For each task, execution difficulty = eligible fails / (eligible passes + eligible
fails), equivalent to 1 minus eligible success rate. Eligibility must be explicit.
A blocked fail is logged but excluded. If the eligible denominator is zero,
execution difficulty is unavailable, not zero or one. Report planned, assessed,
eligible, unassessed and excluded counts; do not silently hide excluded tasks.
Do not average domain/task rates without stating weighting or merge policy versions.
Exclusion can select easier or better specified tasks and must accompany results.
No cutoff for "too frequent" or minimum eligible trial count is assumed approved.

## Existing results and implementation boundary

Earlier v0.2 forced proven blocked attempts to unverifiable. New API judgments
now use `provisional_outcome_v0.3` and prompt
`synthetic_judge_v0.7_outcome_eligibility`. The judge validates and retains outcome,
environment assessment, blocker recognition, explicit difficulty eligibility,
exclusion reason and policy fingerprint. A blocked unmet can now be recorded
without entering execution difficulty. A preventing blocker cannot coexist with met.
The v0.2 validator remains available for historical callers; v0.3 is passed
explicitly by the current judge. Never silently regrade old results or mix policies.
A small authored-control test is recorded separately under `results/judge_review/v7/`;
it is not a validation of original benchmark task judgments. Sandra's approval
of the operational definitions remains pending.

The new outcome ledger maps existing labels met/unmet/unverifiable to display
labels pass/fail/unverifiable without changing semantics or source policy. It uses
one historical v0.2 development source and preserves all 256 original slots.
Its 16 unverifiable judgments had limited judge context and are not adjudicated
v0.3 results; the other 240 slots remain unassessed under that selected policy.
No historical rewards, human answers or earlier source artifacts are overwritten.
The three authored controls are separate diagnostics, not original task scores.

## Lab decisions still needed

1. Approve the designed profile as the primary difficulty deliverable, or define
   a final scalar and its validation procedure.
2. Define mandatory task-specific prerequisites and accepted simulated endpoints.
3. Confirm fail versus unverifiable for observable noncompletion with a blocker,
   while keeping both out of execution difficulty when blocked.
4. Define minimum eligible trials and what rate of reliable environmental findings
   would trigger designed-only final reporting. The purposive 16-case sample is
   not a prevalence estimate for all tasks.
5. Resolve the three new examples and earlier source conflicts, then decide if a
   follow-up meeting is needed before more paid tests or final reporting.

Reproduce without API calls:

```bash
python -m difficulty.meeting_metrics --out results/difficulty/fresh_lab_run
python -m unittest discover -s tests -p 'test_meeting_metrics.py'
```
