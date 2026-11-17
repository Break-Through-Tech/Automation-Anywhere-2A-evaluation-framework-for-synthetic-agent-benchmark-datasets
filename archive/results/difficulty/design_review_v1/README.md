# Complementary design feature review packets

Three source-only requests are prepared; no paid LLM review has been run.
Send only each request's messages array from requests.json. Never send
comparison_targets_NOT_FOR_MODEL.json. That separate file is for offline comparison.
The reviewer is asked to independently propose actions, checks and coordination
with exact source evidence, without seeing our counts, weights, score or tags.
Source wording can still signal complexity; this is not complete removal of cues.

Store returned JSON as D01.json, D02.json and D03.json in a fresh local response
folder. Preserve actual model, settings, raw response, timestamps and exact request
hashes in any API runner. Start with at most three sequential requests; validate
each before continuing and stop on an API or validation error. Do not automatically
run all 64 tasks or retry to obtain agreement. The agent-outcome spending guard's
unmet/unverifiable labels do not directly apply to this different response schema.

Validate saved response bodies and compare with our annotations offline:

    python -m difficulty.design_feature_review --packet results/difficulty/design_review_v1 --responses /path/to/local/responses --out results/difficulty/design_review_compared_v1

The validator checks request fingerprints, exact citations, schema and identities.
It does not establish semantic truth. Count differences are a review queue, not
proof that either annotation is wrong. Neither agreement nor a second LLM is
independent human validation. No scores, weights or profiles are auto-updated.
Runtime outcome evaluation remains in llm_judge.py as a separate procedure.
