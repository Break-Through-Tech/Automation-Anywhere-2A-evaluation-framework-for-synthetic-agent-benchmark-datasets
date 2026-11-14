# Provisional outcome rule for the three attempt retry

Version: `provisional_outcome_v0.1`
Status: authorized by the user for exploratory testing on 2026-11-07; Sandra's review is pending.

Apply this operational clarification to the existing draft rubric for this
versioned experiment. It does not approve the rubric or revise the original
human submissions, dataset, or historical rewards.

1. Establish the required outcome, applicable prerequisites, correct entity,
   and branch. If material conflicts make those semantics impossible to resolve,
   use unverifiable. Do not guess which conflicting source is correct.
2. When those requirements are clear and execution evidence conclusively shows
   noncompletion or a violation, use unmet. A demonstrated environmental blocker
   does not by itself erase an observable noncompletion or establish agent fault.
3. When the available evidence cannot reliably establish the required state,
   use unverifiable. Missing proof alone, an ambiguous failure, or an incomplete
   trace must not be converted into a conclusive failure.
4. Use met only when all applicable material requirements are supported. Correct
   pausing or escalation is distinct from completing the business outcome unless
   the task itself accepts that handoff as its endpoint.
5. Retain clearly established subconditions, even if the overall task is
   unverifiable. Do not label every milestone unmet simply because the task did
   not complete. Empty milestone evidence is acceptable only for unverifiable.
6. Record environmental observations separately from completion and behavior
   quality. Distinguish observed conflicts from suspected blockers; do not claim
   the environment caused all failures. Judge-output errors are not agent failures.

For this exploratory retry, apply the clarification instead of automatically
returning unverifiable solely because a policy decision is pending. Explain
remaining material uncertainty. No empirical difficulty or denominator is
computed. A conclusive unmet outcome with an environment blocker does not
establish intrinsic agent difficulty and may still be ineligible under the
draft denominator proposal. That denominator remains unapproved.

The experiment records this policy's hash and version separately from the
original rubric and prompt hashes. Sandra's later decision may require revising
the policy and rejudging affected attempts, not merely recomputing a percentage.
Original human answers remain unchanged and are not sent to the judge.
