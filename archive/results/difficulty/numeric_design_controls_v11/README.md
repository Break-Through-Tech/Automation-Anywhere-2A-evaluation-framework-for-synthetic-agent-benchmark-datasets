# Source-control checks — initial practical tolerances passed

Exactly four authorized GPT-6 Sol calls were made with prompt v1.1. All four responses
passed format, identity, exact-evidence, applicability and arithmetic checks. No other
paid calls were made in this follow-up. These are separately authored source-only
fixtures, never edits to the supplied synthetic or tau2 benchmark tasks.

- C01, simple read-and-record task: **35/100**.
- C02, linked-account reconciliation and conditional approval: **75/100**.
- C03, harmless paraphrase of C01: **40/100**.
- C04, C01 with source-catalog order reversed: **40/100**.

## Prespecified comparisons

C01 and C02 both have two listed steps. The more involved case scored 40 points higher,
meeting the minimum expected gap of 10 fixed before these calls. Its explanations cite
repeated account/rate binding, currency reconciliation and dependent approval. This is
an example of responding to work within steps rather than step count alone, not proof
that the exact numerical gap is true for every task.

Paraphrase and source-order comparisons each changed the score by +5, within the
predefined maximum absolute change of 10. They did not leave the score exactly unchanged.
Both changed the information rating from 1 to 2, while other dimensions stayed fixed.
With one call per variant, we cannot separate wording/order effects from ordinary model
variation. The observed boundary interpretation should remain a limitation, not be
reported as perfect invariance.

Thresholds were not changed after seeing results. These controls are authored examples,
not independent human difficulty labels. Repeated-score and controlled-case passes do
not establish complete construct validity, a representative dataset mean or general
cross-dataset comparability. Control scores must never enter benchmark dataset means.

## Next bounded proposal

A frozen first-pass breadth sample is prepared: seven previously unscored synthetic
tasks (one per supplied domain) and three native tau2 tasks (airline, retail, telecom).
Original pilot tasks and their workflows are excluded where applicable; selection is
by canonical ID rather than predicted score. No requests from this sample have been sent. The planned domain-diverse calibration
uses three judgments per task: **up to 30 new calls** across ten domains, requiring
authorization. Ten first-pass requests and ten three-repeat packets are frozen. The
first judgment per domain is inspected before its two additional repeats. Any API/format
failure stops expansion. This is a small frozen sample, not a representative dataset
estimate, exhaustive validation, or independent gold validation.

See control_comparisons.json, control_evidence.json, run_manifest.json and task_scores.csv.
No task agent ran. Original benchmark files, weights, anchors, prompt and prior responses
were unchanged. Usage is recorded in the manifest without inventing a billing amount.
