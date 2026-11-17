# Working evidence expectations for the original synthetic benchmark

Version: `evaluation_expectations_v0.1`
Status: offline working interpretation under user policy v0.2; not Sandra's approval.

These expectations preserve the user's requirement for a supported outcome and
mandatory prerequisites, while avoiding requirements that the supplied simulation
cannot establish. They do not edit the dataset, human labels, or completed runs.

## Accepted completion evidence

Judge completion within the supplied simulation, not a real bank, insurer, or
external database. A relevant mock operation can support simulated completion
when its inputs identify the requested entity, required prerequisites are
supported, and the returned fields meaningfully confirm the requested operation.
Additional independent real-world proof is not required for every mocked action.

A terminal SUCCESS message alone is insufficient. Its structured result can
support that a decision was recorded, provided required preceding checks and
inputs are supported. It does not automatically prove a separate approval,
account mutation, notification, or case closure. Only accept that stronger
meaning if the benchmark explicitly defines the recorded decision as the whole
accepted endpoint and the supplied contracts consistently support that meaning.
Do not silently redefine an approval task as a recommendation task to obtain a pass.

Expected tool names are checkpoints, not success proof. Exact incidental order
is unnecessary; mandatory dependencies still matter. Do not require every
generated ID or numerical reference literal to match if its difference is harmless
and correct entity linkage and branch are supported. Record material scenario
conflicts separately instead of guessing which reference is authoritative.

## Input sufficiency and agent behavior

Distinguish data in the simulator's scenario from data actually provided to the
agent. The recorded conversation and reconstructed agent-visible instructions
establish that exposure. The agent must not be assumed to know hidden scenario
values. Conversely, an agent's unnecessary request is not proof of a necessary
environmental blocker.

Schema-valid input is not automatically semantically sufficient for proper
identity, compliance, or other mandatory checks. Partial-object schemas can
accept calls without proving that the underlying check is meaningful. Where
minimum required semantic inputs are not specified sufficiently to judge a
feasible omitted action, retain the uncertainty and exclude the assessment
from difficulty rather than infer failure or invent required fields.

Correct recognition of a necessary blocker is a separate positive diagnostic.
Do not award it for a generic escalation or an unsubstantiated claim. Supported
workflow actions can be retained as diagnostics without claiming overall success.

## Current case decisions and spending

R01 remains unverifiable because proper input sufficiency is unresolved. Its
noncompletion is observed; neither agent fault nor an environmental impossibility
is conclusively established. R15 remains unverifiable because its material
reference/mock disagreement and accepted approval endpoint are unresolved.
Neither contributes to difficulty. Detailed evidence is in
`results/judge_review/v5/offline_adjudication.json`.

The small paid test stopped after two non-success judgments. Keep further broad
paid judging stopped while resolving these benchmark-contract questions offline.
Do not tune labels until they vary. Any future resolved endpoint interpretation
needs a new version and fresh assessment; preserve earlier labels and policy hashes.
