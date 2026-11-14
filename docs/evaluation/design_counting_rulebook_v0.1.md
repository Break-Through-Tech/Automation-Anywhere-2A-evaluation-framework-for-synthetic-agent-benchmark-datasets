# Counting designed task complexity

Version: `design_counting_rules_v0.1_frozen`
Status: frozen for the first small AI comparison; provisional and not Sandra approved.

## How to use this rulebook

Use these same rules for our extraction and the complementary LLM review. Count
what the particular task requires under its intended working environment. Record
uncertain requirements separately. Do not use agent success, supplied difficulty
tags or our earlier score to decide a count. These rules define features, not weights.

## 1 Count active operations conservatively

Count a distinct required verb and object operation once in each required phase.
Creating a record and sending confirmation are two operations. Preparing and
assembling the same packet is one unless separate outputs or steps are explicit.

Do not split lists of fields, recipients or objects merely because they contain
and or a comma. A split needs distinct required operations supported by the task,
workflow or tool contracts. Separate demographic and insurance extraction can be
two when the source explicitly requires both operations; a single extraction of
name and date of birth is not automatically two.

Count a required repeat after changed information as another operation. Multiple
records or parties do not automatically multiply operations: expand only when the
source requires separate instances, rather than one bulk operation. Preserve batch
size and repetition as separate scope information. If the grouping cannot be
resolved, retain one conservative group and explain the uncertainty. Never label
this a proven atomic count or a minimum number of tool calls.

Exclude passive responses, receipt of another person's approval, waiting and pure
SUCCESS/completion signals from active operations. Requesting the response or
routing a review is active; receiving the response is a dependency. A tool call
can support several logical operations, and one operation can require several calls.
Use the task's applicable path, not unused denial/delay branches of a shared workflow.

## 2 Keep business checks distinct from decisions

The current feature is business checks, not exact decision points. Count an
explicit required evaluation, verification, classification or reconciliation.
A lookup or communication alone is not a check. Several attributes assessed in
one inseparable evaluation remain one check group unless separate evaluations
are supported. Repeating the same evaluation after an update is another check.

Do not add a second check merely because its result selects an action. Do not
infer a choice from the word approval or a terminal label. If a task already
selects a branch, unused alternative branches add no in-task decisions. The exact
independent decision count stays unknown; uncertainty is not a zero decision count.

## 3 Identify coordination events before assigning categories

Give each distinct obligation an event key based on its actor/recipient, purpose
and phase. Repeated mentions or citations of the same obligation reuse that key.

Categories are approval, handoff, linked_records, multi_party, external_response
and multi_channel. The same event can carry several categories. For example, one
AP review can be both a handoff and an approval dependency: one event, one item
per category, not two independent events. Never sum category counts as difficulty.

An approval dependency requires an external decision; an automatic approval
marker alone is insufficient. A handoff requires explicit transfer, assignment
or dispatch. Linked records require maintaining an explicit relationship, not
merely mentioning two record types. Multiple parties requires distinct roles or
role-specific obligations; an ordinary recipient list alone is insufficient.
External response means required returned information, not just an outbound
message. Multiple channels requires explicitly using more than one channel.

Zero means no requirement documented under the rules, not proof it cannot exist.
Conflicting sources or opaque operations need uncertainty notes, not invented
requirements or extra complexity penalties for a broken environment.

## Worked examples and expected interpretations

1. **Create a record and send its confirmation.** Two operations; no business
   check or coordination inferred merely from those words.
2. **Prepare and assemble a submission packet.** One operation unless distinct
   outputs are required. Do not count synonyms twice.
3. **Extract name and date of birth in one form-extraction operation.** One
   operation, not two because there are two fields.
4. **Verify coverage; the patient supplies updated insurance; then verify again.**
   Two verification operations and two checks. A passive update is an external
   response, not a third active operation. Count a separately required request
   only if the source states it.
5. **Route an invoice to AP; after AP approval, process payment. Another sentence
   repeats that AP approval is necessary.** Two active operations; one AP review
   event tagged handoff and approval. Repeated approval wording adds no event.
6. **Read a returned status and report it.** Two operations; no evaluative check
   inferred. If the task explicitly also requires categorization, add that
   operation and one classification check. A fixed expected answer does not
   substitute for the required operation.
7. **Create a property claim, create a BI claim, then link the two.** Three
   explicitly separate operations and one linked-record obligation. Contrast
   with an opaque create-linked-claims operation: retain that group and flag
   unresolved granularity instead of inventing its internal implementation.
8. **Send one identical email to two ordinary recipients.** One operation;
   multiple parties is not inferred solely from that recipient list.
9. **Wait for a provider's document, then submit the request.** One active
   operation plus an external-response dependency; waiting is not another action.
10. **A workflow offers approved, denied and delayed branches; this task uses
    the approved branch.** Count its required work only. Do not add unused
    branches or assume the agent independently chooses the branch.

## Freeze and resolve disagreements

Use this version and its fingerprint for the first three source-only reviews.
Generic examples are shared instructions, not labels for the selected tasks.
Hide the current task's proposed features, counts, tags and rank. Require source
citations, preserve uncertainty and compare proposals without automatic scoring.

For a disagreement, classify it as a missed requirement, unsupported split,
duplicate coordination event, check-versus-lookup confusion, applicability issue,
or unresolved source conflict. A citation passing validation does not prove that
the interpretation is correct. Revise rules in a new version rather than changing
them mid-run to obtain agreement. Old profiles remain provisional candidates;
this rulebook does not silently certify or regrade them. No API run is authorized
by preparing or testing this document.
