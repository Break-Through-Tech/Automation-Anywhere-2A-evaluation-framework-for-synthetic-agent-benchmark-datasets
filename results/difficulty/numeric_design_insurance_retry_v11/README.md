# Insurance-only GPT-6 Sol retry — accepted score 70/100

The one additional call authorized by the user completed successfully under prompt v1.1.
All 18 source units were assessed. Context-only units correctly have null ratings.
Schema, task identity, exact quotations, applicability, step/task consistency and arithmetic checks passed.
No other paid calls were made in this follow-up.

Task: InsuranceClaimsIntakeAndTriageAgent_W8_TC1, commercial property and business interruption.
Dimension levels: workload 3, reasoning 3, tool use 3, dependencies 3, information 2.
The frozen formula gives 5 × (3+3+3+3+2) = 70/100.

The explanation cites linked property/BI claims, specialist engagement, prerequisites,
and prior results used by later tools. It still flags ambiguities in how the supplied
vendor-dispatch contract fulfills the specialist requirement. Those are source observations,
not confirmed defects or proof of execution. No task agent was run.

## What this establishes

The revised schema/prompt worked for this response, and the returned score has source evidence.
This is not full judge calibration, an independent difficulty label, or a representative dataset score.
The earlier rejected response remains rejected, even though it also proposed 70.
Agreement across different prompt versions is not a controlled repeatability check.

The earlier account scores (60 and 65) used prompt v1. They are kept separate from this
v1.1 result. Do not combine their means or claim a validated ranking across versions.
The two separately authorized account reassessments have now completed under v1.1.
See [the matched pilot](../numeric_design_matched_pilot_v11/README.md): both account cases
score 65, while this insurance case scores 70. Original prompt-v1 scores are not pooled.
The subsequent six-judgment repeatability check is complete: [repeatability report](../numeric_design_repeatability_v11/README.md). Full calibration remains incomplete.
Repeat/control/held-out checks and broader scoring remain pending.

## Evidence and usage

See retry_evidence.json, source_bindings.json, run_manifest.json, and task_scores.csv.
Raw response and exact request remain in the local frozen packet named in the manifest.
This call reported 8,862 input tokens and 2,459 output tokens (11,321 total).
Token usage is not a dollar-cost estimate or billing audit. The dataset and earlier judgments are unchanged.
