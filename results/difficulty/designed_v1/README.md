# Provisional designed difficulty for all 64 synthetic tasks

All 64 tasks across 7 domains have a reproducible
0–100 complexity index and source-backed component counts. Higher means more
complex under this baseline. This is not a probability, success rate, validated
measurement or a comparison scale with tau2-bench. No agent or API runs were used.

## Start here

Open scores.csv for the 64 results. Read the three component counts before the
combined score. scores.json contains every source excerpt, annotation and flag.
The supplied easy/medium/hard labels are comparison columns, never score inputs.

Formula: score = 100 / 3 × (active task milestone groups / 9 + expected business
tool interactions / 23 + business-check groups / 4). Scales are frozen to this
64-task snapshot. Equal weights are provisional. Changing the task set or counting
rules requires a new version, not silently fitting new scales.

An action group is one active task milestone, excluding terminal signals, passive
responses/approvals and waiting. A milestone may bundle multiple operations, so
this is not an exact atomic action count. A business-check group is an explicitly
annotated evaluative milestone, not a verified independent decision or branch.
Calls come from the intended reference, not observed execution; repeated calls
count again and system signals are excluded. No extra penalty is added for bad
references, missing inputs or environmental defects. A score does not certify
that a task is runnable or that its reference is correct.

Highest three under this method:
- InsuranceClaimsIntakeAndTriageAgent_W3_TC1: 87.96
- BankingCustomerOnboardingAgent_BankOnboard_W7_TC1: 76.01
- DigitalAccountOpeningAgent_W1_TC2: 74.56

Lowest three under this method:
- ManufacturingPurchaseToPayAutomationAgent_P2P_W5_TC1: 18.64
- HealthcarePA_W8_TC1: 20.89
- ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1: 23.79

## Limits and next use

The method can tie tasks with different semantic complexity, including the easy
and hard insurance examples with identical component counts. The features overlap;
more tool calls may also mean more actions or checks. weight_sensitivity.csv shows
alternative weights, not validation. The largest rank shift is
20.5 places across the tested alternatives.
Do not tune weights just to reproduce supplied labels or the assistant's six-task
ranking. Those are not independent validation targets. Exact atomic actions and
independent decisions remain unknown. All annotations are assistant interpretations.

The usable first version is complete; approval and independent validation are not
claimed. Review feature definitions with Sandra before describing scores as final.

Reproduce into a fresh directory:

    python -m difficulty.designed_difficulty --out results/difficulty/designed_fresh

Method: docs/evaluation/designed_difficulty_v0.1.md
Annotations: difficulty/designed_annotations_v1.json
