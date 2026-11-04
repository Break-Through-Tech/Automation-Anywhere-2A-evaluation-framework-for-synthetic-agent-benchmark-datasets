# Independent review of original synthetic attempts

Reviewer: you (or a teammate you choose). All human judgments are blank until
entered by the reviewer. This packet contains no old grader labels or LLM judge
answers. It is a purposive development sample, not a held-out validation set.

1. Open review_packet.json. Read the draft rubric and one case at a time.
   Each case includes its intended outcome, milestones, scenario inputs,
   conversation, and executed tool events with arguments, results, and errors.
2. Fill the matching entry in human_reviews.json. Enter your name, task judgment
   (met, unmet, or unverifiable), rationale, contradictions, and milestone checks.
   Decide applicability/materiality with reasons. Unresolved policy or reference
   conflicts can make a judgment unverifiable; do not invent missing facts.
3. For met/unmet judgments, give evidence with a JSON-pointer locator and a short
   exact excerpt. Example: {"locator":"#/tool_events/0/output/status",
   "excerpt":"verified"}. Conversation evidence uses #/conversation/INDEX/content.
   These locators are relative to that case's transcript object.
4. Keep justified escalation separate from completion of the requested outcome.
   Do not infer success from a SUCCESS call or the simulated user's stop marker.
5. Save the form before looking at any model judgments. Run the comparison
   command documented in difficulty/README.md after model results are available.

If you prefer reviewing in chat, provide the review ID, judgment, supporting
observations, and unresolved questions. The assistant can transcribe your actual
judgments into the form; it must not invent human labels or sign off for you.

The historical attempts and source annotations are unchanged. New judgments
remain exploratory while the rubric is a draft. Full independent calibration,
including held-out examples, remains issue #48.
