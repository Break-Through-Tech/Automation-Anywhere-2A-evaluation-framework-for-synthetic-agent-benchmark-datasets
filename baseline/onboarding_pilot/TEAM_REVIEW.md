# Team review before extending outcome grading

The completed pilot has six revised onboarding scenarios and 24 successful
model trials. These results demonstrate the current simulated workflow; they
do not establish performance on the original synthetic tasks or comparability
with tau2. The offline tests below require no model credits.

Record a reviewer, date, and decision for each section. Unchecked items are
open decisions, not evidence of team approval.

## 1. Agree on each scenario's facts

Review all six entries in `cases.json` against their source narratives and
submitted inputs. Read the `provenance` and `authored_assumptions` fields.

- [ ] Confirm the customer, requested account, contact address, and business owners.
- [ ] Confirm required identity and address documents, including every owner's ID.
- [ ] Confirm the authored prior address and supporting evidence for the mismatch case.
- [ ] Accept or revise fixture-backed AML scores and sanctions responses.
- [ ] Accept or revise the assumptions that documents are valid and requested
      follow-up uploads arrive automatically.
- [ ] Decide whether a missing upload, invalid ID, sanctions match, or high risk
      should lead to rejection, manual review, or another explicit outcome.

Reviewer / date / decisions:

## 2. Agree on what earns a pass

Read `policy.md`, `environment.py`, and `grader.py` together.

- [ ] Confirm which checks must precede account creation and which mistakes an
      agent may correct before completing the task.
- [ ] Confirm that an active account, linked CRM, and recorded welcome delivery
      are all required for these six eligible applications.
- [ ] Review the assumption that beneficial owners equal authorized signers;
      change the task contract if those roles should differ.
- [ ] Decide whether checking message type, recipient, channel, delivery state,
      and nonempty text is sufficient, or whether message meaning also matters.
- [ ] Decide whether address explanations need explicit content validation.
      The current confirmation service checks requested, extracted address
      evidence; it does not assess the explanation's meaning.
- [ ] Define rejection/manual-review success separately before adding ineligible
      applications to the scored dataset. The current grader requires an active
      account, so correctly refusing an ineligible application earns no success
      reward under this version.

Reviewer / date / decisions:

## 3. Verify failures and alternative valid paths offline

Run from the repository root:

```bash
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/python -B -m baseline.onboarding_pilot.run --validate-only
.venv/bin/python -B -m baseline.onboarding_pilot.run --regrade
```

The tests replay public tools with altered inputs and separately corrupt saved
states to exercise the grader. They cover sanctions matches, high AML risk,
invalid identity/address documents, wrong identity inputs, missing document
extractions, unresolved addresses, missing/extra business owners, and welcome
delivery errors. Blocked creation and invalid sends must leave persisted records
unchanged. A claimed `SUCCESS` cannot replace a real outcome. Two distinct valid
workflows per scenario must still pass.

These are offline safety and grading tests, not additional model trials.
Transport outages, delivery retries, semantic message assessment, and successful
rejection/manual-review workflows are not implemented by these tests. Delivery
failure grading is checked through a deliberately altered persisted message;
the simulated send service does not currently inject network failures.

- [ ] Review test assertions, especially which specific failed check is expected.
- [ ] Run the commands and record results.
- [ ] Confirm the saved 24 trial rewards reproduce without API calls.

Reviewer / date / verification:

## 4. Extend one category at a time

- [ ] Choose the next synthetic category and assign an owner.
- [ ] Define its starting state, task-specific outcomes, allowed transitions,
      service behavior, and negative cases before implementing tools.
- [ ] Keep task facts separate from grading checks and model prompts.
- [ ] Validate multiple valid paths and realistic failures offline first.
- [ ] Version changed fixtures, policy, tools, and grader; keep new trial outputs
      separate. Preserve this pilot's immutable sources/results when changing
      behavior so existing source-hash verification remains reproducible.
- [ ] Approve the model-trial budget before running another baseline.
- [ ] Repair the 17 invalid original synthetic references separately, or document
      an explicit migration to reviewed, revised tasks. This pilot does not repair them.
- [ ] Regenerate full-framework metrics only after approving the revised dataset
      and grader, documenting evaluation differences from tau2.
- [ ] Share the local implementation and results with teammates through a reviewed
      commit/PR. These files are not published merely by being created locally.

Owner / next category / decisions:
