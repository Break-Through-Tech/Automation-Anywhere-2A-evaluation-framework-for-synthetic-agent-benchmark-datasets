# Provisional designed difficulty method

Version: `designed_difficulty_v0.1_provisional`
Status: usable first implementation; assistant annotations; no independent validation.
Scope: all 64 original synthetic tasks in seven domains. No agent runs, outcome
judgments, paid API calls or human reviews are needed to reproduce this measure.

## Purpose and the three inputs

Estimate designed task complexity from the intended requirements, assuming the
intended environment functions. The 0–100 output is an index, not a percentage
failure rate. It is not calibrated to tau2-bench. Keep the component profile
alongside the combined number.

1. **Active action groups.** Count one task-specific milestone describing active
   work. Exclude pure completion signals, passive patient/provider responses,
   external approval receipt and waiting. Use the task's milestones rather than
   every shared YAML branch. A group can contain several operations or entities:
   this is a requirement-granularity proxy, not an exact atomic action count.
2. **Reference business-tool interactions.** Count the supplied intended calls,
   including repeats. Exclude SUCCESS, FAILED, CANCELLED and HUMAN_IN_THE_LOOP.
   Do not substitute actual baseline call counts or judge outcomes. The reference
   can itself be incomplete or questionable; this is an intended-path signal.
3. **Business-check groups.** Count explicitly annotated active milestones whose
   work assesses, verifies, classifies or reconciles information. Several checks
   bundled into one milestone count once. Configuration, communication, retrieval
   and routing alone do not automatically qualify. This is an evaluative-work
   proxy, not the number of choices the agent must independently discover.

The last distinction matters: an expected result can be fixed in the reference
while the agent still needs to perform a check. Conversely, an already selected
workflow does not establish that the agent must choose among all its branches.
The method does not claim to resolve this with a keyword detector. Exact atomic
steps and independent decisions remain null rather than being fabricated.

## Annotation provenance

`difficulty/designed_annotations_v1.json` explicitly records every milestone of
every canonical task, its exact source wording, role and business-check flag.
The assistant inspected the task milestone descriptions to prepare these labels.
They are not independent human labels or benchmark truth. All active groups are
assumed relevant to the task's supplied intended path; unresolved conditional
applicability and bundled work are flagged. This is a source interpretation,
not an execution audit or proof that all tasks are feasible.

Every run checks the complete canonical task set, all milestone identities,
wording/order and all 21 source hashes. JSON evidence locators use the checked
JSON-ID-to-canonical-ID mapping; Python class lines and workflow pointers remain
in each record. Supplied data, saved attempts and human judgments are not edited.

## Formula and weights

For A active groups, T reference business calls and C business-check groups:

    score = 100 * ((A / 9) + (T / 23) + (C / 4)) / 3

Each normalized component has weight one-third. The fixed denominators 9, 23 and
4 are the observed maxima in the original 64-task snapshot under these counting
rules. Zero means zero counts, not a claim that a task is effortless. Larger
values indicate more complexity under this method. The observed maximum need
not be 100 because no single task need maximize every component.

Do not fit scales per domain or new batch; that would make scores incomparable.
Counts outside the frozen ranges stop scoring instead of clipping or silently
changing the scale. A new task collection or different counting rules needs a
versioned calibration decision. No easy/medium/hard cutoffs are invented.

Equal weights are an explicit starting assumption, not a learned or validated
choice. Action groups, calls and checks overlap and can double-count some work.
The output therefore also computes action-heavy (.50/.25/.25), tool-heavy
(.25/.50/.25) and no-check (.50/.50/0) variants with tied average ranks. Sensitivity
is a robustness description, not validation or a reason to select whichever
weights reproduce preferred rankings. Supplied tags and the assistant's six-task
ranking are comparison context only and never score inputs.

## Known limits demonstrated by examples

- Approved PA status uses three task milestones, not every shared workflow step.
- Insurance-update onboarding excludes the passive response and final signal,
  but a record/schedule/communication milestone still bundles several actions.
- An easy emergency property claim and a hard commercial interruption claim
  can receive identical components. Linked claims, specialist coordination and
  depth of reasoning are not adequately represented by this version.
- A batch reference has many repeated calls and scores highly. Batch size and
  how the source expresses work affect this result.
- No additional penalty is added for missing inputs, invalid reference arguments
  or conflicting mocks. Those are data-quality issues, not designed work. A source
  issue can still contaminate a reference-based count; the score does not certify
  the source or establish runnable-task eligibility.

## Outputs and reproduction

    python -m difficulty.designed_difficulty --out results/difficulty/designed_v1

Use a fresh directory; existing outputs are never overwritten. Main files:

- scores.csv: all 64 scores, counts, tied ranks and uncertainty flags.
- scores.json: full source-backed evidence, annotations and version fingerprints.
- summary.json: domain summaries and supplied-label summaries, descriptive only.
- weight_sensitivity.csv: scores/ranks under all four weight choices.
- README.md: short guide and limitations.

Optional full-framework attachment:

    python run_all.py --synthetic-designed-scores results/difficulty/designed_v1/scores.json --output-dir results/framework/designed_v1

That full framework also computes coverage embeddings; it is not needed to
compute designed difficulty. The optional attachment checks identities, source
hashes and a full offline rebuild before adding `designed_index_` columns.
Empirical difficulty and previous write-count results remain distinct.

## What is complete and what is not

The provisional measure, per-task evidence, reproducible scoring, sensitivity
report and framework attachment are implemented. A final validated metric is not
claimed. Without independent review, tests establish implementation integrity,
not that the index measures true complexity or predicts agent performance.
Sandra can approve or revise the definition and decide whether one scalar is
needed. Refining task-specific atomic actions, decisions and coordination, and
checking on fresh independent assessments, remain future validation work rather
than hidden completed steps.
