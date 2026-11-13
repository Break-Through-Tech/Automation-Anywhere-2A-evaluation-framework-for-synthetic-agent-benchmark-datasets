# Numeric design difficulty — start here

This mode reads task designs and asks an LLM for evidence-backed difficulty ratings.
It does not run task agents or grade saved attempts. The implementation and offline
checks are ready; full calibration requires authorized API calls. The first three-call
pilot produced two accepted scores and one rejected response; see
[the pilot review](../../results/difficulty/numeric_design_pilot_v1/PILOT_REVIEW.md).
A separate approved v1.1 insurance retry returned an accepted 70/100; see
[the retry report](../../results/difficulty/numeric_design_insurance_retry_v11/README.md).
The matched v1.1 pilot now has accepted scores **65, 65 and 70**; see
[the comparison and limits](../../results/difficulty/numeric_design_matched_pilot_v11/README.md).
The [initial repeatability check](../../results/difficulty/numeric_design_repeatability_v11/README.md)
passes on three development cases: accounts 65/65/65 each, insurance 70/70/75.
The [four source controls](../../results/difficulty/numeric_design_controls_v11/README.md)
now pass their practical tolerances (35, 75, 40 and 40). Broader calibration remains: a
[domain calibration](../../results/difficulty/numeric_design_domains_v12/README.md) now has
nine complete three-judgment cases within tolerance. Thirty calls were used under an
extended cap of 31. Airline stopped on an invented-unit response after its input-context
gap was diagnosed; full calibration remains incomplete. No paid retry followed that error.

1. Read the [short rubric](../../docs/evaluation/numeric_design_rubric_v1.md).
2. Prepare source inputs and a three-task request packet offline.
3. Obtain approval for API credits, run the bounded pilot, and inspect its explanations.
4. Complete the [calibration protocol](../../docs/evaluation/numeric_design_calibration_v1.md)
   before broader scoring. Implementation completion does not imply validation.
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
  --selection pilot --model gpt-6-sol --reasoning-effort low --out .cache/design_numeric/pilot
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

## Evidence validation v1.2

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
matching, whitespace rewriting or concatenation across separate values is allowed. Packets pin implementation hashes: old
reports should be regenerated using their recorded implementation revision, not by
silently rewriting old manifests. Revised validation policy is part of aggregation's
compatibility fingerprint.
