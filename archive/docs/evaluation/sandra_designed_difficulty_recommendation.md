# Recommendation for presenting designed difficulty

## Main recommendation

Present designed difficulty as a **feature profile for each task**, with thex
combined index as a secondary experiment. This makes the required work visible
without implying that an arbitrary weighting is a validated measurement.

We have profiles for all **64 tasks across seven domains**, covering proposed
operations, intended tool interactions, business checks and explicit coordination.
Reviewing global requirements added 22 operations/checks across 12 tasks. Twenty-five
tasks still have unclear global duties; those remain flagged without invented
work or automatic penalties. Exact atomic actions and independent decisions are
not established. The profiles are provisional source interpretations.

## What the scoring comparison showed

- Operations alone is simple, but grouped batch operations can hide repetition.
- Combining operations and reference calls captures more work volume, but those
  features overlap and the supplied references can be incomplete.
- Adding coordination distinguishes linked claims and multiple specialist roles.
  We count events once across tags and exclude handoff-only events from the extra
  coordination term. This reduces obvious duplication but does not eliminate overlap.
- A 20% coordination weight can move a task by 19.5 rank places. That weight has
  not been shown to be the correct one.

For example, emergency property intake and commercial interruption tie on workload
alone. Coordination separates them, but we cannot justify a particular numerical
gap as true difficulty. A three-claim batch scores highly because of work volume,
not proven reasoning difficulty.

## The role of the LLM judge

The source-only LLM reviewer helped identify omitted global requirements and
ambiguous feature boundaries. It supports consistency checking, not independent
human validation. The execution judge remains supplementary and separate from
this designed-difficulty deliverable.

## Decision to confirm with Sandra

Is a transparent feature profile sufficient as the main designed-difficulty
measure? If the project requires one number, present a clearly provisional
workload-plus-coordination index with its formula and sensitivity, rather than
claiming its weights are validated. No new API run is needed for this decision.
