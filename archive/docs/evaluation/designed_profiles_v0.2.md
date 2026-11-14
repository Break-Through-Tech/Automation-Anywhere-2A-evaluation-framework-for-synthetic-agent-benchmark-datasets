# Designed complexity profiles and complementary LLM review

Version: `designed_profiles_v0.2_provisional`
Status: source-bound assistant interpretation, not independent validation.
Scope: all 64 original synthetic tasks. v0.1 scores and supplied data are preserved.

## Why this revision

The v0.1 audit found that grouped milestone counts hide multiple operations and
coordination. Changing weights cannot separate tasks with identical inputs.
This version expands the profile instead of creating another arbitrary scalar.
The old numeric index is retained only as `v1_score_reference_only`; there is
no v0.2 combined score or new easiest-to-hardest ranking.

## Operational units

An operational unit is a proposed distinct active verb/object operation. Split
clear action clauses such as create the record, schedule an appointment and send
confirmation. Do not automatically split noun lists, data fields, audiences or
synonymous verbs such as prepared and assembled. Multiple recipients or records
may be scope/coordination requirements rather than separate operation types.
The number of calls and actual computational effort can differ from these units.

The full source milestone supports each interpretation. Exact atomic actions
remain unknown. Opaque groups are retained conservatively with an unresolved
flag; counts are not guaranteed lower bounds on actual executions. Passive
responses/approvals, waiting and pure completion signals are excluded from
active units. Role and business-check-group classifications retain v0.1 semantics
so this revision does not silently change a second axis at the same time.

All source-specific splits are explicit in designed_annotations_v2.json, never
produced by blindly splitting every occurrence of and or a comma. The profile
builder verifies complete canonical identity coverage, milestone wording and
roles, citation locations and all 21 source hashes. Source evidence proves where
an interpretation came from, not that the decomposition is uniquely correct.

## Coordination and repetition

Record requirements with deduplicated IDs and exact source evidence:

- Linked records: parent/patient links, duplicate-record merge or related claims.
- Approval: an explicitly required external decision, such as CFO override or
  accounts-payable resolution. Repeated mentions of one approval count once.
- Handoff: an explicit routing, dispatch or coordinator assignment. An automatic
  payment-approval marker alone does not establish a human handoff.
- Multiple parties: explicit distinct actors or entity roles, including owners,
  legal and adjuster coordination, or multiple specialist roles. This counts
  requirement groups, not a headcount. Overlapping requirements are visible.
- External response: an explicitly described patient/provider response.
- Multiple channels: an explicit requirement such as call and email.

No requirement annotated means zero documented under these rules, not proof of
absence. Requirements may overlap, so their counts must not be summed into a
new difficulty score without justification. The reference sequence also reports
repeated tool names and additional calls beyond one per tool; these are intended
repetitions, not observed agent behavior. Explicit wait groups remain separate.
This remains a partial operationalization: dependency graphs, substantive depth,
branch discovery and record multiplicities are not exhaustively established.

Examples: insurance-update onboarding has five active v0.1 milestone groups but
eight proposed operations. The two formerly tied insurance examples can now be
distinguished by explicit linked-claim and specialist-coordination requirements.
This addresses a coverage gap, not proof of a correct new ranking.

## Complementary LLM procedure for designed difficulty

The first small comparison now uses the [frozen counting rulebook](design_counting_rulebook_v0.1.md),
version `design_counting_rules_v0.1_frozen`. Its shared-event keys distinguish
coordination events from category tags, and it explicitly retains checks rather
than an inferred decision count. This clarifies review rules; it does not silently
relabel the earlier v0.2 profiles.


Use a separate design reviewer, not the execution outcome prompt:

1. Freeze source material and counting rules. Give the model the task-specific
   requirements, selected workflow, relevant tool definitions and guidelines.
   Mark expected calls as reference context, not an authoritative answer script.
2. Hide our score, counts, annotations, supplied easy/medium/hard tag and prior
   ranking. Source titles and prose still contain cues; this is blinding to our
   judgments, not complete blinding or an independent human review.
3. Ask for its own proposed operational units, business-check groups,
   coordination requirements and uncertainties, each supported by exact source
   citations. Do not ask it to choose weights or issue an unexplained score.
4. Validate schema, canonical task identity, source excerpts, duplicate units
   and source/request fingerprints. These checks establish structural and
   citation integrity, not semantic truth or completeness.
5. Compare the proposals offline. Differences in actions or coordination become
   a review queue. A difference may reflect granularity or interpretation,
   rather than an error. Preserve uncertainty, and do not auto-average counts,
   change weights or overwrite profiles to make the two assessments agree.

Three purposively selected source-only packets are prepared for emergency
property intake, commercial interruption, and insurance-update recovery. They
are not a representative or held-out sample. The first three paid requests are
[documented separately](../../results/difficulty/design_review_run_v1/README.md):
one incomplete-context diagnostic and two corrected-context reviews. They do not
establish a validated score.
Earlier `design_review_v1` and `design_review_rules_v1` packets are preserved as
superseded drafts. The first paid response exposed a nested-tool collection defect;
`design_review_rules_context_v1` contains the corrected tool-definition catalogs. The
validator rejects mismatched rule versions instead of silently reusing them.
The separate comparison target file must never be sent to the model. A source
catalog uses parsed/serialized source fields; citations quote that catalog,
with original file and field provenance retained for inspection.

Prepare fresh requests:

    python -m difficulty.design_feature_review --out results/difficulty/design_review_fresh

The module has no API client. Only messages from requests.json should be sent
by a separately authorized API runner. If used, start with at most three
sequential requests, preserving requested/returned model, settings, timestamps,
raw responses, exact request hashes and usage. Validate each before continuing;
stop after any API or validation failure or unresolved substantive disagreement.
Never automatically expand to all 64. The execution judge's met/unmet stopping
labels are not this review schema; here uncertainty/disagreement requires diagnosis.

Compare saved JSON response bodies:

    python -m difficulty.design_feature_review --packet results/difficulty/design_review_rules_context_v1 --responses /path/to/responses --out results/difficulty/design_review_compared_v1

Citation or count agreement is complementary AI corroboration, not benchmark
accuracy or independent validation. Same-family models may share biases. Keep
frozen versions and record accepted rule revisions explicitly. AI-only review
can speed internal checking, but cannot be represented as human validation.

## Where the existing outcome judge fits

The existing llm_judge.py has a different input and purpose: task references plus
an actual execution trace, to judge met/unmet/unverifiable with separate execution
eligibility. It can later supply supplementary runtime evidence under fixed
agent settings, excluding blocked or unverifiable attempts. It must not turn
an environment-caused failure into a designed-complexity penalty.

Once there are reliable, varied eligible outcomes, preplanned comparisons with
frozen designed features may provide external behavior evidence. Agent choice,
shared workflows, exclusions and limited trials affect that comparison. It is
not currently available or required to produce these profiles. Do not force
label diversity, use synthetic controls as benchmark ground truth, or conflate
the outcome judge with this source-only feature reviewer.

## Deliverables

    python -m difficulty.designed_profiles_v2 --out results/difficulty/designed_v2_fresh

profiles.csv gives all 64 profiles. profiles.json retains all operational splits,
coordination requirements, source citations and uncertainty. summary.json and
README.md explain coverage and limitations. Existing outputs cannot be overwritten.
The independent decision count and exact atomic action count remain null.
