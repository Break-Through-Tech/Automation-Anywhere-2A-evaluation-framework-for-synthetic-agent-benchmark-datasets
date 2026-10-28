# Outcome-grading pilot: banking customer onboarding

This isolated pilot covers the six banking customer-onboarding scenarios using
new stateful services and explicit business-outcome checks. It is inspired by
tau2's environment-state evaluation, but **does not invoke tau2's grader**.

## Scope and versioning

- Dataset: `onboarding_state_pilot_v1`.
- Grader: `onboarding_business_outcomes_v1`.
- Baseline: the existing v2 model, ReAct instruction template, agent/user
  decoding settings, seed 42, four trials per task, 200 steps, concurrency four.
- Output: `results/pilots/onboarding_state_v1/`.
- Trial IDs have a versioned prefix so they cannot silently be included in
  the original synthetic benchmark by `run_all.py`.

The original synthetic fixtures contain hard-coded responses that conflict
with their scenarios. `cases.json` defines **revised, controlled fixtures**
using the source narratives, submitted inputs, and declared customer/document
facts. It records explicit authored assumptions. It does not contain a required
tool sequence. The original files and all previous results remain unchanged.
These are new pilot results, not replacements for the original 64-task scores.

## What the environment does

Tools persist customer, account, CRM, and communication records. Identity,
sanctions, AML, document verification, and address-confirmation evidence must
exist before an account can be created. The created account records that
evidence, preventing checks performed afterward from satisfying the rule.

`get_application` exposes already-submitted application facts through an
authenticated simulated portal. Missing-document requests do not require a
customer ID before a customer exists. Follow-up uploads are deterministic
simulated customer events after a request. Address mismatches require the
supplied explanation and extracted supporting evidence. Generated IDs are
deterministic service IDs; they do not copy the original expected IDs.

AML outcomes are fixture-backed simulations, not a real-world scoring model.
The scenario facts and eligibility rules require team review before broader use.

## What the grader checks

The grader reads only the fixture's business contract and persisted database
state. It does not read the model's `SUCCESS` claim or reference tool calls.
It checks the correct customer/application, active account type and owners,
compliance evidence at creation, verified documents and address, linked CRM,
and an actually recorded welcome delivery to the intended channel/recipient.

Different valid check orders, batching, extra reads, idempotent retries, and
paraphrased messages can pass. The bank services prevent invalid transitions;
blocked mistakes may be corrected without automatically failing an otherwise
correct final outcome. Message meaning is not LLM-judged: the grader checks
message type, send state, recipient/channel, and nonempty content.

`validation.py` exercises two distinct known-valid workflows for each scenario.
Unit tests also corrupt otherwise-correct states, try forged success, omit an
owner's verification, and attempt unsafe creation. Validation plans and grading
rules are not provided to the agent/user models. The agent sees the public
policy and tool schemas; the user sees the narrative and submitted input.

## Commands

Use [TEAM_REVIEW.md](TEAM_REVIEW.md) to review fixture assumptions, grading rules,
offline failure coverage, and decisions needed before extending this pilot.

```bash
# No model calls: validate 12 different known-valid workflows.
.venv/bin/python -m baseline.onboarding_pilot.run --validate-only

# First two of the 24 planned trial slots.
.venv/bin/python -m baseline.onboarding_pilot.run --limit-trials 2

# Continue remaining slots without rerunning saved trials.
.venv/bin/python -m baseline.onboarding_pilot.run --resume

# Verify saved rewards against final states without model calls.
.venv/bin/python -m baseline.onboarding_pilot.run --regrade

.venv/bin/python -m unittest discover -s tests -v
```

The first live command makes API calls using the existing configured
credentials. Output includes full compressed traces and final database states,
per-trial pass/fail checks, per-task empirical difficulty, input/source hashes,
configuration and package versions, and the offline validation evidence.
Resume/regrade refuse changed sources or configuration.

The pilot demonstrates outcome-grading mechanics. A full fair comparison still
needs reviewed task contracts, additional negative/edge cases, and consistent
evaluation goals across datasets. It does not by itself establish that scores
from this revised environment are directly comparable with the old tau2 run.
