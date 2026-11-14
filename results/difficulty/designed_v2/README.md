# Designed complexity profiles version 0.2

## What changed

All 64 tasks now include proposed operational units, repetition and source-backed
coordination requirements. Original v0.1 scores remain unchanged. There is no new
weighted scalar: adding weights before agreeing on overlapping features would
hide the uncertainty identified in the audit.

## How to read the profiles

Start with title and proposed_operation_unit_count. This is a conservative
assistant interpretation, not a minimum execution length or
an exact atomic action count. Only clearly distinct active operations are split;
noun lists, fields, audiences, prepared/assembled wording and opaque bundled work
are not automatically separate actions. Passive responses, waiting and completion
signals remain outside active units. Unresolved groups are explicitly counted.

Then read reference_tool_interactions and additional_reference_calls_from_repetition.
Repeated calls come from the supplied intended reference, not agent execution.
The coordination columns count documented requirements, not people or difficulty
points. They include approvals, handoffs, linked records, multiple parties,
external responses and multiple communication channels. One source requirement
can appear in more than one dimension; do not add these columns into a score.
Zero means no requirement annotated under these rules, not proof of no coordination.

## Examples that the old counts hid

- Emergency property: 8 old action groups; 8 proposed operation units; 0 linked-record, 0 multi-party and 2 handoff requirements.

- Commercial interruption: 8 old action groups; 8 proposed operation units; 1 linked-record, 2 multi-party and 2 handoff requirements.

- Insurance-update recovery: 5 old action groups; 8 proposed operation units; 0 linked-record, 0 multi-party and 0 handoff requirements.

The commercial and emergency claim examples can now be distinguished by their
coordination profile, rather than by changing weights on identical old counts.
That is better feature coverage, not proof that one has a particular true score.
All counts remain provisional assistant annotations with exact source excerpts.

## Complementary LLM review

A separate source-only reviewer can propose operational units, business checks,
coordination and uncertainties without seeing our counts, score, supplied difficulty
tag or earlier ranking. We compare the proposals and inspect disagreements.
It does not judge whether an agent succeeded. It is neither human validation nor
an automatic authority that overwrites the profile or supplies scoring weights.
Three blinded-to-our-features requests are prepared offline under
results/difficulty/design_review_v1. No paid LLM review has been run.

Full definitions: docs/evaluation/designed_profiles_v0.2.md.

    python -m difficulty.designed_profiles_v2 --out results/difficulty/designed_v2_fresh
