# Native semantic complexity profiles

These profiles complement the numeric LLM difficulty score. They describe required
work from task documents, not completed execution or empirical difficulty. They do
not supply another weighted score or replace the primary score.

Use the active-operation, business-check and event definitions in
`design_counting_rulebook_v0.1.md`, with the applicability and coordination
clarifications in `design_counting_rulebook_v0.2.md`. Each authored item has a
stable key, rationale and exact source excerpt bound to the frozen input. The full
source map retains file path, locator and hash. Operations may span several calls;
a single call may implement several operations. Category tags for the same
coordination event are nonadditive.

Arithmetic alone is not a business check. Distinct policy evaluation, verification,
classification or reconciliation is a check. An ordinary lookup is not. A required
customer authorization is an external response/approval obligation under the
current rulebook; it is not an extra count per category or per conversational turn.
Ordinary synchronous tool returns and entity IDs do not create coordination events.

Profiles use three statuses:

- `provisional_complete`: assistant has proposed a complete applicable-path profile.
  Counts remain interpretive, not gold labels or independently confirmed atomic units.
- `unresolved_path`: some work is documented, but the complete applicable path is
  unresolved. Complete features are null; partial documented counts stay separate.
- `not_authored`: no semantic profile exists yet. All semantic features are null.

Do not convert missing or unresolved values to zero. Do not use a source conflict
or absent environment capability as an additional complexity penalty. Cite and
explain exclusions as well as included work. Setup state is judge context, not
information the task agent would automatically know.

The first three examples reuse previously examined development cases. Prior LLM
scores were visible, so their annotations are not independent validation. Numeric
scores are joined only in the report; no score is an input to the annotation fields
or counting logic. Do not compute a representative correlation from two usable
selected profiles. Broader authoring remains open, with a score-free remaining
queue. No tags, fixed paths or other human decisions are fabricated to fill gaps.

Run the validator with the saved full native inventory, the authored annotations,
and the published score report. It verifies original source hashes, exact quotes,
input identities, event uniqueness and missingness before producing a report.
It never imports or calls an API client and never executes benchmark tools.
