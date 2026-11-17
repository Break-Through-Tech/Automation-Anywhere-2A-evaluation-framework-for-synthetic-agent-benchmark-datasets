# Five diverse-case checks completed

**The wording preserves complex work in this first look. All five new responses passed format and source-evidence checks. The 24 repeated calls were not authorized and were not run.**

Published dataset scores remain **τ²-bench 65.35/100** and **synthetic 64.30/100**. This experiment does not replace them or adopt a new judge policy.

## What changed

The same frozen task documents, model settings, evidence schema, and five equally weighted dimensions were used. Only the draft required-path clarification was added to the prompt. It asks the judge to include discovery, prerequisites and genuinely required work, while excluding unnecessary actions after a decisive exit. This evaluates designed difficulty from documents; no task agent or tools were executed.

Scores below compare one saved original-prompt judgment with one clarified-prompt judgment per case. They are not repeat averages:

- **Airline 14: 75 → 85.** Balance totals, cancellation eligibility, flight comparison, multiple passengers and payment allocation remain necessary. The documented card charge is below the user's limit, so the clarification does not justify skipping the replacement booking. The +10 change warrants repeat checks; this single pair cannot distinguish wording effects from model variation.
- **Retail 107: 75 → 70.** Authentication, variant and payment checks, confirmation, and exchanges in two orders remain. The prohibited identical boot replacement selects the user's fallback rather than adding an extra exchange.
- **Banking fraud W3 TC2: 70 → 65.** Investigation, enrichment, risk assessment and a complete package remain required before analyst handoff. The judge excludes unrelated customer verification or decline paths afterward. The short expected package versus broader routing contract remains an uncertainty, not a repaired source.
- **Simple authored control C01: 40 → 40.** Retrieve and record a balance; no conversion, linked-account reconciliation or approval is required.
- **Complex authored control C02: 75 → 75.** Linked accounts, dated exchange rates, identifier discrepancies and a conditional approval decision remain. Work after approval rejection is excluded, while discovery and the decision remain. Unknown balances and approval outcomes are explicitly flagged.
- **Previously tested SIM exit: 75 → 50 (cached; zero new calls here).** Included as context for the earlier targeted exit case, not as a sixth new API call.

The controls have the same two listed steps but a **35-point complexity gap**, above the predeclared 10-point minimum. Their preserved distinction and the varied task scores argue against the earlier concern that the wording simply compresses everything to 50. These authored controls are not independent gold scores and never enter dataset means.

## Interpretation and next step

Source review found no unsupported removal of the principal required work in these five responses. That supports proceeding to repeatability checks, not claiming the wording is validated or numerically accurate. These are selected development cases with prior scores visible. Single judgments cannot establish stability, generalize to all tasks, or attribute each score change to the prompt alone.

The prepared next phase contains **24 additional calls**, interleaved across original and clarified prompts: two further judgments per arm for six cases. It still requires separate approval. The frozen repeat gates are a maximum within-case range of 10 and mean range of 5, measured per arm; the non-target mean-shift review threshold is 10. Those gates cannot be evaluated from this first phase. Do not rerun all 342 tasks or replace published results based on this report.

GitHub #50/#71 stay open: repeatability and the native semantic operations/business-check/coordination profiles remain unfinished.

## Audit and verification

Exactly five new API intents and five completed responses; no API or format errors, no automatic retries. Seven earlier judgments were reused without a call. All 12 results were revalidated, with unique response IDs and preserved raw replies, evidence, request/input hashes, model configuration, and source bindings. New-call token usage: 114,399 input and 6,473 output (120,872 total). No dollar cost or billing-account ownership is inferred.

The 176 offline tests passed during preparation; production code was unchanged in this phase. The published native comparison and synthetic score file match their branch versions. All 80 previously protected user files are unchanged.

- [Comparison CSV](comparison.csv) and [full explanations](comparison.json).
- [Execution record](run_manifest.json) and [verification](verification.json).
- `requests.json.gz` and `inventory_PRIVATE_COMPARISON.json.gz`: exact requests and source-bound inputs for these 12 observations. Identity/tag comparison metadata was not sent to the model.
- `raw/`, `results/`, `intents/`: original responses, validated judgments and the five new spending intents.
- `prepared_manifest.json`, `prepared_selection.json`, `prepared_cache_bindings.json`: frozen preparation snapshots. The preparation manifest's zero-call status describes preparation only; actual execution is recorded in `run_manifest.json`.
