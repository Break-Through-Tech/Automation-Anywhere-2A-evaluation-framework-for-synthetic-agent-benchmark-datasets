# Original-task readiness inspection

Three original tasks were inspected offline: one banking, one healthcare and
one manufacturing task from the source audit's unflagged group. Their first
saved trials were selected before inspecting outcomes. None is ready for a
clean completion canary without further clarification. This is a readiness
finding, not three new failure labels or a benchmark-wide conclusion.

No API requests, new tool executions, dataset edits, historical score changes,
or human-review changes were made. Trial 0 was reviewed in depth for each task;
the other nine saved trials were inventoried, not independently adjudicated.

## Banking: standard personal onboarding

Task: `BankingCustomerOnboardingAgent_BankOnboard_W1_TC1`, trial 0.

The customer supplies `driver_license.pdf` and `utility_bill.jpg`. Two extraction
attempts label the latter as a passport. The source explains why: any filename
without `license` is classified as a passport. It also returns Sarah Chen while
the expected identity-validation inputs describe Alice Smith. The agent pauses
and requests human review.

The account-creation, CRM and communication tools have useful simulated result
fields, but they were not reached. Establish which applicant identity and document
interpretation are authoritative before judging full completion. The conflicting
classification is established; whether an extracted passport address can satisfy
this task's address requirement remains unresolved. Do not assume every possible
route is impossible or count the pause automatically as agent failure.

## Healthcare: annual physical without preferred dates

Task: `HealthcareOnboarding_W1_TC2`, trial 0.

The agent obtains demographics, insurance, active eligibility and medical history.
The YAML policy calls for duplicate detection, but the exposed tools provide no
patient-search operation. Human escalation returns only an acknowledgement. The
availability tool returns a fixed `2024-02-12` slot, which the agent calls past.
The historical scenario clock is not established by this inspection; today's date
and the agent's assertion alone cannot establish that the slot was invalid.

EHR creation and scheduling have meaningful simulated endpoints. Clarify how the
duplicate check should be fulfilled and how scenario time works before selecting
this attempt for paid validation. Tool-returned patient data also differs from
expected-call literals; those differences must not become automatic failures.

## Manufacturing: early payment discount

Task: `ManufacturingPurchaseToPayAutomationAgent_P2P_W6_TC1`, trial 0.

The matching tool requires an existing purchase-order ID. The customer cannot
supply it, the requisition lookup returns no PO ID, and the tool inventory has
no lookup operation for the existing order. The expected call assumes
`PO-100001`, but this is evaluator reference data, not information supplied to
the agent. The requisition also returns amount `500.0` while the scenario gives
`7000.0`; the discrepancy needs reconciliation.

A tool for creating a new PO exists. Creating a fresh order does not establish
the existing order associated with this invoice and must not be assumed to be
an authorized workaround. The agent escalates the missing-reference problem.
Approval and payment tools offer meaningful simulated results if prerequisites
are established. Resolve how the existing PO should be obtainable first.

## Recommended next action

Keep these three cases as evidence for source-owner clarification. Continue
source inspection of other original tasks if a clean completion canary is
needed before those questions are resolved. Do not repair the supplied fixtures,
expose private expected IDs to the agent, or relax mandatory prerequisites just
to obtain varied labels. A revised environment would be a separate experiment.

The next paid selection is deliberately empty. No difficulty was computed.
The three successful authored controls in `results/judge_review/v6/` establish
basic rule discrimination only; they do not resolve these original-task gaps.

## Saved evidence and checks

- `inspection.json`: findings, exact transcript evidence pointers, source method
  locations, trace/source hashes, and the nine other-trial inventories.
- `context_packets.json`: original task/trace, reconstructed agent instructions
  and schemas, and separately marked evaluator-only implementation references.
  Reconstructed schemas are not a claim that historical schema bytes were archived.
- `next_canary_selection.json`: no candidates selected and no automatic expansion.

All cited execution excerpts were checked against their transcript locations.
All 13 observed tool inputs in the three deeply reviewed attempts passed the
current reconstructed input schemas. This checks schema compatibility, not
semantic correctness or successful task completion. Input and human-review
hashes were verified unchanged. These are assistant inspections, not new
independent human gold labels.
