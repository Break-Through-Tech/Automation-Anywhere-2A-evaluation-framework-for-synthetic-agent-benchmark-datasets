# Original synthetic evaluation review for issue 45

Status: author review draft pending independent team adjudication. No new reward
or difficulty label has been assigned. The proposed rubric is in
`docs/evaluation/synthetic_milestone_rubric.md`.

## Findings from the saved run

All 256 saved trial identities were inspected for termination metadata. Of these,
254 have termination_reason=user_stop: 103 end with TRANSFER, 96 with OUT-OF-SCOPE,
and 55 with STOP in the final user message. The other two end through a workflow
terminal call. These are conversation endings, not independent outcome labels.
No API errors or step-limit terminations occur in the final CSV; retry history
is a separate preserved artifact. This does not establish absence of task or
simulation problems.

The old grader reports 188 reference-failed attempts over 47 tasks and 68
invalid-reference attempts over 17 tasks. Both workflow-terminal attempts
still fail reference grading. At least some old missing_tool messages concern
calls that actually occurred with different arguments or ordering.

## Offline reference sanity check

We replayed all 64 supplied reference call lists verbatim through the existing
adapter and original mocks, without model calls. Exactly the same 17 task IDs
fail as in the saved preflight. There are 39 rejected reference calls: 9 also
raise when invoked directly on the mock, and 30 return without exception when
schema validation is bypassed. These are call counts, not task counts. Direct
Python acceptance of invalid typed inputs is not proof of an adapter defect;
the original tool contract and runner still need to be respected.

The 47 accepted lists pass their own reference evaluator by construction. This
is a self-consistency check, not independent evidence of correct outcomes.
References inject values directly rather than deriving every argument from
preceding outputs, and execution continues after an individual error for the
purpose of collecting diagnostics. A passing replay therefore does not prove
that the task is reachable from information available to the agent.

## Review sample and limits

The sample contains 16 attempts covering 15 tasks and all seven categories.
For each category, select the first invalid-reference attempt by task ID/trial
(or the least tool-active reference-failed attempt if none exists), plus the
most tool-active reference-failed attempt. Break ties by task ID/trial. Add the
two workflow-terminal attempts and deduplicate identities. This purposive
sample emphasizes contrasting failure patterns; it cannot estimate population
error rates or substitute for the independent calibration sample in #48.

`sample.json` records exact paths, trace hashes, source lines, milestone text,
and zero-based event indices. `review_notes.json` records the following draft
observations and review questions. Candidate classifications can overlap and
are not final root-cause assignments. All human reviewer/adjudicator fields
remain pending. The source case, reference list, and selected trace were used
for these observations; Python-to-JSON reconciliation remains work for #46.

## R01 banking_accounts_deposits

Task `DigitalAccountOpeningAgent_W3_TC1`, trial 0.

Reference identity validation supplies business_license, which the mock rejects. The saved attempt performs only a human handoff; owner screening and account opening are not evidenced.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_accounts_deposits/DigitalAccountOpeningAgent_W3_TC1_trial0.json.gz` at tool event indices 0. Source: `data/banking_accounts_deposits/test_cases.py`, class line 1755, milestones line 2062.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Resolve the business-identity contract and what information was accessible. Does a justified handoff count as behavior quality while the opening task remains incomplete?

## R02 banking_accounts_deposits

Task `DigitalAccountOpeningAgent_W2_TC2`, trial 1.

Identity and AML calls return verified/clear and the tier call returns student. The old grader reports calculate_account_tier missing even though it is event 2; the reference age is 22 while the attempt uses 24. The agent escalates because risk_level is not explicit and never opens an account.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_accounts_deposits/DigitalAccountOpeningAgent_W2_TC2_trial1.json.gz` at tool event indices 0, 1, 2, 3, 4. Source: `data/banking_accounts_deposits/test_cases.py`, class line 1455, milestones line 1673.

Candidate factors: grader_limitation, unresolved.

**Decision needed:** Determine the run date/age convention and whether clear AML supports low risk. Do not treat the executed tier call as absent or infer account completion from the user STOP marker.

## R03 banking_customer_onboarding

Task `BankingCustomerOnboardingAgent_BankOnboard_W4_TC2`, trial 0.

The business-document extraction returns unrelated personal identity records and types. The agent escalates that discrepancy. Separate reference schema errors concern null business dates of birth.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_customer_onboarding/BankingCustomerOnboardingAgent_BankOnboard_W4_TC2_trial0.json.gz` at tool event indices 0, 1. Source: `data/banking_customer_onboarding/test_cases.py`, class line 1078, milestones line 1217.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Adjudicate extraction and business identity semantics before judging opening completion. A handoff does not establish account creation.

## R04 banking_customer_onboarding

Task `BankingCustomerOnboardingAgent_BankOnboard_W1_TC1`, trial 0.

The requested utility bill is returned as a passport, including after a repeat extraction. The agent requests manual review and stops before identity verification or account creation.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_customer_onboarding/BankingCustomerOnboardingAgent_BankOnboard_W1_TC1_trial0.json.gz` at tool event indices 0, 1, 2. Source: `data/banking_customer_onboarding/test_cases.py`, class line 414, milestones line 549.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Can any supported action resolve the document mismatch? Evaluate the escalation separately from the requested account outcome.

## R05 banking_fraud_monitoring

Task `BankingFraudMonitoringSupportAgent_W5_TC1`, trial 1.

The sole event is an urgent escalation asserting no account-access blocking tool. The tool set does include auto_decline_transaction, which the reference uses and whose mock returns block_status. Transaction blocking and account-access blocking are not automatically equivalent.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_fraud_monitoring/BankingFraudMonitoringSupportAgent_W5_TC1_trial1.json.gz` at tool event indices 0. Source: `data/banking_fraud_monitoring/test_cases.py`, class line 2058, milestones line 2211.

Candidate factors: candidate_agent_interpretation, unresolved.

**Decision needed:** Determine the intended scope of the blocking milestone and whether the agent should have used the transaction operation. Do not accept the agent claim of a missing tool without checking the contract.

## R06 banking_fraud_monitoring

Task `BankingFraudMonitoringSupportAgent_W2_TC2`, trial 2.

Returned transaction/device details conflict with the takeover scenario and its expected high device risk. The trace contains a risk calculation, an analyst route, and repeated escalations, but no auto_decline_transaction.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_fraud_monitoring/BankingFraudMonitoringSupportAgent_W2_TC2_trial2.json.gz` at tool event indices 1, 4, 7, 9, 11, 12. Source: `data/banking_fraud_monitoring/test_cases.py`, class line 1055, milestones line 1215.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Resolve entity linkage and low-risk mock outputs versus the takeover narrative before assigning task eligibility or attributing the omitted block.

## R07 healthcare_patient_onboarding

Task `HealthcareOnboarding_W5_TC1`, trial 0.

Self-pay reference creation passes insurance=None, rejected by the declared schema. The agent escalates self-pay registration, receives a frozen 2024 appointment slot, and requests help with pricing; no record creation or booking is executed.

Evidence: `results/baseline/v2_synthetic_full/traces/healthcare_patient_onboarding/HealthcareOnboarding_W5_TC1_trial0.json.gz` at tool event indices 0, 1, 2, 3, 4, 5. Source: `data/healthcare_patient_onboarding/test_cases.py`, class line 1621, milestones line 1731.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Review how self-pay is represented and whether required pricing/duplicate-review information is available. Judge dated availability against the recorded run context.

## R08 healthcare_patient_onboarding

Task `HealthcareOnboarding_W7_TC1`, trial 1.

Insurance eligibility is active and history is extracted. The agent requests duplicate-record review and twice receives the same 2024 availability, including after a 2026 date request. It explicitly says the appointment is not booked.

Evidence: `results/baseline/v2_synthetic_full/traces/healthcare_patient_onboarding/HealthcareOnboarding_W7_TC1_trial1.json.gz` at tool event indices 0, 1, 2, 3, 4, 5, 6, 7, 8. Source: `data/healthcare_patient_onboarding/test_cases.py`, class line 1969, milestones line 2125.

Candidate factors: dataset_reference_inconsistency, candidate_agent_interpretation, unresolved.

**Decision needed:** Separate the frozen scheduling response from the agent interpretation of duplicate-review requirements. The STOP marker does not mean a booking was completed.

## R09 healthcare_prior_authorization

Task `HealthcarePA_W1_TC2`, trial 0.

The agent escalates payer/plan formatting without executing the requirements check. Offline reference replay shows that check accepts the supplied IDs; the mock contains no corresponding format rejection. Later reference calls independently fail structured-schema validation.

Evidence: `results/baseline/v2_synthetic_full/traces/healthcare_prior_authorization/HealthcarePA_W1_TC2_trial0.json.gz` at tool event indices 0. Source: `data/healthcare_prior_authorization/test_cases.py`, class line 648, milestones line 769.

Candidate factors: candidate_agent_interpretation, dataset_reference_inconsistency, unresolved.

**Decision needed:** Decide how to interpret documented format examples versus accepted tool inputs. A later invalid reference does not establish that the first check was unavailable.

## R10 healthcare_prior_authorization

Task `HealthcarePA_W1_TC1`, trial 3.

The scenario title says all documentation is present, but the criteria response requires an imaging report and both document-retrieval attempts report it missing. The mock always places imaging report in docs_missing. The user ends OUT-OF-SCOPE.

Evidence: `results/baseline/v2_synthetic_full/traces/healthcare_prior_authorization/HealthcarePA_W1_TC1_trial3.json.gz` at tool event indices 0, 1, 2, 3. Source: `data/healthcare_prior_authorization/test_cases.py`, class line 451, milestones line 578.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Decide whether this environment blocks the intended happy path. The agent must not fabricate the missing document to satisfy the reference.

## R11 insurance_claims_intake

Task `InsuranceClaimsIntakeAndTriageAgent_W2_TC2`, trial 0.

The reference supplies null contact strings rejected by the schema. The saved attempt escalates missing incident information and does not create a claim.

Evidence: `results/baseline/v2_synthetic_full/traces/insurance_claims_intake/InsuranceClaimsIntakeAndTriageAgent_W2_TC2_trial0.json.gz` at tool event indices 0. Source: `data/insurance_claims_intake/test_cases.py`, class line 1182, milestones line 1334.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Review whether required loss details are recoverable from the scenario/tools and whether escalation is the acceptable endpoint for this case.

## R12 insurance_claims_intake

Task `InsuranceClaimsIntakeAndTriageAgent_W5_TC1`, trial 3.

Coverage is confirmed by a tool, while repeated handoffs request legal notification and preservation. No claim-creation or acknowledgment operation is executed; the user ends OUT-OF-SCOPE.

Evidence: `results/baseline/v2_synthetic_full/traces/insurance_claims_intake/InsuranceClaimsIntakeAndTriageAgent_W5_TC1_trial3.json.gz` at tool event indices 0, 1, 2, 3. Source: `data/insurance_claims_intake/test_cases.py`, class line 2043, milestones line 2214.

Candidate factors: unresolved.

**Decision needed:** Establish whether the available tools and supplied information support the legal-notification milestones. Generic human acknowledgements do not prove notification or preservation occurred.

## R13 manufacturing_purchase_to_pay

Task `ManufacturingPurchaseToPayAutomationAgent_P2P_W4_TC1`, trial 0.

Two requisition reads return a 500 total against a 10000 scenario amount. The agent escalates reconciliation. Independently, reference quantity_mismatch is rejected by route_payment_approval.

Evidence: `results/baseline/v2_synthetic_full/traces/manufacturing_purchase_to_pay/ManufacturingPurchaseToPayAutomationAgent_P2P_W4_TC1_trial0.json.gz` at tool event indices 0, 1, 2, 3. Source: `data/manufacturing_purchase_to_pay/test_cases.py`, class line 1420, milestones line 1519.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** Resolve amount/entity consistency and approval status vocabulary. No payment-completion evidence follows from a handoff request.

## R14 manufacturing_purchase_to_pay

Task `ManufacturingPurchaseToPayAutomationAgent_P2P_W2_TC1`, trial 1.

The requisition mock returns a 500 amount against a 22000 scenario. The agent routes the discrepancy for review, checks a supplier contract, and does not create/send a PO. The reference assumes a CFO override; the system tool provides only a generic escalation acknowledgement.

Evidence: `results/baseline/v2_synthetic_full/traces/manufacturing_purchase_to_pay/ManufacturingPurchaseToPayAutomationAgent_P2P_W2_TC1_trial1.json.gz` at tool event indices 0, 1, 2, 3, 4, 5, 6. Source: `data/manufacturing_purchase_to_pay/test_cases.py`, class line 954, milestones line 1067.

Candidate factors: dataset_reference_inconsistency, unresolved.

**Decision needed:** What establishes the override and authoritative amount? An acknowledgement must not count as CFO approval or supplier delivery.

## R15 banking_fraud_monitoring

Task `BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC2`, trial 2.

The original grader reports check_device_intelligence missing, although it is executed at event 3. The returned device/transaction differ from reference IDs. The tool returns risk 15 while the reference expects 25; SUCCESS echoes the agent conclusion with no independent approval state.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_fraud_monitoring/BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC2_trial2.json.gz` at tool event indices 0, 3, 5, 6. Source: `data/banking_fraud_monitoring/test_cases.py`, class line 689, milestones line 806.

Candidate factors: dataset_reference_inconsistency, grader_limitation, unresolved.

**Decision needed:** Determine whether the trace supports the correct alert/entity. Completion of the reference-shaped analysis does not automatically establish correct approval.

## R16 banking_fraud_monitoring

Task `BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC2`, trial 3.

The same task in trial 3 also reaches SUCCESS but performs history after device/database checks. These independent reads need not have the reference total order. Entity and risk-output conflicts remain.

Evidence: `results/baseline/v2_synthetic_full/traces/banking_fraud_monitoring/BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC2_trial3.json.gz` at tool event indices 0, 2, 4, 5, 6. Source: `data/banking_fraud_monitoring/test_cases.py`, class line 689, milestones line 806.

Candidate factors: dataset_reference_inconsistency, grader_limitation, unresolved.

**Decision needed:** Separate harmless read reordering from consequential entity/risk discrepancies. This is not yet a confirmed valid alternative solution.

## Decisions still needed

- Nominate a teammate for independent review and a lead/advisor to adjudicate
  material reference or policy ambiguity. No reviewer has been assigned by
  this analysis.
- Decide how much simulated tool evidence is sufficient to establish each
  outcome in these stateless environments, including generated IDs, mocked
  confirmations, generic handoffs, and frozen dates.
- Approve or revise the rubric's separate completion, behavior, and eligibility
  judgments and denominator policy. Appropriate caution can coexist with an
  incomplete task; an impossible specification should not silently become an
  agent failure.
- Keep the revised onboarding pilot separate by default; ask the lead whether
  it has an optional methodological role. Its 24 passes do not resolve the
  original environments' conflicts.

## Reproduction and preservation

Run `python -m baseline.review_synthetic_rubric` from the repository root. The
script only produces offline diagnostic artifacts under `results/rubric_review/v1/`;
it does not implement the future judge or assign new rewards. Use --output-dir
for a separate regeneration. `input_manifest.json` records source/input hashes,
including every saved trace. The authored review notes and this report are
review documents and are not overwritten by the diagnostic generator.

The supplied data, current baseline artifacts, original grader, framework
outputs, archived runs, and separate pilot results are preserved. Issue #45
should remain open until team review and scope/denominator decisions are
recorded. Implementation and human adjudication are different completion steps.
