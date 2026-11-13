# Initial three-task repeatability check

Six new GPT-6 Sol judgments were authorized and made. Three earlier accepted v1.1
responses were reused as repeat 0, giving nine distinct model responses in total.
No other generation requests were made. All nine responses pass schema, evidence,
identity, applicability, step/task consistency and arithmetic checks.

- Premium account: **65, 65, 65**; mean 65; observed range 0.
- Standard account: **65, 65, 65**; mean 65; observed range 0.
- Commercial property/BI insurance: **70, 70, 75**; mean 71.67; observed range 5.

This passes the tolerances specified before the calls: maximum within-task range
at most 10 points and mean within-task range at most 5 points. Observed values are
5 and 1.67 respectively. This is an initial development-sample consistency result,
not independent validation or a confidence interval for score error.

## What varied

All five task dimensions stayed the same across both account triplets. The insurance
variation came from workload being rated 3, 3 and 4; other task dimensions stayed fixed.
The last response emphasized linked claim types and multiple specialists. This is a
borderline anchor judgment, not different task data or a changed scoring rule.
A five-point difference between tasks should not be treated as a proven distinction.

Explanations and required-versus-selected-conditional labels sometimes differed even
when task scores matched. The active workflow-step sets remained the same within each case. For insurance,
the global-guidance unit changed from context to required in one response, although
all three explanations said it added no separate workflow step. That interpretive
variation is recorded explicitly and needs attention before stronger semantic claims.
Identical scores do not mean every word or per-step judgment is identical or correct.

The uniform-score inspection gate fired on the two account triplets. Because these
were intentionally identical repeated inputs, the ties were inspected as expected
consistency rather than failed scoring. Each packet was already complete; no extra
calls were made within it or beyond the approved six-call budget.

## What is still missing

Only three purposively selected tasks from two synthetic domains were repeated. This
is not the domain-diverse calibration sample, and no tau2 tasks were scored. The
three-task mean (67.22 after averaging repeats within each task) is a selected-subset
summary, not the difficulty of all 64 tasks. Old prompt-v1 values are not pooled.

Next are four separate source-control cases: a simple task, a more involved task
with the same listed step count, a paraphrase, and a source-order variant. These
check sensitivity and harmless-change stability; they are not edits to benchmark data
or independent gold difficulty labels. Their v1.1 packet is prepared but has not
been sent. Four additional paid calls require approval. Broader domain-diverse and
held-out checks remain beyond that bounded control check.

See repeat_summary.json, repeat_evidence.json, reliability.json, run_manifest.json
and task_scores.csv. Raw responses and cached-seed provenance remain in their frozen
local packets. Anchors, weights, original tasks and earlier responses were unchanged.
Usage is recorded for the six new calls separately from the three cached responses;
no dollar amount or billing ownership is inferred.
