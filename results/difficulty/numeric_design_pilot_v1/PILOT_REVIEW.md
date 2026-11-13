# First GPT-6 Sol design-difficulty pilot

Three model calls were authorized and made. Two responses passed validation; the
third was rejected. No task agent was run, and no extra generation calls or retries
were made after the rejection.

- Premium savings account, instant funding verification: **60/100**, accepted.
- Standard checking account, micro-deposit funding verification: **65/100**, accepted.
- Commercial property/business-interruption claim: **no accepted score** because
  the response violated the output contract. Its raw proposed 70/100 is preserved
  for diagnosis only and is excluded from all accepted-score summaries.

## What the first two examples show

Both account cases share the same eight workflow steps. The judge assessed their
tool binding, business checks, prerequisites and case-specific funding path rather
than using step count alone. Both received task levels 3 for workload, 2 for reasoning,
3 for tool use, and 2 for information. Dependency levels were 2 versus 3, producing
the five-point difference under the frozen formula.

That difference remains tentative. The dependency explanations cite much of the
same shared workflow. The second response also notes that the micro-deposit
continuation is underspecified. Repeat and control checks are needed to determine
whether this is a stable design distinction or judgment variability. Do not present
the gap as validated evidence of greater difficulty.

## Why the third response was rejected

The judge classified the final success signal and several milestone state checks as
context, while giving them numeric unit ratings. Our local contract requires all
three ratings to be null for context, unselected or uncertain units. The initial API
schema allowed this combination even though local validation rejected it. The prompt
also did not state that null requirement explicitly enough.

Offline diagnosis found that this mismatch was the validation failure: a hypothetical
copy with those context ratings set to null passed the other checks. **That copy was
not accepted, saved as a replacement, or used to compute a score.** The original
response is unchanged in pilot_evidence.json and the local raw-response archive.

The third response also identifies source ambiguities worth discussing: linked-claim
creation is not clearly implemented by the shown reference call; a salvage-service
reference does not clearly satisfy dispatching an engineer and forensic accountant;
and general escalation guidance differs from the selected case path. These are
model observations to inspect against the supplied sources, not confirmed dataset bugs.

## Offline correction and next step

Prompt v1.1 explicitly distinguishes null from zero. Its API schema now separates
active units with numeric ratings from context/unselected/uncertain units with null
ratings. Local validation still rejects inconsistent results. New offline regression
tests cover both combinations. Rubric anchors, dimension weights and the dataset are
unchanged.

The next proposed paid action is **one diagnostic retry of the insurance case** in a
fresh versioned packet. It requires authorization. It will test the output-contract
correction; it will not retroactively validate or replace the original response.
Do not silently combine revised-prompt scores with this pilot's accepted scores.

## Scope, evidence and usage

This purposive pilot has only **2 accepted scores out of 3 selected tasks**, covering
2 of the original 64 synthetic cases. The accepted subset mean, 62.5, is not a
representative estimate of synthetic dataset difficulty. No τ²-bench tasks were scored.
Full repeat, controlled-pair, paraphrase/order and held-out checks remain incomplete.
New human review was not required; automated validity is not independent validation.

The three responses reported 26,670 input tokens and 7,461 output tokens, including
reasoning tokens. These are usage counts, not a dollar-cost estimate or billing audit.
The earlier rejected request to the invalid `gpt-6` name is a separate configuration
attempt and is not one of these three GPT-6 Sol responses.

See run_manifest.json, pilot_evidence.json, source_bindings.json and task_scores.csv.
Exact requests, raw responses, fingerprints and usage are preserved locally under
`.cache/design_numeric_v1/pilot_gpt6_sol_v1`. The original implementation is commit
`9fa5640`; use that frozen version when regenerating its outputs. Supplied source
files and existing successful judgments were not edited.
