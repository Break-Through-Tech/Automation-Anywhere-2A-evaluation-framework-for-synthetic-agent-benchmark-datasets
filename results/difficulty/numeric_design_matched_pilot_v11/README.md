# Matched GPT-6 Sol pilot — 65, 65 and 70

All three source-only reviews below use the same corrected prompt v1.1, schema, model,
settings and provisional 0–100 rubric. All passed evidence, identity, applicability,
step/task consistency and arithmetic checks. Exactly two new account-review calls
were made in this follow-up; the insurance response was reused from its authorized retry.
No live task agent was run and no additional generation requests were sent.

- Premium savings account / instant funding: **65/100**.
- Standard checking account / micro-deposit funding: **65/100**.
- Commercial property and business-interruption claim: **70/100**.

## Interpretation

The account cases receive the same five task ratings: workload 3, reasoning 2,
tool use 3, dependencies 3, and information 2. Their shared complexity falls in the
same rubric bands despite different funding paths. A tie is allowed; scores are
not forced apart to reproduce supplied labels.

Insurance receives the same levels except reasoning is 3. Its explanation cites
integrating property and BI coverage, linked claims and specialist requirements.
That one-level difference produces the five-point score gap under the frozen formula.
It does not establish a statistically reliable distinction or a true difficulty ordering.
The judge still flags ambiguities in how specialist dispatch is fulfilled by the
supplied tool/reference. Source quotations establish provenance, not truth.

The original prompt-v1 account scores were 60 and 65. The earlier five-point account
gap was not sustained under v1.1. Because the prompt/schema changed between runs,
this is not a controlled estimate of model variability. Old scores remain archived
and are not pooled with these results. The original rejected insurance response is
still rejected; only its separately authorized v1.1 retry is used here.

## Scope and next check

Only 3 of 64 synthetic tasks were selected purposively. The selected-subset mean is
66.67, not an estimate of overall synthetic dataset difficulty. No tau2 tasks were
scored. Repeatability, perturbation/control and held-out checks remain incomplete;
response validity alone does not validate the metric.

The next bounded proposal is **six new model calls**: two additional judgments of each
of these three unchanged inputs. Three separate repeat packets are prepared offline,
each reusing its existing accepted response as repeat 0. Copies preserve hashes and
source provenance and do not count as new paid calls. Each packet needs only two new
calls to obtain three judgments. No requests from those packets have been sent.
This checks initial repeatability only, not the full domain-diverse calibration plan.

See matched_evidence.json, source_bindings.json, run_manifest.json and task_scores.csv.
Raw responses remain in their original frozen packets. Weights, anchors, benchmark
sources and earlier model outputs were not edited. Token usage in the manifest is
not a dollar-cost estimate or billing audit.
