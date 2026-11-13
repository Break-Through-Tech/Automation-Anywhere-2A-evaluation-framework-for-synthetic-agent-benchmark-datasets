# Task-bound unit schema — one real diagnostic passed

The updated response schema permits only the unit IDs supplied for that task, and no
more unit rows than supplied units. Local duplicate, coverage, quotation, applicability
and score checks remain. The rubric and prompt are unchanged; generation schema version
is now `design_schema_v1.2_task_bound_units`. Schema version enters the aggregation
compatibility fingerprint. Old and new generation protocols are not silently pooled.

The prior airline response invented `reservation_and_eligibility_check`,
`cancel_reservation` and `transfer_to_human` rows although the source contract supplied
only `task_requirements`. That response remains rejected. Do not repair model output
by deleting units or accepting its proposed score.

## Verification

**145 offline tests passed.** An additional offline check applied the task-bound schema
to all 43 archived responses: all 42 previously valid responses still conformed, while
the invented-unit response was rejected before local grading. This is a regression
check on saved outputs, not a new API run or independent validation.

One new, separately versioned GPT-6 Sol diagnostic was authorized within the extended
31-call batch cap. It passed at **50/100**, assessing only `task_requirements` and giving
all five dimensions level 2. Its evidence describes fact retrieval, explicit policy
checks and refusal rather than a complex booking-write workflow. The case's initial
reservation and applicable flight-date records are judge-only design context; the
agent must still retrieve the relevant facts. No task agent ran.

**Total new calls in this domain batch: 31/31. No authorized calls remain.** This final
call is separate from the [30-call domain report](../numeric_design_domains_v12/README.md),
which retains the earlier source gap and genuine judge failure. Thirteen development
and control responses were also reused offline, without additional calls.

## Limits and next action

One successful new-schema judgment does not establish repeatability. The earlier
valid 55 used a different generation schema; it is not averaged with this 50. Likewise,
the rejected proposed 55 is never treated as a usable score. Do not interpret the five-
point difference as the causal effect of the schema change: ordinary sampling variation
is also possible.

The response notes that the selected flight-date records lack explicit flight-number
bindings in the judge-facing catalog. Their original source pointers retain those
bindings, but consistent task-relevant state extraction across native tasks still needs
attention. Do not claim complete native source coverage or a final whole-dataset ordering.
The source dataset is unchanged.

Next bounded proposal: **two more judgments on this same frozen new-schema packet/input**
to form a three-judgment diagnostic, stopping on any validation error or excessive
variation. This requires approval for two additional API calls (33 total). Broader
calibration and full dataset scoring remain separate work; no paid calls are scheduled
automatically. The current one-repeat packet is complete. A fresh three-repeat packet
can reuse this exact raw response without another charge; two new calls would remain.

See `evidence.json`, `run_manifest.json` and `task_scores.csv`. Source inputs, request,
manifest, raw response, model metadata and validation output are retained unchanged.

## Latest follow-up

The separate task-bound airline cohort now validates at 50/50/50 under validator v1.3.
The signature/return rendering issue was resolved offline with explicit diagnostics;
no raw response was edited. Total approved batch calls used: 33. See [the repeat review](../numeric_design_airline_repeats_v13/README.md).
These older cohort scores and generation versions remain separate.
