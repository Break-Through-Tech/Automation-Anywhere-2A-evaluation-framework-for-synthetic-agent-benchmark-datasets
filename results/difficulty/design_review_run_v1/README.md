# Results of the three source only LLM reviews

## Main conclusion

The complementary review is useful: it corroborated the commercial-claim profile
and exposed requirements our milestone-focused extraction may omit. It does not
validate the difficulty score. Clarify requirement scope offline before more paid
reviews or automatic changes to the profiles.

Exactly three GPT-6 Astra requests were used, with no retries, expansion or agent
runs. Original scores, profiles, source data and human labels remain unchanged.
All three responses passed schema and exact source-citation checks. The first
had incomplete tool context, so it is not equivalent to the other two reviews.

## What happened

1. Emergency property claim: eight operations and three checks, matching our
   candidate. The model proposed one additional whole-case multi-party requirement
   and flagged source conflicts. It also correctly identified an empty tool
   catalog. This was our packet-builder defect: YAML definitions were nested in
   system_tools/domain_tools lists, while our filter expected top-level tool names.
   We stopped, fixed the parser offline, added coverage tests, and preserved this
   first response without retrying it.
2. Commercial interruption claim: the corrected packet included the relevant
   definitions. The model proposed eight operations and three checks, matching
   our candidate. It also matched one linked-record, two multi-party and two
   handoff categories. Shared event keys represent these as three coordination
   events rather than five independent events. Opaque linked-claim creation,
   specialist dispatch support and inconsistent escalation/input details remain
   source uncertainties; count agreement does not resolve them.
3. Insurance-update onboarding: the corrected model proposed twelve operations
   and five checks versus our eight operations and two checks. Its four additional
   operations came from global instructions: initial field validation, renewed
   validation after the update, duplicate detection and access logging. Some are
   credible coverage gaps; logging's agent-versus-infrastructure boundary remains
   unresolved. The model additionally treated two payer API returns as external
   responses and ordinary patient/provider scheduling links as linked records.
   Those expose taxonomy questions rather than automatically accepted additions.

No profiles were overwritten to match the model, and no larger paid run followed.
The original request budget was honored across the interrupted and corrected runs.

## What we should clarify next without API calls

- Include applicable explicit global prerequisites in the effective requirements,
  rather than treating milestones as the whole task. Record applicability conflicts
  instead of adding every global guideline to every task indiscriminately.
- Separate explicit agent work from ambient compliance or infrastructure behavior.
  Do not invent a logging action when the automation boundary is unknown.
- Reserve external-response coordination for an additional person/organization
  response or asynchronous dependency; ordinary synchronous tool returns should
  not automatically duplicate the tool-interaction feature. This is a proposed
  clarification, not a silent amendment to the frozen rules.
- Distinguish a required link/merge/synchronization obligation from merely passing
  routine patient or provider IDs. Define case-level versus event-level multi-party
  grouping consistently. Keep unresolved interpretations visible.

These clarifications belong in the next rule version. The first comparison's
rules, request hashes and responses remain frozen. Missing tool inputs and source
contradictions are separate data-quality findings, not difficulty penalties.

## Evidence and limits

combined_summary.json records counts, token usage, source versions and inspection
notes for all three requests. input_context_diagnosis.json records the confirmed
packet defect and the corrected tool coverage: nine named definitions for each
insurance task and eight for insurance-update onboarding. The earlier stopped
run is in run_summary.json; corrected results are in corrected/run_summary.json.

Raw requests and responses are retained locally under .cache/design_review_run_v1
and .cache/design_review_corrected_run_v1. The corrected validator snapshot is
preserved alongside its run. The two versions are explicitly distinguished;
there is no pooled accuracy, inter-reviewer agreement or validated difficulty claim.
Exact citations establish source provenance, not correct semantics or completeness.
Model judgments are not independent human validation.

All 105 offline tests passed, including the new nested-tool coverage checks.
