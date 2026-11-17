# Broader calibration prepared — not run

**Zero new API calls. Published scores remain native 65.35/100 and synthetic 64.30/100.**

## What this tests

The prior four-task wording probe produced four ties at 50. This next plan asks whether
the same wording can preserve genuinely complex work while handling a simple mandatory
exit. It includes:

- The previously tested locked-SIM escalation, including discovery/reseating.
- Airline 14: cancellation/rebooking with payments and confirmations.
- Retail 107: two delivered-order exchanges with variant/payment checks.
- BankingFraud W3 TC2: analysis and a complete package before analyst handoff.
- C01/C02: authored simple and more involved designs with the same two listed steps.

These are source-reviewed development cases with prior scores visible, not independent
or held-out labels. Known source limitations are retained. The controls are fixtures,
not benchmark tasks, and never enter dataset means.

## Proposed budget and stop gates

**36 planned judgments = six cases × two prompts × three judgments. Seven exact
cached judgments are reused, so the proposal needs at most 29 NEW API calls.**

1. Five new clarified-prompt judgments first. Inspect source-backed work and exits.
2. Only if that review supports continuing, use up to 24 calls for repeated judgments
   under both prompts, following the frozen interleaved order.

Stop on the first API/format/evidence error or unsupported simplification. Inspect
unexplained ties rather than automatically calling them failure. No automatic retries
or full-dataset rerun. The previous four-call authorization is fully used; this plan
requires a new authorization. The preparation tool has no paid-run command.

## Frozen interpretation

[Full protocol and tolerances](../../../docs/evaluation/required_path_calibration_plan_v1.md).
The clarification wording is identical to the four-call probe. Task inputs, schema, model/config and five equal weights stay fixed between arms.
The original and clarified prompt results are compared as separate arms, never pooled.
Each arm's repeatability is measured; instability in the old arm is a finding, not a
requirement to make the historical baseline pass. The candidate must meet the frozen
repeat tolerances for a favorable stability conclusion. A lower score is not a pass rule.

Check the complex-versus-simple control gap, changes on non-targeted airline/retail
work, and preservation of the fraud investigation/package before handoff. These checks
could reveal that the wording over-compresses real complexity. Even passing them would
not establish independent numerical accuracy or automatically replace the 342 scores.

## Verification and files

All 176 offline tests passed. The 36 request bodies were checked against their frozen
source requests: only the system addendum differs between arms. Seven cached raw
responses were hash-verified and bound to identical requests. No new API intents or
credentials were used. Earlier user files and published numeric outputs are unchanged.

- case_inventory.csv/json: identities, source evidence and preserved source notes.
- planned_requests.csv: every arm/repeat, request fingerprint and cached/new stage.
- manifest.json: exact budget, frozen order, thresholds and configuration.
- verification.json: offline verification and unchanged-score checks.

Actual prepared bodies and the seven cached responses are under
.cache/required_path_calibration_v23. Recheck offline with:

```bash
python -m difficulty.required_path_calibration check --packet .cache/required_path_calibration_v23
```

#50/#71 remain open: this is preparation for the next validation, not completed
calibration or the remaining native operation/check/coordination annotations.
