# Independent review of six designed tasks

Read this sheet before the count comparison. Judge the work the task requires, assuming its intended environment works. Record missing information or contradictions separately. Supplied difficulty tags and code counts are omitted to reduce bias.

Reviewer: ______  Date: ______

Rank A through F from easiest to hardest. Ties are allowed. Give a reason and record your confidence. This review has no approved correct ranking.

## A Check an approved authorization

Status Check for Approved PA

### Scenario conditions

- pa_status_check = true

- reference_id corresponds to approved PA

### Intended work and result

- PA status tracked for reference ID

- Results categorized as approved

- Provider notified of approval

Intended final state: approved.

Required actions in your own words: ______

Business choices and why they are distinct: ______

More or less complex than another example and why: ______

Uncertain requirements or data issues: ______

## B Resolve an invoice mismatch

Invoice price mismatch > $500, AP resolves and payment processed

### Scenario conditions

- invoice_match_status: price_mismatch

- variance_amount: 800

- AP review: resolved

### Intended work and result

- Invoice matched to PO and receipt (price mismatch > $500)

- Exception routed to AP for review

- Payment processed after AP approval

- Workflow completion signaled

Intended final state: completed.

Required actions in your own words: ______

Business choices and why they are distinct: ______

More or less complex than another example and why: ______

Uncertain requirements or data issues: ______

## C Recover from inactive insurance

Patient provides updated insurance after initial inactive coverage

### Scenario conditions

- Initial insurance eligibility inactive

- Patient responds with updated insurance

- New insurance eligibility active

### Intended work and result

- Extract patient demographics and insurance info

- Attempt insurance eligibility verification (inactive)

- Send request for updated insurance or self-pay

- Patient responds with updated insurance

- Re-attempt insurance verification (active)

- Create EHR record, schedule appointment, send confirmation

- Signal success

Intended final state: success.

Required actions in your own words: ______

Business choices and why they are distinct: ______

More or less complex than another example and why: ______

Uncertain requirements or data issues: ______

## D Escalate a high risk transaction

High-Risk Online Transaction with Device Mismatch

### Scenario conditions

- fraud_risk_score = 85

- alert_type = card_not_present

- transaction_type = online

- Device mismatch and velocity anomaly

- Cross-referenced fraud database shows no blacklist

### Intended work and result

- Transaction details, customer profile, and history retrieved

- Device intelligence and fraud database cross-referenced

- Fraud risk score calculated and investigation package compiled

- Case routed to analyst

Intended final state: escalated.

Required actions in your own words: ______

Business choices and why they are distinct: ______

More or less complex than another example and why: ______

Uncertain requirements or data issues: ______

## E Handle an emergency property claim

Emergency Property Claim – Water Intrusion, Storm Peril, Coverage Confirmed

### Scenario conditions

- claim_type = property

- severity = emergency

- cause = storm/wind

- policy_status = active

- coverage_confirmed = true

- emergency_services_needed = true

### Intended work and result

- Loss details extracted (storm, water intrusion)

- Claim classified as property, peril: storm/wind

- Policy coverage validated (active, peril covered)

- Claim severity assessed (emergency)

- Claim record created with emergency flag

- Emergency water mitigation vendor dispatched

- Claim routed to CAT team

- Claim acknowledgment sent to customer

Intended final state: success.

Required actions in your own words: ______

Business choices and why they are distinct: ______

More or less complex than another example and why: ______

Uncertain requirements or data issues: ______

## F Handle a commercial interruption claim

Complex Commercial Property Claim – Business Interruption, Large Loss

### Scenario conditions

- claim_type = commercial_property

- business_interruption = true

- cause = fire

- policy_status = active

- coverage_confirmed = true

### Intended work and result

- Loss details extracted (fire, business interruption)

- Claim classified as commercial property + BI

- Property and BI coverage validated

- Severity assessed (large loss, BI exposure)

- Linked claims created for property and BI

- Claim routed to large loss unit and BI specialist

- Forensic accountant and engineer dispatched

- Claim acknowledgment sent to insured

Intended final state: success.

Required actions in your own words: ______

Business choices and why they are distinct: ______

More or less complex than another example and why: ______

Uncertain requirements or data issues: ______

## Your ranking

Easiest to hardest with ties: ______

Reason for the closest or most uncertain comparison: ______

Which features should a designed difficulty measure capture: ______

The set is deliberately selected for discussion, not a representative sample. Independent ratings are not yet collected. Source IDs and hashes are retained in the companion review.json.
