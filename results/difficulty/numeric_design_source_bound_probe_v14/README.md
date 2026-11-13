# Source-bound evidence diagnostic: API rejected the request

The final authorized diagnostic returned **HTTP 400 / BadRequestError**, before a model
judgment or token-usage record was returned. **60/60 cumulative domain request slots are
used; no calls remain authorized.** This turn attempted 27 calls: 26 returned judgments,
then the experimental diagnostic was rejected. No billing charge is inferred from that
rejection. No automatic retry, fallback, task-agent run or source-data edit followed.

## Why the experiment exists

The [26-call calibration cohort](../numeric_design_calibration_v13/README.md) has nine
complete repeated cases within tolerance (maximum range 5, mean range 2.78). Telecom's
second response changed “a user” to “the user” in a claimed exact policy quotation, so
it was rejected and its proposed score excluded. The remaining call tested selecting
exact source/excerpt pairs through an API schema instead of freely copying quotations.
The full source text still supports reasoning; the score formula and weights are unchanged.

**152 offline tests pass.** They check altered articles, wrong-source evidence, tool-signature rendering,
provider schema-size limits for all 342 tasks, and failure gates. That does NOT establish
API compatibility. The request was within the documented enum/string limits, but the
specific server rejection reason was not retained by the earlier error logger. Do not
claim a diagnosed API root cause, successful fix or complete calibration from this run.

The [official Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs)
describes enum constraints, definitions/references and schema limits; actual acceptance
must still be verified for this request and account/model.

## What changed offline afterward

The excerpt-choice schema is explicitly **experimental and opt-in**, not the default.
The API-exercised task-bound unit schema remains the default. Strict evidence validation
still rejects paraphrased quotations. Safe error capture now retains bounded server
code/parameter/message fields with credential redaction, without saving headers or whole
requests as error strings. Original failure records remain unchanged.

A fresh one-request diagnostic is prepared with the SAME rejected API body and updated
error capture. It requires new authorization. Its first purpose is to obtain the specific
HTTP 400 reason; only a concrete, offline-reviewed correction should precede any subsequent
call. A proposal of **up to three additional diagnostic calls** would raise the request
cap to **63**. None are scheduled or authorized automatically. Do not use a large batch
to debug this API compatibility issue.

The nine valid triplets remain useful provisional numeric evidence, not final dataset
scores or independent validity. Historical controlled examples remain separate. Broader
synthetic/native scoring and issue closure remain pending; previous broad-run packets
are pinned to earlier implementation hashes and must be regenerated after the format is settled.

See `evidence.json` for the preserved request, original manifest, HTTP status and error
record. No old response was edited or accepted merely to obtain agreement.
