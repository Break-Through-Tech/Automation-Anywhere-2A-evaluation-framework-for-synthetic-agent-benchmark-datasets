# Six examples for reviewing designed difficulty

## Start here

We are checking whether our features describe the work each task requires. No new agent runs or grading are needed. These are assistant proposals for review, not approved task counts or human judgments.

Read A and B first to see unused workflow branches. Compare E and F next to see complexity that identical counts can miss. C shows retries; D shows bundled work and conditions outside step descriptions.

**Recommendation:** use task-specific necessary actions and business choices as the candidate features. Keep supplied tags as a comparison. Record data quality separately. Do not assign a final weighted score before agreeing the units and independently checking the features.

## What the numbers mean

Applicable description count selects YAML descriptions for the intended scenario, retaining input receipt, waiting and terminal descriptions for a like-for-like comparison. It is not an exact action count or final scoring feature. Decisions remain unconfirmed.

Business calls exclude SUCCESS, FAILED, CANCELLED and HUMAN_IN_THE_LOOP. Repeated calls count again; distinct tools do not. Wording hits count matching step descriptions only, not actual decisions. The six cases span five domains and two tasks from each supplied tag. This is a deliberately chosen development sample.

## A Check an approved authorization

Task `HealthcarePA_W8_TC1` · supplied tag **easy**

**Required work:** Look up the authorization status, identify the approved result, and notify the provider. The approved scenario does not require an appeal or delayed-request follow-up.

**Code counted:** 5 shared steps; 1 business calls; 1 distinct tools; 3 milestones; 0 wording hits.

**Proposed applicable descriptions:** 3 (workflow steps 1, 2, 3). Exact action and decision counts remain unconfirmed.

**Comparison:** The code counts all five workflow descriptions. For this approved scenario, steps 4 and 5 describe other outcomes. Three descriptions appear applicable; provider notification and EHR update are bundled into step 3 and are not established by the single expected lookup call.

**Choices to inspect:** Categorizing the returned status is a choice even though the wording rule flags zero descriptions. Whether this counts as a decision when approval is fixed in the scenario needs an agreed rule.

**Separate data or scope note:** The scenario input omits reference_id, although the intended lookup assumes one. Record this separately as a data feasibility issue; do not inflate designed complexity.

**Ask Sandra:** Count the approved path as three described steps? Is categorization a decision, and how should bundled notification and EHR work be represented?

Sources: `data/healthcare_prior_authorization/test_cases.py:1886`; `data/healthcare_prior_authorization/agent_definition.yaml:528` (#/agent/workflows/7); `data/healthcare_prior_authorization/test_cases.json` (/workflows/7/test_cases/0).

## B Resolve an invoice mismatch

Task `ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1` · supplied tag **medium**

**Required work:** Receive the invoice, match it to the order and receipt, identify the excessive price variance, obtain accounts payable approval, process payment, and signal completion.

**Code counted:** 7 shared steps; 3 business calls; 3 distinct tools; 4 milestones; 2 wording hits.

**Proposed applicable descriptions:** 6 (workflow steps 1, 2, 3, 4, 6, 7). Exact action and decision counts remain unconfirmed.

**Comparison:** Seven shared descriptions include escalation if accounts payable cannot resolve the mismatch. This scenario explicitly resolves it, so step 5 is an alternative. Six descriptions appear applicable, including receiving the invoice and signaling completion; the reference contains only three business-tool calls.

**Choices to inspect:** Inspect the variance threshold and whether accounts payable resolves the exception. The two flagged descriptions are review leads, not a verified count. Decide whether the threshold is a workflow-entry condition or an in-task choice.

**Separate data or scope note:** Do not treat human approval as an agent tool call or ignore the approval dependency simply because the reference has only three business calls.

**Ask Sandra:** Exclude the unused escalation step? Should receiving an already supplied invoice and signaling completion contribute to complexity?

Sources: `data/manufacturing_purchase_to_pay/test_cases.py:1196`; `data/manufacturing_purchase_to_pay/agent_definition.yaml:397` (#/agent/workflows/2); `data/manufacturing_purchase_to_pay/test_cases.json` (/workflows/2/test_cases/0).

## C Recover from inactive insurance

Task `HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1` · supplied tag **medium**

**Required work:** Extract patient and insurance information, check coverage, request an update after inactive coverage, receive the response, recheck coverage, create the patient record, schedule the visit, and send confirmation.

**Code counted:** 7 shared steps; 8 business calls; 6 distinct tools; 7 milestones; 3 wording hits.

**Proposed applicable descriptions:** 7 (workflow steps 1, 2, 3, 4, 5, 6, 7). Exact action and decision counts remain unconfirmed.

**Comparison:** All seven workflow descriptions appear relevant, but they bundle different amounts of work. Step 1 has two extraction tools; step 6 has record creation, scheduling, and communication. Eight expected business-tool interactions use six distinct tools because verification and communication each repeat.

**Choices to inspect:** Inspect the initial coverage result, updated insurance versus self-pay, and the recheck result. The three wording hits include a final success/escalation description that may repeat an earlier choice. Do not equate three hits with three independent decisions.

**Separate data or scope note:** The intended reference includes updated insurance. Whether the runtime supplies it properly is a separate environment question, not an extra designed step.

**Ask Sandra:** Count retries separately from distinct tools? Does waiting for the response contribute to difficulty, and how should bundled work be split?

Sources: `data/healthcare_patient_onboarding/test_cases.py:1107`; `data/healthcare_patient_onboarding/agent_definition.yaml:387` (#/agent/workflows/2); `data/healthcare_patient_onboarding/test_cases.json` (/workflows/2/test_cases/0).

## D Escalate a high risk transaction

Task `BankingFraudMonitoringSupportAgent_BankingFraud_W3_TC1` · supplied tag **hard**

**Required work:** Gather transaction, customer, and history information; inspect device and fraud data; calculate risk and compile an investigation package; route it to an analyst; confirm escalation.

**Code counted:** 5 shared steps; 7 business calls; 7 distinct tools; 4 milestones; 1 wording hits.

**Proposed applicable descriptions:** 5 (workflow steps 1, 2, 3, 4, 5). Exact action and decision counts remain unconfirmed.

**Comparison:** All five descriptions appear relevant. The first contains three business-tool calls and the second two, giving seven business calls overall. A five-step workflow is therefore not necessarily less work than a longer workflow with fewer tools.

**Choices to inspect:** The risk threshold 70 < score <= 95 is in trigger_conditions, which the current wording rule does not scan. Package completeness appears in exit conditions. Separate business routing choices from generic tool-failure handling.

**Separate data or scope note:** The supplied hard tag is a comparison annotation. Neither the tag nor seven calls independently proves this task is hard.

**Ask Sandra:** Include workflow trigger conditions in the decision feature? Does the agent select the route or merely execute an already selected escalation workflow?

Sources: `data/banking_fraud_monitoring/test_cases.py:1262`; `data/banking_fraud_monitoring/agent_definition.yaml:351` (#/agent/workflows/2); `data/banking_fraud_monitoring/test_cases.json` (/workflows/2/test_cases/0).

## E Handle an emergency property claim

Task `InsuranceClaimsIntakeAndTriageAgent_W1_TC1` · supplied tag **easy**

**Required work:** Extract loss details, classify the claim, verify coverage, assess severity, create the claim, dispatch emergency mitigation, assign a team, acknowledge the customer, and signal completion.

**Code counted:** 9 shared steps; 8 business calls; 8 distinct tools; 8 milestones; 0 wording hits.

**Proposed applicable descriptions:** 9 (workflow steps 1, 2, 3, 4, 5, 6, 7, 8, 9). Exact action and decision counts remain unconfirmed.

**Comparison:** All nine descriptions appear relevant to the intended reference. The code finds eight business calls, eight distinct tools, eight milestones, and zero wording hits. Those counts are identical to example F even though the supplied tags differ.

**Choices to inspect:** Coverage, emergency severity, and team assignment are potential business choices. They are written as actions rather than using the wording detector keywords. The workflow may already fix some choices; do not invent an exact count.

**Separate data or scope note:** The input has catastrophe_event=false but the reference assigns the CAT team. Flag this source tension for review without deciding that the whole task is invalid.

**Ask Sandra:** How much difficulty comes from selecting a route versus following the scenario route? What evidence would justify distinguishing this task from F?

Sources: `data/insurance_claims_intake/test_cases.py:451`; `data/insurance_claims_intake/agent_definition.yaml:313` (#/agent/workflows/0); `data/insurance_claims_intake/test_cases.json` (/workflows/0/test_cases/0).

## F Handle a commercial interruption claim

Task `InsuranceClaimsIntakeAndTriageAgent_W8_TC1` · supplied tag **hard**

**Required work:** Extract and classify the loss, validate property and business interruption coverage, assess severity, create linked claims, involve the large loss team and specialist, dispatch experts, acknowledge the insured, and signal completion.

**Code counted:** 9 shared steps; 8 business calls; 8 distinct tools; 8 milestones; 0 wording hits.

**Proposed applicable descriptions:** 9 (workflow steps 1, 2, 3, 4, 5, 6, 7, 8, 9). Exact action and decision counts remain unconfirmed.

**Comparison:** The same nine descriptions and eight business calls as E conceal richer outputs: two linked claims, property and business interruption coverage, and several specialists. This is a candidate source of complexity that raw step and tool counts miss.

**Choices to inspect:** Coverage scope, large loss routing, and specialist involvement deserve inspection. Zero wording hits does not establish zero choices. Multiple output entities and coordination could be separate features if defined consistently.

**Separate data or scope note:** The source reference expects linked claims and multiple specialists through a small set of tools. Do not assume one tool call represents one elementary action.

**Ask Sandra:** Should linked entities and coordination be added as a feature? Can reviewers justify a higher difficulty than E from the requirements without seeing the tags?

Sources: `data/insurance_claims_intake/test_cases.py:2632`; `data/insurance_claims_intake/agent_definition.yaml:564` (#/agent/workflows/7); `data/insurance_claims_intake/test_cases.json` (/workflows/7/test_cases/0).

## How to validate the measure

- Agree units for necessary actions and business decisions; separate generic failure handling and data quality.

- Have independent reviewers rank A-F with ties allowed using the requirements, without tags or assistant recommendations. Capture reasons and disagreements.

- Freeze candidate features and score rule, then evaluate on additional held-out tasks. Six selected cases only support initial content review.

- If a scalar is required, agree normalization and weights before inspecting validation rankings. Compare feature-only baselines and a simple equal-weight candidate on the same held-out set. Report uncertainty and limitations; do not tune weights to these six tags.


## Independent review form

For a less biased first ranking, read the requirements in review.json or the supplied sources without looking at supplied_tag, computed counts, or these comparisons. A separate reviewer should do this independently of the assistant.

Reviewer: ______ Date: ______

Rank easiest to hardest using A-F; allow ties: ______

For each task, record necessary actions, business decisions, uncertain requirements, and why it is easier or harder than another task. Keep missing inputs and broken mocks in separate notes. Leave a count unknown when it cannot be established.

Sandra decisions: Count terminal signals? Count passive waiting? Split bundled actions? Count preselected branches? Add retries, linked entities or coordination? Profile or one score?
