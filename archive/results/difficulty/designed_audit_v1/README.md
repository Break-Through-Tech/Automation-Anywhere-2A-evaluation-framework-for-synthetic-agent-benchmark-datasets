# Audit of the provisional designed difficulty index

## Recommendation for Sandra

Keep v0.1 as an exploratory baseline and show the three component counts first.
Do not present its scalar ranking as a validated final difficulty measure.
The code reproduces the intended formula; the main problems are feature coverage
and annotation granularity. Weights alone cannot distinguish tasks with identical
component counts. No baseline scores or supplied data were changed in this audit.

## What looks reasonable

The highest index, 87.96, belongs to a catastrophe batch with three claims and
23 reference business calls, including two emergency dispatches. This explains
its placement as high-volume work; it does not prove hardest reasoning.
The lowest index, 18.64, belongs to duplicate-invoice rejection, a short intended
branch. Approved-authorization status lookup is also near the bottom at 20.89.
These placements are plausible from source scope, not independently established.
The notification obligations in the low-scoring examples may still be bundled
or weakly expressed by their reference tool sequences.

## What needs revision

1. **Limited resolution.** There are 35 distinct three-component profiles across
   64 tasks. 40 tasks belong to 11 repeated-profile groups. Some ties are
   sensible, but others hide meaningful differences. The emergency property and
   complex commercial-interruption examples both score 66.22 from (8,8,3), even
   though commercial interruption requires linked claims and several specialist
   roles. Any weights applied to those same counts will leave them tied.
2. **Source grouping affects scores.** One milestone can bundle multiple actions,
   entities or checks. An action group is not an atomic action, and a check group
   is not an independently resolved decision. Standardize these units before
   adding more decimal places or adjusting weights.
3. **Feature overlap.** Descriptive Spearman associations are 0.78 between action
   groups and calls, 0.68 between action groups and checks, and 0.65 between calls
   and checks. This suggests overlapping signals; it does not prove any feature
   invalid. Tasks share workflows, so these are not independent inferential tests.
4. **Normalization matters.** One extra action group adds 3.70 points, one extra
   reference call adds 1.45, and one extra check group adds 8.33. Equal component
   weights do not mean equal per-item influence. Twenty-three calls is the batch
   maximum, so eight calls contribute only 11.59 of a possible 33.33 points.

## Weight sensitivity with the comparisons kept separate

Moving weights from equal thirds to action-heavy (.50/.25/.25) changes a task's
rank by at most 10 places; 1 task moves at least 10. Tool-heavy
(.25/.50/.25) changes ranks by at most 6 places.

Removing checks entirely (.50/.50/0) is a component-removal experiment, not a
small weight adjustment. It changes a task's rank by as much as 20.5 places;
7 tasks move at least 10. Self-pay onboarding moves from rank 6 to 26.5 in
that experiment, but only to rank 7 under the two ordinary weight variants.
Ranks are average ranks for ties, with 1 easiest and 64 hardest. Rank changes
measure sensitivity, not which ordering is correct.

## What to do next

- Preserve v0.1 and its evidence as the baseline; do not silently overwrite it.
- Make profiles primary in the meeting and the composite index secondary.
- In a new version, define actions at a consistent granularity and separately
  describe required repetitions, linked entities, approvals and coordination.
  Keep these features descriptive until their aggregation is justified.
- Do not tune weights to copy supplied easy/medium/hard tags or the assistant's
  earlier ranking. Neither is independent validation. Do not treat an apparent
  label mismatch as proof that the task, annotation or score is wrong.

Suggested meeting statement: “We have a reproducible 64-task baseline. The audit
shows it measures work volume better than it distinguishes all forms of task
complexity. I recommend leading with the feature profile and refining action
units and coordination before declaring a final single score.”

## Source-backed reviewed examples

### Catastrophe Event – Batch Processing, Emergencies Flagged

Task: `InsuranceClaimsIntakeAndTriageAgent_W3_TC1`. Score 87.96; profile (8,23,3).

Three claims and two emergency dispatches explain the 23 reference business calls. High volume is supported by the intended reference, not proof of hardest reasoning.

Source: `data/insurance_claims_intake/test_cases.py:1408`; `data/insurance_claims_intake/test_cases.json` at `#/workflows/2/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Address Mismatch: Customer Provides Explanation and Valid New Document

Task: `BankingCustomerOnboardingAgent_BankOnboard_W7_TC1`. Score 76.01; profile (8,9,4).

Address mismatch recovery includes two extraction and two communication calls. Four evaluative milestone groups contribute a full 33.33 points; their independence is not established.

Source: `data/banking_customer_onboarding/test_cases.py:1513`; `data/banking_customer_onboarding/test_cases.json` at `#/workflows/3/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Standard Checking Account - Individual, Small Deposit, Micro-Deposit Funding

Task: `DigitalAccountOpeningAgent_W1_TC2`. Score 74.56; profile (8,8,4).

Identity, AML, tier and funding verification give four check groups. Six account tasks share (8,8,4), including a multi-owner business task; depth and entity multiplicity are not resolved.

Source: `data/banking_accounts_deposits/test_cases.py:878`; `data/banking_accounts_deposits/test_cases.json` at `#/workflows/0/test_cases/1`. Exact milestone excerpts and pointers are in audit.json.

### Emergency Property Claim – Water Intrusion, Storm Peril, Coverage Confirmed

Task: `InsuranceClaimsIntakeAndTriageAgent_W1_TC1`. Score 66.22; profile (8,8,3).

Emergency property intake has profile (8,8,3). It ties the commercial-interruption task despite different required entities and specialist coordination.

Source: `data/insurance_claims_intake/test_cases.py:451`; `data/insurance_claims_intake/test_cases.json` at `#/workflows/0/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Complex Commercial Property Claim – Business Interruption, Large Loss

Task: `InsuranceClaimsIntakeAndTriageAgent_W8_TC1`. Score 66.22; profile (8,8,3).

The milestones require property and business-interruption coverage, linked claims, large-loss and BI specialists, and accountant/engineer dispatch. Grouped counts collapse those requirements to the same (8,8,3) profile as ordinary emergency property intake.

Source: `data/insurance_claims_intake/test_cases.py:2632`; `data/insurance_claims_intake/test_cases.json` at `#/workflows/7/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Partial receipt, quantity mismatch, backorder received and payments processed

Task: `ManufacturingPurchaseToPayAutomationAgent_P2P_W4_TC1`. Score 36.35; profile (6,4,1).

Partial receipt and a backorder lead to partial and final payments. Rank moves from 8 to 18 with action-heavy weights; the four-call reference includes two payment calls. This supports a dependency/repetition feature discussion, not a proven correct rank.

Source: `data/manufacturing_purchase_to_pay/test_cases.py:1420`; `data/manufacturing_purchase_to_pay/test_cases.json` at `#/workflows/3/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Self-pay patient onboarding with initial visit

Task: `HealthcareOnboarding_W5_TC1`. Score 30.92; profile (6,6,0).

Six active groups and six reference calls, but no annotated check group. Rank moves from 6 to 26.5 only when checks are removed; ordinary weight changes move it from 6 to 7. Zero annotated checks is not proof of zero reasoning.

Source: `data/healthcare_patient_onboarding/test_cases.py:1621`; `data/healthcare_patient_onboarding/test_cases.json` at `#/workflows/4/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Status Check for Approved PA

Task: `HealthcarePA_W8_TC1`. Score 20.89; profile (3,1,1).

The approved status path has three milestones and one lookup call, not all five shared workflow steps. Missing reference_id is a separate feasibility concern and is not a complexity penalty.

Source: `data/healthcare_prior_authorization/test_cases.py:1886`; `data/healthcare_prior_authorization/test_cases.json` at `#/workflows/7/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

### Duplicate invoice detected and rejected, supplier notified

Task: `ManufacturingPurchaseToPayAutomationAgent_P2P_W5_TC1`. Score 18.64; profile (2,2,1).

A short duplicate-invoice branch has two active milestone groups and two business calls. Rejection is the intended endpoint. Notification is bundled into a milestone and terminal result; a short reference does not establish that notification is fully implemented.

Source: `data/manufacturing_purchase_to_pay/test_cases.py:1619`; `data/manufacturing_purchase_to_pay/test_cases.json` at `#/workflows/4/test_cases/0`. Exact milestone excerpts and pointers are in audit.json.

## Checks and reproducibility

The audit verifies the saved artifact against a fresh offline build, including
source hashes. All statistics come from the original 64 records; supplied tags
are comparison context only. Source inspection is the assistant's interpretation,
not a human review, task rerun, completion judgment or independent validation.
Top-band selection retains ties at the fifth-place boundary rather than picking
an arbitrary five tasks. Original scores and outcome judgments remain unchanged.

    python -m difficulty.audit_designed_difficulty --out results/difficulty/designed_audit_fresh
