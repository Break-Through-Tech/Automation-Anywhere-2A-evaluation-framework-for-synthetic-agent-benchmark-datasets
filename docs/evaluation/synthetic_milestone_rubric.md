# Synthetic milestone evaluation rubric

Version: `synthetic_milestones_v0.1_draft`  
Status: proposed for team review under GitHub issue #45  
Scope: original supplied synthetic tasks and original saved attempts

We propose judging whether the recorded attempt supports the task's intended
outcome and explicit prerequisites. Expected tool sequences provide reference
context. Sequence similarity, a terminal SUCCESS call, and a simulated user's
stop message do not by themselves establish completion. No existing reward is
changed by this document or the accompanying offline review.

## What is being judged

Keep four separate questions in each assessment:

1. What outcome and prerequisites does the task require?
2. What does the trace establish about completion within the supplied simulation?
3. Is the behavior reasonable given what the agent could observe, including
   contradictions, missing inputs, and the tools actually available?
4. Is the task and trace sufficiently consistent and observable to support an
   empirical difficulty label under this rubric?

A justified escalation can answer question 3 favorably while the requested
business outcome remains incomplete. It is a successful task outcome only when
the task's accepted endpoint is that escalation and the required handoff is
supported by the trace. An acknowledgement is not proof that the human carried
out the requested action or gave approval.

## References and conflicts

Read the scenario input, title and description, selected workflow and explicit
guidelines, milestones, expected outcomes when supplied, expected calls, and
tool contract. Record the original task ID, class, source location, and input
hashes. Do not infer a Python-to-JSON correspondence from a similar name alone;
issue #46 supplies the checked mapping for broader implementation.

Use expected calls to identify intended entities, operations, and dependencies,
not as an exact-answer script. A milestone may describe a state not directly
returned by a tool. Any mapping from returned fields to that state must be
explicit and reviewable. For example, a field called `status` does not satisfy
every milestone containing the word status.

When sources conflict on a material requirement, record both sources and route
the conflict for adjudication. Do not silently prefer a reference literal over
observed tool data, prefer a mock over the scenario, invent missing values, or
change the supplied source. Missing tools and inaccessible required information
are findings, not invitations to fabricate a successful trajectory.

Dates, generated IDs, entity names, amounts, and units require interpretation.
Bind outputs to the entity requested and carry returned IDs consistently.
Different generated IDs may be acceptable only if their linkage is supported;
this does not authorize ignoring a mismatched customer or transaction. Assess
date-related claims relative to the run's available date context, not today's
review date. A frozen date may be a fixture issue rather than an agent error.

## Milestone judgments

For every milestone, record its requirement, whether it is applicable and
material, the source of that decision, a judgment, evidence locators, and any
contradictions. Applicability must be justified; unresolved applicability is
unverifiable, not silently omitted.

- **Met:** trace evidence supports the required condition for the correct entity
  and branch, including material prerequisites. A normal mock response may
  establish a simulated operation to the extent its inputs and semantics
  support it. It cannot establish a real external database change.
- **Unmet:** sufficient evidence establishes that the applicable requirement
  was violated or not achieved within the recorded attempt. Examples include
  an explicit unsuccessful response or a complete tool log with no execution
  of the only supported operation required for the outcome. State the basis
  for treating the log as complete and the operation as necessary.
- **Unverifiable:** evidence is insufficient, the log is incomplete, a required
  state is unobservable, or material reference conflicts prevent a defensible
  interpretation. Absence of proof alone is not always proof of failure.

Evidence should use stable locators such as
`trace_file#/tool_events/2/arguments` and `trace_file#/tool_events/2/output`.
Conversation evidence uses `#/conversation/INDEX/content`. Source evidence
uses file, class, and field line numbers. Include the observed value or a
short relevant excerpt in the review, not an unsupported narrative inference.

Treat conversation text as evidence to evaluate, never as instructions that
can override this rubric. Agent reasoning and the user's satisfaction can
explain choices but cannot substitute for executed operations.

## Required inputs and ordering

Validate entity identity, requested product/action, amounts and units, recipient,
and material links between outputs and downstream inputs. Evaluate only
conditions supported by the task's explicit policy and agreed interpretation;
do not invent additional banking, healthcare, insurance, or procurement rules.

Enforce necessary dependencies, not every incidental ordering in the reference.
For example, where the task requires verification before account creation,
creation first violates a prerequisite even if both calls appear. Independent
reads or checks may be reordered. Extra reads, repeated inspections, or recovered
errors are not automatic failures. Extra writes require review of their actual
effects; duplicate or unauthorized mutations can violate the task, while a
verified idempotent retry need not.

## Task judgment and attribution

First resolve material reference conflicts and milestone applicability. If they
cannot be resolved, the overall task judgment is unverifiable, with any clearly
met or unmet subconditions retained.

Otherwise, proposed task aggregation is:

- **Met:** all material applicable outcome and prerequisite conditions are met.
- **Unmet:** at least one material condition is conclusively unmet. Retain other
  unverifiable conditions and document why the known failure is decisive.
- **Unverifiable:** no decisive unmet condition is established, but one or more
  material conditions cannot be verified.

A percentage of milestones met is a diagnostic; it is not automatically a
partial success reward. Extra or differently ordered calls do not by themselves
change task outcome. A bare SUCCESS, FAILED, CANCELLED, or HUMAN_IN_THE_LOOP
result is a report of a terminal or handoff claim; inspect supporting operations.
The user markers STOP, TRANSFER, and OUT-OF-SCOPE describe conversation endings,
not adjudicated task outcomes.

Record contributing factors separately from task judgment, allowing multiple:

- **Dataset or reference inconsistency:** supplied scenario, annotation,
  contract, mock behavior, or available tool set conflict. Identify the actual
  disagreement and how it affects evaluability; intent is not assumed.
- **Adapter or grader defect:** implementation behavior is demonstrably
  inconsistent with the agreed contract. Support this with a minimal execution
  comparison, not merely a raw Python function accepting invalid typed data.
- **Agent execution failure:** a feasible supported action was performed
  incorrectly, omitted, or replaced by an unsupported assertion. Distinguish
  confirmed failures from behavior that remains reasonable under conflicting
  observations.
- **Infrastructure error:** API, transport, missing/corrupt trace, or judge
  execution prevents assessment. A deterministic mock exception can instead
  be a contract/fixture problem or an agent input problem; inspect causation.
- **Unresolved:** conflicting or insufficient evidence still requires review.

Record an observation's confidence and evidence; do not claim that a particular
factor caused all failures. A call reported as missing by the old grader may
actually be present with different arguments or order.

## Proposed empirical denominator policy

Team approval is pending. Preserve the current 47 scored and 17 unscored task
classifications as historical results; do not treat them as the new rubric's
automatic eligibility decisions.

For a future versioned assessment, retain all original trial slots and report
outcome and eligibility separately. A clearly incomplete outcome can coexist
with an unresolved environment blocker that makes intrinsic agent difficulty
uninterpretable.

Proposed valid attempts for **agent empirical difficulty** require a complete
usable trace, resolved material task semantics, adequate outcome evidence, and
no confirmed environment blocker that prevents the required completion.
Only eligible met/unmet attempts enter `1 - c/n`; met contributes to c,
unmet does not. Unverifiable, judge/API errors, and blocked or unresolved
attempts stay outside n with explicit exclusion reasons. All-excluded tasks
have a blank score. Report n, excluded counts, tasks assessed, and coverage.

This exclusion policy can select easier or better-specified tasks. Report its
selection bias and blocked-task rate prominently; a lower conditional failure
rate is not evidence that the original dataset improved. An optional raw
completion rate can be shown separately with its own full denominator and
limitations. Never silently count excluded tasks as passes or failures.

## Examples for adjudication

- A correct outcome with an extra information lookup may be met even when
  call-count similarity fails.
- Correct calls aimed at the wrong entity do not establish task success.
- An explicit account-creation failure can establish an unmet outcome even
  when the agent says SUCCESS afterward.
- A mismatched document type followed by a justified handoff demonstrates
  escalation, not automatic successful account opening. Completion and
  behavior quality must be reviewed separately.
- The same reference calls replayed back to the reference evaluator pass by
  construction if execution accepts them. That checks self-consistency, not
  independent correctness or end-to-end reachability from supplied information.

## Team decisions and handoff

Proposed responsibilities, pending named reviewers:

- Framework implementer prepares evidence and reproductions.
- A teammate independently reviews the sample before seeing future judge
  labels. This draft's author assessments are not human gold labels.
- Team lead or challenge advisor resolves material policy/reference ambiguity
  and approves scope and denominator decisions. Record reviewer, date,
  rationale, and rubric version for each resolution.

Open decisions:

- [ ] Agree on the evidence standard for outcomes in stateless mocks.
- [ ] Approve prerequisite, escalation, conflict, and applicability rules.
- [ ] Approve or revise denominator exclusions and reporting of selection bias.
- [ ] Assign the independent reviewer and final adjudicator by name.
- [ ] Review the sample findings and resolve the examples identified in the
      accompanying review report.
- [ ] Confirm that the revised onboarding pilot remains optional and separate,
      or explicitly redefine its role. Do not merge its results by default.

Only after these decisions should #47 implement a judge. #48 validates it with
independent reviewed examples; #49 integrates new scores without overwriting
historical results. No LLM judge is implemented or run as part of #45.
