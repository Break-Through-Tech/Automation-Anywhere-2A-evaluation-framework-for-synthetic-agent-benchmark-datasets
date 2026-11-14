# Broader required-path calibration — frozen proposal

Status: preparation only; requires a new API authorization. No published score or
active judge changes. The exact wording tested in the four-call probe is unchanged.

## Scope and selection

Six source-reviewed development cases, with prior scores visible during selection:
1. The first locked-SIM concern from the completed probe (discovery and reseating,
   then transfer). Reuse its original and clarified first judgments.
2. Airline 14: cancellation/rebooking, saved payments and explicit confirmation.
3. Retail 107: exchanges on two delivered orders, variant/refund/payment checks.
4. BankingFraud W3 TC2: high-risk analyst handoff requiring analysis and a package
   before routing. Package/example discrepancies remain source-quality findings.
5. C01: the existing authored simple two-step source control.
6. C02: its existing authored two-step variant with linked accounts, dated FX,
   reconciliation and approval. Rejection is an allowed endpoint after required work.

These are purposive development checks, not a random, independent or held-out
benchmark sample. C01/C02 are fixtures and never enter dataset means. Native examples
were selected with fewer known source conflicts; original gaps are not repaired.

## Paired design and budget

Three judgments per case under the original prompt and three under the exact
clarified prompt: 6 × 2 × 3 = 36 judgments. Reuse six frozen original judgments and
one completed clarified SIM judgment only when full API request equality is verified.
Thus **29 new calls** are proposed, not 36. Cached judgments are not new spending.
Inputs, tools, evidence schema, model/config, five dimensions and weights are fixed.
Only the system addendum differs between arms. No review labels or target scores
are sent to the model. Historical baseline timing is retained as a limitation.

Phase 1: five new clarified first judgments, excluding the already-scored SIM case.
Inspect them before any repetition calls. Stop on API/format/evidence failure,
unsupported path simplification, or unexplained collapse of complex controls.
Three identical scores trigger inspection, not an automatic failure or a paid retry.

Phase 2, only if Phase 1 is defensible: 24 repeated judgments, two more per case and
arm, in a frozen interleaved order. No automatic retries. Stop for errors or a
an unstable clarified-arm repeat range above the frozen tolerance. Original-arm
variation is reported as a baseline finding, not automatically treated as a failure
of the candidate or an API error. Inspect it rather than retrying it. Never spend the unused allowance merely
to obtain agreement. No full-dataset run is authorized by this plan.

## Prespecified checks

- All planned results must be usable; do not average only convenient successes.
- For EACH arm separately, maximum task repeat range ≤10 and mean range ≤5, the
  same practical tolerances used earlier. These are assumptions, not confidence bounds.
  The clarified arm must meet them for a favorable stability conclusion; original-arm
  instability is an informative comparison finding, not a requirement to obtain a
  passing historical baseline.
- For each arm, mean C02 minus mean C01 must be at least 10, the prior authored-control
  tolerance. Equal listed step counts do not imply equal required complexity.
- Airline/retail tasks have no targeted locked-SIM exit: an absolute mean change
  above 10 flags review. It is not automatic proof of an error or a reason to tune.
- SIM explanations must retain necessary discovery and exclude unrelated repair
  after the decisive exit. Fraud explanations must retain required analysis and
  package preparation before the analyst handoff. A lower score is not a pass rule.
- Inspect applicability and source evidence, not just total scores or valid JSON.

Passing these bounded checks would inform an adoption decision; it does not establish
independent numerical accuracy, validate every domain, replace published means or
authorize a full rerun. Paired repeats reduce some sampling ambiguity but do not turn
an LLM self-consistency study into human/gold validation.
