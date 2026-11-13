# Domain calibration — nine complete cases; airline stopped on a judge error

Read this summary first. `task_scores.csv` lists all 64 synthetic and 278 native
τ²-bench tasks, including missing scores. `judgment_evidence.json` retains the model
responses, exact judgments, validation statuses and original-response provenance.
These are source-only designed-difficulty scores (0–100), not live-agent pass rates.

## Result and decision

Nine newly selected cases have three usable judgments each. Their largest within-task
range is **5 points** and mean range **2.22 points**, passing the frozen practical
limits of 10 and 5. This does not establish independent difficulty truth or complete
cross-dataset calibration. **Do not expand paid scoring until the airline contract
failure is addressed and the revised response format is checked.**

- Accounts/deposits: 65, 65, 65.
- Customer onboarding: 65, 65, 65.
- Fraud monitoring: 60, 60, 60.
- Patient onboarding: 65, 65, 60.
- Prior authorization: 65, 60, 65.
- Denied insurance claim: 60, 60, 60.
- Manufacturing purchase-to-pay: 65, 65, 65.
- τ²-bench retail: 65, 70, 70.
- τ²-bench telecom: 80, 80, 85.

The airline case initially returned **unscorable**: our adapter omitted reservation
facts present in the original benchmark database. We prepared a separate input with
the exact reservation and applicable flight-date records, clearly marked as judge-only
initial state, not knowledge already given to the task agent. Its first judgment passed
at **55**. Its second proposed 55 but invented three assessed unit IDs. That response
was rejected, not edited or accepted. The third call was not made. The case therefore
has **judge_error**, no aggregated score, and is excluded from means. This finding is
about judge/input reliability, not agent failure or evidence that the benchmark is broken.

## API use and validation fixes

**30 calls used from the approved cap of 31; one remains unused.** No paid retry was
made after the invented-unit failure. Usage: 301,696 input tokens and 65,193 output
tokens; no dollar estimate or account ownership is inferred. Thirteen earlier calls
(three development tasks repeated three times plus four controls) were reused offline.

Two earlier local rejections were representation/validation defects: a genuine
milestone citation supporting its corresponding workflow step, and a genuine tool-doc
quotation containing a line break escaped by JSON. Validator v1.2 treats cross-references
as review diagnostics and accepts exact literal or decoded-JSON-string quotations.
No fuzzy matching or invented evidence is allowed. Saved raw responses were reassessed
unchanged, with provenance; original rejections remain preserved. This made no new API
calls. All cohort results use the same revised validator. The later invented-unit
response is a genuine contract failure and remains rejected.

The rubric, equal 20% weights, anchors, prompt v1.1, generation schema and model/settings
were unchanged during these calls. The separate airline-context input has its own hash;
it is not averaged with the earlier incomplete input. Supplied benchmark files were
never edited. **144 offline tests passed** for this frozen implementation.

## Current coverage and complementary checks

Including three earlier development tasks, usable repeated scores cover **10/64 synthetic
tasks** and **2/278 τ²-bench tasks**. Their descriptive scored-subset means are **64.33**
and **75.00**. These selected, tiny, differently composed subsets cannot establish a
whole-dataset ordering or final dataset scores. Missing scores are never zero.

Tags were hidden during generation and compared afterward. Synthetic label association
is Spearman ρ=0.561 (n=10; approximate p=0.092). Associations with operations, reference
calls, business checks and coordination are 0.519, 0.736, 0.248 and 0.561 respectively.
Small samples, many ties, multiple comparisons and shared design evidence limit these
exploratory associations; they are not independent validation. No τ²-bench tags or
structural-feature values were invented. See `crosschecks.json` for counts and missingness.

The existing authored controls still pass their practical tolerances after offline
revalidation: equal-step complexity difference +40, paraphrase +5, source order +5.
These controls are excluded from benchmark means. Equal real-task scores are legitimate;
we did not change weights or thresholds to force a synthetic/τ²-bench difference.

## Next work

Constrain allowed unit IDs in the API response schema, preserve local identity/coverage
checks, add offline regression coverage, and prepare a fresh versioned diagnostic. Do
not silently pool its new generation protocol with this frozen cohort. A new bounded
paid check requires authorization beyond the remaining single call if three judgments
are planned. Broader scoring, consistent native database-context treatment and final
report integration remain open in #75–#77 and #50.

## Later, separate follow-up

After this 30-call cohort was frozen, the task-bound schema fix passed 145 offline
tests and one separately authorized diagnostic at 50/100. That exhausted the 31-call
batch cap. It is not pooled into these means. See [the follow-up](../numeric_design_schema_guard_v12/README.md).

## Latest follow-up

The separate task-bound airline cohort now validates at 50/50/50 under validator v1.3.
The signature/return rendering issue was resolved offline with explicit diagnostics;
no raw response was edited. Total approved batch calls used: 33. See [the repeat review](../numeric_design_airline_repeats_v13/README.md).
These older cohort scores and generation versions remain separate.
