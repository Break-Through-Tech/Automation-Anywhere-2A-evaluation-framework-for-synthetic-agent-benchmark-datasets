# Airline: 50 / 50 / 50 with the task-bound schema

The three unchanged GPT-6 Sol responses on the same enriched airline input now validate
under evidence validator v1.3. **Mean 50/100; repeat range 0.** This is one case, not
complete cross-dataset calibration or a dataset difficulty estimate. No task agent ran.

## What was fixed

The third response quoted each tool as `signature -> ReturnType`. Our static source
catalog stores `signature` and `returns` separately. The quoted method, arguments and
return type were all correct. Validator v1.3 recognizes that exact, deterministic
rendering from the SAME structured tool object and flags it as `rendered_tool_signature`.
It is explicitly a rendered source reference, not a literal quotation. Wrong return
types, arbitrary field concatenation, cross-object joins, invented text and fuzzy
matching remain rejected. Existing literal and decoded-JSON-string quotation checks
remain. This does not verify the semantic relevance of every citation independently.

The original rejection is preserved. Its raw response was neither edited nor regenerated;
the new result records its original path/hash/status and revalidation policy. The schema,
source input, prompt, model, weights and numerical responses were unchanged by this
validator-only correction. The earlier response inventing unit IDs remains rejected.

**146 offline tests pass.** A separate check of all 46 unique archived outputs validates
45 under the current evidence policy and still rejects the invented-unit response.
This is a regression check, not independent human validation or 46 new API calls.

## Calls and version separation

**33/33 approved calls used in the domain batch; zero remain.** The three task-bound
responses comprise one previously saved call and two newly approved repeats. Revalidation
made no API calls. Earlier source/format failures and the source-context diagnostic
remain in their original packets. Thirteen prior development/control calls were reused
offline in the historical domain report and are not counted as new batch calls.

Do not average these responses with the earlier, differently constrained airline 55
or rejected proposed scores. The [historical domain report](../numeric_design_domains_v12/README.md)
retains nine complete cases using the earlier generation schema: maximum repeat range 5,
mean range 2.22. Its ten synthetic scores include three prior development tasks. The
new task-bound schema is recorded separately and not silently pooled into those means.

The complete 342-task CSV here includes only this new-schema scored case (1/278 native
τ²-bench; 0/64 synthetic), with other tasks pending/source-blocked. A single-case subset
mean is not a whole-dataset score. The source catalog's flight-date bindings and broader
native initial-state extraction remain limitations for general comparisons.

## Next bounded step

Nine three-repeat packets are prepared offline for the remaining calibration cases,
using the SAME task-bound schema and evidence validator as this airline case. This
requires **27 additional calls**, raising the domain-batch total cap to 60 if approved.
No such calls are authorized or scheduled automatically. This finishes the prespecified
ten-case calibration in a consistent generation protocol; it does not score all 64/278
tasks or establish independent validity. Stop and diagnose any error or excessive
variation; do not repeat completed responses to obtain a desired score.

Original benchmark files and the user's existing work remain unchanged.
