# Designed difficulty metric v1.1

**Status: operational rules frozen for the authorized full clarified-protocol run.** The user approved up to 341 new calls with the documented uncertainty on November 13, 2026. Numerical results remain pending until the run and its audit finish. This is a project scoring convention, not independent proof of true difficulty or Sandra's approval.

## What the score means

Estimate the complexity of the work a capable agent would need to understand and perform from a task's design in a functioning environment. Read the scenario and initial trigger, applicable steps, milestones, tool contracts, policies, available state and valid exit requirements. Do not run an agent or measure correctness, failure rate or elapsed time.

A valid exit may be completion, refusal, cancellation or escalation. The source-only judge does not prove that an agent reached any exit.

## One numeric task score

Use the fixed 0–4 anchors in `numeric_design_rubric_v1.md` for five dimensions:

- **Workload:** breadth of required active work.
- **Reasoning:** interacting rules, choices and reconciliation within the work.
- **Tool use:** selecting tools and binding their inputs, outputs and state.
- **Dependencies:** prerequisites, linked state, approvals and handoffs.
- **Information:** required discovery, verification and reconciliation of inputs.

Each dimension has **20% weight**. Compute **judgment score = 5 × sum of the five levels**, from 0–100. Compute the total locally from unchanged model ratings and retain any raw-model arithmetic disagreement. Do not fit weights to labels, counts or a desired dataset ordering. A score of 80 is not proven twice as difficult as 40.

Review required/selected units individually. Task reasoning, tool-use and information levels must be at least their maximum required-unit levels; higher whole-task levels need a cross-unit explanation. Workload and dependencies describe the full applicable path. Milestones are requirements and are not automatically extra actions. Equal step counts can have different scores.

## Applicable-path convention

Use the exact tested addendum from `required_path_clarification_draft_v1.md`, without further wording changes. Include necessary discovery, authentication, applicable prerequisites and handoff preparation. Judge-only initial records are not facts already known to the agent. Do not assume an oracle or an exact shortest tool sequence.

Once a decisive mandatory exit is established, exclude later work unless sources independently require that work before the exit. Explain the chosen sufficient path when multiple orders are defensible. Flag conflicting policy rather than silently accumulating every branch. Exclude setup operations and inactive alternatives.

The retained API prompt still identifies the addendum as a development probe. Its exact bytes are intentionally preserved so cached observations and the completed repeatability study remain compatible. This release identifier records the operational choice; it does not rewrite the measured prompt or old results.

## Evidence, ambiguity and missingness

Keep supplied difficulty tags, label-bearing IDs/classes and previous scores outside the model input. Require source-linked evidence for unit applicability, dimension judgments and intended endpoints. Preserve quotes, uncertainties, source-quality flags, raw responses, hashes, model settings and version metadata.

The rubric is interpretive. A defensible score can retain specific source/rating uncertainties. Missing or conflicting essential design information that prevents a defensible assessment makes the case **unscorable**, not difficult by default and not an agent failure. API/parser/evidence errors never become numeric scores or zeros. Stop and diagnose errors; do not retry automatically or edit source data to obtain a score.

## Task and dataset aggregation

Preserve the original 342-task inventory and repeat convention: 64 synthetic tasks plus 278 native tasks; three native pilot tasks have three planned judgments and all other tasks have one. This gives 348 planned judgments. Seven exact same-request/same-repeat cached clarified judgments are reused; at most 341 new calls are authorized.

Average all planned usable judgments within a task first. If any planned judgment is pending, erroneous or unscorable, do not average only its convenient successes. Then average usable task means with equal task weights for each dataset. Publish scored/total coverage, missingness reasons, median, IQR, range and domain/workflow summaries. An incomplete mean is explicitly a subset result. Do not silently replace missing tasks with zero or give domains equal headline weight when their task counts differ.

All primary results for this run use the clarified prompt. Keep original-protocol scores in their historical report; do not patch a few cases into that mean. Controls, calibration repeats and partial semantic profiles do not enter dataset means.

## Validation and complementary analysis

The six-case paired development study has three judgments per prompt and case. The clarified arm passed frozen practical gates: maximum repeat range 10, mean range 3.33 and complex-versus-simple control gap 35. Required investigation and full packages were retained before handoff. These are consistency/source-review findings with prior scores visible, not independent accuracy or an ambiguity-free scoring scale.

Operations, reference calls, business checks, coordination and supplied tags remain complementary comparisons after scoring. They do not determine the numeric score or require 278 additional human reviews before reporting. Native semantic-profile coverage remains partial. Higher designed difficulty is not higher dataset quality, and native/synthetic scores may legitimately be similar.

## Implementation and audit

Use `difficulty/clarified_design_run.py` for this release. It leaves the original `difficulty/design/` core and old packets unchanged. The fixed arithmetic, schema, source-evidence checks and request-bound identity rules are reused. Its separate loader verifies the clarified prompt, source-bound model input, exact evidence schema, request hashes, case identities, repeat coverage and one generation configuration.

Use GPT-6 Sol with low reasoning and the existing 10,000-output-token cap. No automatic retries. Begin with three sequential requests; then allow at most three in flight. Stop new dispatch immediately on an unusable response or repeat range above 10. Already dispatched requests may finish and remain charged within the total 341-call cap. Persist spending intents before dispatch; unresolved intents are never replayed automatically. Preserve and diagnose stopped runs before continuing.

The prepared manifest is a historical preparation snapshot. `authorization_v27.json`, spending intents, progress, raw responses and execution logs record actual execution authority and usage. No API key is saved in those artifacts.
