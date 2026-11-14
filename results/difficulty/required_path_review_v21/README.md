# Required-path source review

**All 18 queued cases reviewed offline. No API calls, live agents, changed source data, human labels or revised numeric scores.** This is an assistant review with prior scores visible, not independent validation.

## Findings

- **2 explanations explicitly include an additional payment/resumption chain**: review items 5 and 10. These need clarification; this is not a claim that their numeric scores are definitively wrong.
- **4 explanations need stronger justification for additional account/contract investigation**: items 1, 2, 7 and 13.
- **7 explicitly limit work after the exit**: items 4, 8, 9, 14, 15, 16 and 18. This validates wording only, not all ratings.
- **5 do not describe the path precisely enough**: items 3, 6, 11, 12 and 17.

The manual explicitly directs escalation for a locked SIM; customer identification and enough diagnosis to discover that state still count. The general best-effort instruction does not by itself establish that every unrelated repair must be completed after a decisive exit.

Static code review also shows why some extra work is legitimate: `_check_sim_status` reports Missing before the underlying lock; reseating removes the missing-card flag without clearing the lock. That private-helper context was not fully in the original judge input, so it is additional review evidence, not something the judge is assumed to have seen. No benchmark code was imported or executed.

## Concrete proposed next test

The [draft prompt clarification](../../../docs/evaluation/required_path_clarification_draft_v1.md) explains required discovery and excludes unnecessary post-exit work without assuming an oracle-shortest path. It leaves the published judge, five dimensions, weights and published scores unchanged.

A **four-call GPT-6 Sol development probe** is selected: two explicit-chain concerns and two explicit-exclusion contrasts. Only the system addendum changes. Inputs, tool context, evidence schema and model settings are preserved; private-helper context is not added. No desired scores or review labels go to the model. No retries or full-dataset rerun. It is prepared offline and needs a new API authorization before execution.

Even if all four outputs validate, review the required-path explanations; JSON validity or lower scores alone do not establish correctness. A one-judgment comparison cannot isolate prompt effects from variation. Separate calibration would precede any replacement of published means.

See review.csv for all 18 dispositions, review.json for exact source evidence and saved explanations, and pilot_selection.json for the sample and prespecified checks. Native operation/check/coordination profiles remain separate unfinished work in #50; #50 and parent #71 remain open.

All 171 offline tests passed. The prepared request fingerprints are recorded in pilot_manifest.json and request_summary.json; actual request bodies remain in the ignored .cache/required_path_probe_v21 folder. The prepare/check tool does not expose a paid-run command or read API credentials. It can regenerate the plan from the four original/replayed packets without model calls.
