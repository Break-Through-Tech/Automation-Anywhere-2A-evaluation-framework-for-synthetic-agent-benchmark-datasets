# Outcome and environmental blocker clarification

Version: `provisional_outcome_v0.2`
Status: user-directed clarification on 2026-11-08; Sandra's review remains pending.
Supersedes: `provisional_outcome_v0.1` for future assessments; previous results are retained under their original policy.

## Full requested outcome

Success means the requested result for the correct entity and branch, with the
required inputs, permissions, prerequisites, and necessary ordering supported
by execution evidence. Required milestones are part of that assessment.

An agent's answer or terminal SUCCESS claim is insufficient. A recorded result
obtained by skipping a mandatory prerequisite is not success. A correct-looking
or lucky answer is not proof of proper execution. Equivalent valid methods and
harmless ordering differences remain allowed; exact sequence matching is not
required. Do not invent additional requirements beyond the supplied task.

If references conflict about which milestones are mandatory or omit an operation
needed for the requested outcome, record the conflict rather than inventing a
requirement or accepting an unsupported success.

## Missing environmental material

When necessary information, documents, tools, or other supplied environmental
material are missing or contradictory and this prevents the required execution
or reliable assessment, classify the attempt as **unverifiable** and exclude it
from the difficulty denominator. Keep it in a separate blocked/unverifiable
report with the missing material, evidence, and affected requirement identified.

Do not infer agent failure from the blocked outcome. Correctly identifying a
necessary missing item and safely pausing or escalating is a positive behavior
diagnostic, even though the full requested outcome could not be established.
Record that observation separately; do not turn it into a fractional completion
reward, a pass, or an input to the difficulty score.

Distinguish a supported environmental blocker from an agent merely claiming
that information or tools are unavailable. A missing optional detail, harmless
format mismatch, or unsupported demand by the agent does not automatically
make a task blocked or unverifiable. Where the environment provides what the
task needs and the agent demonstrably skips a required feasible action, unmet
can still be appropriate. An unresolved suspected blocker requires an explicit
uncertainty explanation rather than an assumed feasible or impossible path.

## Reporting and denominator

Keep outcome, environmental assessment, and blocker recognition separate:

- Outcome: met, unmet, or unverifiable, with supported mandatory milestones.
- Environmental assessment: blocker supported, suspected, or not established;
  identify what is necessary, what is missing/conflicting, and how execution
  or assessment is prevented. Retain the original trace references.
- Blocker recognition: supported positive behavior, unsupported claim, or not
  established. This diagnostic is not a difficulty contribution.

Only assessable met/unmet attempts enter difficulty's eligible denominator.
Environmental-blocked/unverifiable attempts contribute neither a pass nor a
failure. Report their counts and reasons separately. If every attempt is
excluded, difficulty is unavailable, not zero or one. Judge/API errors are also
separate from agent failure. This clarification is not approval of every other
open rubric or denominator decision.

## Existing evidence and next assessment

Do not overwrite the original human answers or relabel the sixteen saved v0.1
model judgments as v0.2. Reassess the sample under this version before drawing
new difficulty conclusions. Preserve positive milestone findings and blocker
recognition, rather than assuming that all unexecuted milestones failed.
Record any revised assessment with this policy version, source evidence, and
the reason for a change. The earlier 10/16 label match is an observation under
v0.1, not validation of the revised rule.
