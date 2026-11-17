# Recommendation on presenting designed difficulty

## Recommendation for Sandra

Use the v0.3 feature profile as the primary designed-difficulty measure. Report
operations, intended tool interactions, checks and explicit coordination together,
with uncertainty flags. Keep the experimental combined index secondary and do
not call it a validated final score. This is a concrete project deliverable;
choosing an unsupported universal weighting is not necessary to present it.

If a single number is required, show the 80% workload / 20% additional-coordination
index as a transparent candidate for discussion, not an adopted score or a failure
probability. I do not recommend declaring its 20% coordination weight final: it
moves ranks substantially. The weight is an assumption, not a learned optimum.

## What was checked

All 64 profiles reproduce from their frozen inputs. The 12 changed tasks retain
source evidence for all 22 additional operations; covered checks, the self-pay
exception, update phases and deduplicated AP/claim events are tested. There remain
25 tasks with unresolved global duties, plus retained action-granularity flags.
These are interpretation limits, not agent failures. No API calls or profile,
score, source-data or model-response edits were made.

## Options compared

- Profile only: no scalar or rank. It preserves distinctions and uncertainty but
  requires reading several features. This is the recommended primary output.
- Operations only: 100 × operations / 11. Simple workload baseline, but a bulk
  milestone can hide repeated work. The three-claim batch has eight operation
  groups, so this alone does not express its 23 intended reference calls.
- Workload only: 100 × (operations / 11 + reference calls / 23) / 2. Captures
  reference repetition as well as required work, but the two inputs overlap and
  reference call counts can be incomplete. This is not double-count-free truth.
- Workload plus coordination: 100 × [0.4 × operations / 11 + 0.4 × calls / 23
  + 0.2 × additional-coordination events / 3]. It excludes handoff-only events
  already represented by routing/dispatch actions. An event carrying several
  categories counts once. Business checks are not added again as a scored term
  because they are already active evaluations. Residual overlap remains: linked
  records, approvals or multiple-role coordination may still be reflected in work.

Scales 11, 23 and 3 are frozen to this v0.3 64-task snapshot, not inherited from
v0.1 or refitted per domain. No easy/medium/hard cutoffs, uncertainty penalty or
validated confidence intervals are introduced. All ranks are conditional on the
current documented counts; ambiguous duties are not silently imputed.

## Concrete examples

The emergency property and commercial interruption cases both have eight
operations and eight reference calls. They tie at 53.75 on workload alone.
After counting additional coordination once per event, they have zero versus
three such events. The 80/20 candidate becomes 43.00 versus 63.00.
This shows that the feature distinguishes requirements. It does not establish
that the 20-point difference is the correct amount of difficulty.

The catastrophe batch remains higher at 69.09 under that candidate because its
three-claim reference contains 23 business calls. That expresses work volume,
not proof that its reasoning is harder than a commercial claim.

## Sensitivity and limitations

Using coordination weights of 0%, 10%, 20%, 30% and a 50% stress case changes
rankings. At 20%, the largest rank change from workload-only is 19.5 places.
More distinct scores or resolving a preferred tie is not validation. Do not tune
weights to supplied tags, the assistant's ranking or these selected examples.
This comparison does not use agent outcomes or claim independent validation.

## Suggested meeting statement

“We have a reproducible designed-complexity profile for all 64 tasks. The source
review and LLM experiment helped us find omitted global requirements and clarify
coordination. I recommend the profile as the main result. If one number is required,
we have a transparent workload-plus-coordination candidate, with explicit weights
and sensitivity results, rather than claiming it is already validated.”

## Files and reproduction

scoring_options.csv contains all exploratory indices and ranks. comparison.json
contains input fingerprints, the 12 changed-task checks, formulas' inputs and
summary statistics. weight_sensitivity.csv keeps all tested coordination weights.
Current profiles and previous indices are separate and remain unchanged.

    python -m difficulty.compare_designed_scoring --out results/difficulty/scoring_options_fresh
