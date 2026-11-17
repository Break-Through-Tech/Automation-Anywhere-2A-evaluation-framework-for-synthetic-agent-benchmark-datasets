# Separate observed outcomes from difficulty eligibility

Version: `provisional_outcome_v0.3`
Status: user-authorized implementation on 2026-11-12; Sandra review pending.
Supersedes: v0.2 for new assessments only. Historical results keep their original policy.

## Outcome

Use met (pass) only when execution evidence supports the full requested outcome
for the correct entity and branch, including mandatory prerequisites and necessary
ordering. A terminal claim is insufficient. Equivalent valid methods are allowed.

Use unmet (fail) when evidence clearly establishes a material violation or actual
noncompletion. This describes the observed outcome, not who caused it. A supported
necessary environment blocker may coexist with unmet when noncompletion is clear.
Do not turn missing evidence, an omitted call by itself, or an agent's unsupported
claim into a failure. Give exact execution evidence for a decisive unmet finding.

Use unverifiable when conflicting requirements or insufficient evidence prevent a
reliable outcome judgment. A blocker does not automatically select unverifiable.
If the requirements themselves are materially unresolved and no decisive outcome
can be established, use unverifiable rather than inventing a resolution.

## Environment and eligibility

Return environment_assessment with status supported_blocker, suspected_blocker,
or not_established; prevents_required_execution (boolean); rationale; and evidence.
A supported blocker must identify necessary missing or conflicting material and
show why it prevents completion or reliable assessment. An agent claim alone is
not proof. A confirmed preventing blocker cannot coexist with met.

Return blocker_recognition with status supported_positive, unsupported_claim, or
not_established; rationale; and evidence. Supported recognition requires a supported
preventing blocker. Recognition is a separate positive diagnostic, never partial success.

Return difficulty_eligible (boolean) and difficulty_exclusion_reason (string).
Supported preventing blockers, unresolved suspected blockers and every unverifiable
outcome must be ineligible. Explain every exclusion. For eligible attempts use an
empty exclusion reason. A blocked unmet is logged as fail and still excluded.
Unassessed attempts and judge/API errors are not task outcomes.

## Evidence and calculation

All non-default environmental claims and met/unmet judgments require exact
transcript-relative locator/excerpt evidence. Reference material explains the
requirement but is not execution evidence. Read provided runtime contracts and
reference workflows without assuming reference-only information was agent-visible.
If necessary context is absent, record uncertainty; do not invent tool availability.

Execution difficulty is eligible unmet divided by eligible met plus eligible unmet.
With no eligible attempts it is unavailable, not zero or one. Preserve excluded
counts, reasons, policy version and evidence. Do not mix policy versions or silently
relabel historical judgments. This supports the difficulty-only project and adds
no separate correctness score. Designed difficulty remains the primary project work.
