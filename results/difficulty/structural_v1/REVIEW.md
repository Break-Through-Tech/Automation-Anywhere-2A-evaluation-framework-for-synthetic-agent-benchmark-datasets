# Completed structural feature review

The seven examples below were reviewed with AI assistance at the user’s request. The pending human-review step is waived for this structural feature document. This is a source and counting-rule spot check, not independent human validation or approval of a difficulty score.

The copied tags and literal counts are confirmed for these seven examples. Exact task-path step counts and true decision-point counts remain unknown because the extraction does not establish them. The supplied dataset and the separate human judge-review forms are unchanged.

## Review 1 banking accounts deposits

Standard Checking Account - Individual, Small Deposit, Micro-Deposit Funding

Task ID: `DigitalAccountOpeningAgent_W1_TC2`.

Confirmed supplied tag: **easy**. Workflow: **W1**. YAML steps: **8**. Expected domain calls: **8**. Expected control calls: **1**. Decision-wording cue steps: **2**.

The easy tag, eight YAML steps, eight reference domain calls, and one SUCCESS control call match the sources. The two cue matches are based on in steps 3 and 5. Tier/risk-dependent limits in step 4, instant versus micro-deposit verification in step 7, and conditional exit rules illustrate why two wording matches are not an exact decision count.

Sources: `data/banking_accounts_deposits/test_cases.py` at class line 878; `data/banking_accounts_deposits/agent_definition.yaml` at workflow W1; `data/banking_accounts_deposits/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## Review 2 banking customer onboarding

Low-Risk Personal Account: Standard KYC, Driver License

Task ID: `BankingCustomerOnboardingAgent_BankOnboard_W1_TC1`.

Confirmed supplied tag: **easy**. Workflow: **W1**. YAML steps: **8**. Expected domain calls: **7**. Expected control calls: **1**. Decision-wording cue steps: **0**.

The easy tag, eight YAML steps, seven reference domain calls, and one SUCCESS control call match the sources. The eighth workflow step signals completion. Zero cue matches does not mean no decisions: risk assessment and failure handling still exist, and the heuristic does not inspect exit conditions.

Sources: `data/banking_customer_onboarding/test_cases.py` at class line 414; `data/banking_customer_onboarding/agent_definition.yaml` at workflow W1; `data/banking_customer_onboarding/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## Review 3 banking fraud monitoring

Low-Risk Card Present Transaction with Typical Device

Task ID: `BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC1`.

Confirmed supplied tag: **easy**. Workflow: **W1**. YAML steps: **5**. Expected domain calls: **5**. Expected control calls: **1**. Decision-wording cue steps: **1**.

The easy tag and literal counts match the sources. Step 2 lists two domain tools, so five workflow steps need not equal five domain tool calls. Auto-approve in step 5 produces an approve wording match, but that step describes a chosen action rather than proving a runtime branch. Conditional escalation rules are outside the cue-count scope.

Sources: `data/banking_fraud_monitoring/test_cases.py` at class line 520; `data/banking_fraud_monitoring/agent_definition.yaml` at workflow W1; `data/banking_fraud_monitoring/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## Review 4 healthcare patient onboarding

High-risk patient with >2 chronic conditions and >5 medications

Task ID: `HealthcareOnboarding_W7_TC1`.

Confirmed supplied tag: **easy**. Workflow: **W7**. YAML steps: **9**. Expected domain calls: **8**. Expected control calls: **1**. Decision-wording cue steps: **0**.

The easy tag and literal counts match the sources; easy is a supplied label, not a conclusion about the high-risk scenario. The reference includes extract_insurance_info, which is absent from W7 tool lists. Preserve this discrepancy for interpretation. Manual versus system coordinator assignment and exit rules may contain decisions not captured by the wording heuristic.

Sources: `data/healthcare_patient_onboarding/test_cases.py` at class line 1969; `data/healthcare_patient_onboarding/agent_definition.yaml` at workflow W7; `data/healthcare_patient_onboarding/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## Review 5 healthcare prior authorization

Standard MRI PA - All Documentation Present, Criteria Met

Task ID: `HealthcarePA_W1_TC1`.

Confirmed supplied tag: **easy**. Workflow: **W1**. YAML steps: **7**. Expected domain calls: **7**. Expected control calls: **1**. Decision-wording cue steps: **2**.

The easy tag and literal counts match the sources. The cue heuristic flags if in steps 1 and 4. These indicate checks of PA requirement and clinical criteria, but seven workflow steps are not a verified path length for every result. Documentation and submission alternatives, along with exit rules, require separate interpretation.

Sources: `data/healthcare_prior_authorization/test_cases.py` at class line 451; `data/healthcare_prior_authorization/agent_definition.yaml` at workflow W1; `data/healthcare_prior_authorization/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## Review 6 insurance claims intake

Denied Claim – Policy Lapsed, Coverage Not Confirmed

Task ID: `ClaimsAgent_W6_TC1`.

Confirmed supplied tag: **easy**. Workflow: **W6**. YAML steps: **7**. Expected domain calls: **6**. Expected control calls: **1**. Decision-wording cue steps: **0**.

The easy tag and literal counts match the sources. This workflow completes by recording a denied claim and notifying the customer. A denial can be the intended task outcome; it is not automatically an agent failure. No listed decision wording cue in the steps does not rule out coverage checks or conditional escalation.

Sources: `data/insurance_claims_intake/test_cases.py` at class line 2294; `data/insurance_claims_intake/agent_definition.yaml` at workflow W6; `data/insurance_claims_intake/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## Review 7 manufacturing purchase to pay

Standard requisition, preferred supplier, exact invoice match

Task ID: `ManufacturingPurchaseToPayAutomationAgent_P2P_W1_TC1`.

Confirmed supplied tag: **easy**. Workflow: **W1**. YAML steps: **10**. Expected domain calls: **8**. Expected control calls: **1**. Decision-wording cue steps: **1**.

The easy tag and literal counts match the sources. Ten YAML steps and eight reference domain tool calls are different measures. The workflow includes receipt handling and an explicit completion step; the shorter reference list is not proof that those workflow steps are unnecessary. Approval wording is a cue, not a verified count of branches or approvals executed.

Sources: `data/manufacturing_purchase_to_pay/test_cases.py` at class line 483; `data/manufacturing_purchase_to_pay/agent_definition.yaml` at workflow W1; `data/manufacturing_purchase_to_pay/test_cases.json` for milestones.

Reviewer: AI-assisted review requested by user. Status: completed source spot check.

- [x] Supplied tag and literal counts checked.
- [x] Workflow counts distinguished from task-specific path counts.
- [x] Wording cues reviewed with limitations recorded.

Exact task-path steps: **unknown**. Exact decision points: **unknown**.

## How to use these results

Keep tags, workflow steps, reference tool calls, and wording cues as separate proposed features. Do not use the cue count as an exact branch count or combine the features into a difficulty score without a justified method. The seven checks do not certify all 64 task scenarios. Further human review is optional for this document; independent human labels remain necessary for the separate judge-agreement study.
