# Numeric design difficulty — start here

This mode reads task designs and asks an LLM for evidence-backed difficulty ratings.
It does not run task agents or grade saved attempts.

**Final synthetic result: [64.30/100](../../results/difficulty/synthetic_final_v15/README.md),
64/64 tasks scored, no exclusions.** All task scores use one evidence-reference format,
with the same provisional five-dimension rubric. The first three pilot calls are included
in the 64; older-format scores are not pooled. **153 offline tests pass.**

The API-format problem is resolved for this run: strict schemas use short citation IDs,
then code expands them to exact source excerpts without changing numerical judgments.
[Chart and readable task scores](../../results/difficulty/synthetic_final_v15/README.md).
This is a computed source-only index; independent validity and final native tau2 scoring
remain separate. Source data and historical raw responses are preserved.

1. Read the [short rubric](../../docs/evaluation/numeric_design_rubric_v1.md).
2. Prepare source inputs and a three-task request packet offline.
3. Obtain approval for API credits, run the bounded pilot, and inspect its explanations.
4. Record calibration findings and limits using the [protocol](../../docs/evaluation/numeric_design_calibration_v1.md).
   Successful scoring does not establish independent validity.
5. Generate the task scores, dataset means, coverage and post-scoring diagnostics offline.

The provisional formula gives five LLM-assessed dimensions equal weight (20% each):
workload, reasoning, tool use, dependencies/coordination, and information discovery.
Each dimension is 0–4; the task score is five times their sum (0–100). Step assessments
and scenario-specific paths justify these ratings. These weights and anchors are
documented implementation assumptions, not Sandra-approved or empirically validated.
The historical 40/40/20 count formula remains separate.

## Offline commands

Run from the repository root. Use a **fresh output directory** for every new packet/report.

```sh
python -m difficulty.design inventory --dataset both --out .cache/design_numeric/inventory
python -m difficulty.design prepare --inventory .cache/design_numeric/inventory/inventory.json \
  --selection pilot --model gpt-6-sol --reasoning-effort low --source-bound-evidence --out .cache/design_numeric/pilot
python -m difficulty.design check --packet .cache/design_numeric/pilot
python -m difficulty.design report --inventory .cache/design_numeric/inventory/inventory.json \
  --packet .cache/design_numeric/pilot --out results/difficulty/numeric_design_pilot_report
```

Preparation and reporting make no API calls. Before scoring, the report correctly
shows no dataset mean and zero scored tasks. No synthetic model scores are substituted.

## Paid pilot — requires explicit approval

Use an already configured `OPENAI_API_KEY` in the environment. This mode never prints
the key or automatically reads `.env`. The explicit model is preserved; an unavailable
model fails and stops rather than silently substituting another model. Account/billing
ownership cannot be inferred from a key's variable name.

The configured account rejected the bare name `gpt-6`; the authorized pilot used
`gpt-6-sol`. Verify availability for the intended account before a new paid run.

```sh
python -m difficulty.design run --packet .cache/design_numeric/pilot \
  --authorize-paid-api --max-calls 3
```

The runner uses the Responses API with a strict JSON schema. See the
[official Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).
Local validation additionally checks source quotations, identity, applicable units,
step/task consistency and arithmetic. A conforming response is not proof of semantic
correctness. Requests and raw responses are retained; returned model and usage metadata
are saved. No API price or final cost is invented when unavailable.

The runner makes at most three new calls per authorized invocation and has no automatic
retries. The first API/format/input failure stops it. Three identical scores or repeated
unscorable responses trigger inspection. A stop gate blocks further calls on that packet;
diagnose and prepare a fresh reviewed packet. Completed calls are cached; an interrupted
intent is never automatically replayed because it may already have incurred a charge.

Prompt v1.1 now enforces null difficulty levels for context/unselected/uncertain units
in the API schema as well as local validation. The original pilot and rejected response
remain unchanged. Its packet is pinned to implementation commit `9fa5640`; use that
version to regenerate its reports. Fresh v1.1 requests must not be pooled silently with
the earlier prompt's scores. The rubric anchors and 20% dimension weights are unchanged.

## Framework integration

```sh
python run_all.py --difficulty-mode source-only \
  --design-inventory .cache/design_numeric/inventory/inventory.json \
  --design-packet .cache/design_numeric/pilot \
  --output-dir results/framework/numeric_design_pilot
```

This explicit mode avoids embeddings, live agents and empirical trial loading. The
historical default remains available. Multiple `--design-packet` options may combine
disjoint task subsets only under compatible rubric/prompt/model configurations.

## Files and extensibility

- `inputs.py`: static YAML/JSON/Python adapter and native τ-bench policies/tools/tasks.
- `rubric.py`: versioned scale, prompts and response schema.
- `judge.py`: offline packet preparation, evidence validation and bounded paid runner.
- `reporting.py`: mean of planned repeats per task, then equal-task dataset mean;
  median/spread, histogram counts, domain/workflow coverage and complete task inventory.
- `calibration.py`: frozen pilot and reliability/paired comparison checks.
- `crosscheck.py`: supplied-tag and structural-feature diagnostics after scoring.

For another dataset, produce the same `CaseBuilder` contract with scenario inputs,
requirements, relevant tool contracts, intended endpoint and source evidence. Supply
opaque judge-facing case keys; keep canonical IDs, labels, source paths/hashes and
comparison annotations outside the model payload. Preserve native representations:
τ-bench reference actions are not synthetic milestones or an exhaustive executed path.
Missing essential source material is explicit and never a zero difficulty score.

The default τ-bench adapter targets the checked-out `tau2-bench` base split (not τ-bench
v1), with the telecom manual policy. File hashes identify the exact sources; the local
revision is recorded where available. Full database records are not sent: this limitation
is explicit in the prompt, and cases requiring absent state must remain unscorable.
Supplied source documents themselves may still contain indirect complexity cues.

Add `--features results/difficulty/designed_v3/profiles.json` to the offline `report`
command to cross-check existing features. It never blends them into the numeric score.
Do not invent missing τ-bench tags, tune to copy supplied labels, or force one dataset
above another. Equal scores can be legitimate. Report incomplete averages as scored-
subset means and do not equate greater difficulty with greater dataset quality.

## Evidence validation v1.3

A genuine quotation from a task-specific milestone may support a shared workflow step.
The validator now records a `unit_uses_cross_reference` review diagnostic when a unit
has no direct unit-source citation, instead of rejecting the entire response. It still
requires exact, nonempty quotations from the same task's source catalog, valid unit
coverage/applicability, and consistent score arithmetic. A warning is not proof that
the cited source is semantically relevant.

This is a versioned validator-only correction: the generation prompt v1.1, schema,
inputs, weights, model and settings are unchanged. Existing raw responses were reassessed in fresh packets with provenance; no
generations were repeated. The original rejected responses remain unchanged.
Exact quotations may match the literal source or one decoded JSON string value,
so a documented line break is not rejected solely because JSON escaped it. No fuzzy
matching, whitespace rewriting or arbitrary concatenation across separate values is allowed.
One explicit structured rendering is recognized: an exact `signature -> ReturnType`
from the `signature` and `returns` fields of the same tool object. It is flagged as
`rendered_tool_signature`, not described as a literal quotation. Wrong annotations and
cross-object joins are rejected. This validator-only correction reassessed unchanged
raw responses without paid retries. Packets pin implementation hashes: old
reports should be regenerated using their recorded implementation revision, not by
silently rewriting old manifests. Revised validation policy is part of aggregation's
compatibility fingerprint.

## Task-bound generation schema

`design_schema_v1.2_task_bound_units` restricts generated unit IDs to the supplied task
and limits the number of unit rows. Local coverage and duplicate checks still apply.
An unscorable response may omit unit assessments. This changes the generation contract,
not the rubric or weights: prepare fresh packets and do not silently pool old/new schema
results. The 30-call domain report is frozen to implementation commit `c72a37e`; use that
revision to regenerate its outputs. Revalidation is not a license to accept invented units.

## Earlier run history

- [Original pilot](../../results/difficulty/numeric_design_pilot_v1/PILOT_REVIEW.md).
- [Matched v1.1 pilot](../../results/difficulty/numeric_design_matched_pilot_v11/README.md).
- [Initial development repeats](../../results/difficulty/numeric_design_repeatability_v11/README.md).
- [Authored source controls](../../results/difficulty/numeric_design_controls_v11/README.md).
- [First task-bound schema diagnostic](../../results/difficulty/numeric_design_schema_guard_v12/README.md).

Historical reports describe their own frozen cohorts and versions, not current full
dataset coverage. Their numeric scales, limits and raw-response provenance remain explicit.

## Verified evidence-reference format

Use `--source-bound-evidence` for schema v1.4 / prompt v1.3. The option now emits short
citation IDs rather than excerpt strings in schema enums. A deterministic evidence
index accompanies the full source catalog. Raw model-selected IDs and exact resolved
evidence are retained separately; scores and dimension levels are never rewritten.
This format passed all 64 final synthetic calls. The manifest's historical experimental
flag name is retained for compatibility. The earlier v1.3 excerpt-enum prototype was
API-rejected and remains preserved as a failed experiment, not a current result.
