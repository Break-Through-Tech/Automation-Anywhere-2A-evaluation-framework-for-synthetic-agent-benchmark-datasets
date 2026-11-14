# Counting designed complexity with clarified requirement scope

Version: `design_counting_rules_v0.2_scope_clarified`
Status: applied offline to v0.3 profiles at the user's request; provisional, not independently validated or Sandra approved.
Supersedes: v0.1 for new profile interpretations only. Earlier rules and model requests remain frozen.

## Main rules

Use the active-operation and business-check definitions in v0.1, with these scope clarifications:

1. Effective requirements include task milestones and applicable explicit global
   guidelines. Inspect every guideline for every task. Mark it as already covered,
   added, not applicable to this phase, conditional branch not selected, uncertain,
   or constraint only. Cite the guideline and task-specific phase evidence.
2. Add an operation only when required work is explicit, applicable and distinct
   from the existing operations. Reuse an existing evaluation when its contract
   already encompasses the policy. Do not duplicate a check just because its
   result selects an action. Do not assume every generic guideline creates a
   new action in every task. A separate required phase, such as validation after
   changed information, can require another evaluation.
3. Keep ambiguous infrastructure/compliance duties separate from agent work.
   Access logging, audit trail and security wording are not automatically extra
   operations. Their scope or actor can remain uncertain without inflating counts.
4. External-response coordination means an additional human/organization response
   or asynchronous dependency. Ordinary synchronous tool/API returns are already
   represented as interactions and do not automatically add coordination.
5. Linked-record coordination requires explicit link, merge or synchronization
   work beyond ordinary IDs in arguments. Parent links, record merges and linked
   claims qualify. Passing patient_id and provider_id for normal booking alone
   does not. An explicit additional synchronization obligation can qualify.
6. Count events before category tags. The same AP review cited as a handoff and
   an approval has one event key and two nonadditive tags. Multi-party groups
   must identify event-level distinct role obligations; do not add another
   whole-workflow event merely because several actors occur somewhere in it.

Uncertain duties remain in the profile with rationale. A zero count is not proof
of absence. Source conflicts, missing tools or unavailable inputs are data-quality
findings rather than added difficulty penalties. No unmentioned tool calls are
invented to implement a logical requirement.

## Worked interpretations

- Insurance-update onboarding includes initial field validation, validation after
  changed information and duplicate detection because global rules explicitly
  require those evaluations. They are absent from the old milestone-only count.
  Access logging remains separate because who performs it is unspecified.
- A missing-information task already identifying required missing fields does
  not receive another initial-field check for the same phase. Validation after
  the response is distinct. An existing duplicate-search step is not duplicated.
- Self-pay onboarding has no insurance-verification operation under the explicit
  self-pay exception. Demographic validation and duplicate detection still apply.
- A status-only PA task does not gather documents or submit a new request, so
  prerequisites triggered by those phases do not automatically add operations.
- A risk evaluation returning a recommended action can encompass threshold-based
  routing. Do not add an independent check solely because the output selects a
  route, unless the source explicitly requires a separate evaluation.
- Clinical validation and document preparation can already cover readiness. When
  an urgent submission has no explicit clinical-criteria evaluation, the global
  prerequisite is retained as required work even if the reference omits it.
- One AP-review event can have approval and handoff tags. Two ordinary payer API
  results do not become two additional external-response events.

## Implementation boundary

The v0.3 source-bound annotation file records applicability decisions and distinct
added operation keys. Its dispositions are assistant interpretations, not ground
truth. Ambiguous authority limits, human-review scope and audit duties remain
uncounted uncertainties or constraints. Existing reference call counts do not
increase just because a logical requirement is added.

No new scalar is computed. The original normalization/scales must not silently be
reused for changed feature definitions. Original task data, v0.1 scores, v0.2
profiles and the three LLM responses remain unchanged. No new API run is implied.

The earlier LLM review module remains tied to the earlier frozen rulebook, so its
old packet/results are not presented as reviews under this revised scope. A future
paid comparison needs a new explicit packet version and authorization.
