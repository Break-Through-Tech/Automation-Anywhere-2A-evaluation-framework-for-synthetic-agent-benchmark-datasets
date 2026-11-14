# Comparable reference-design diagnostics

Status: frozen definitions for the first offline native cross-check. These do not
change the rubric, scores or supplied data and do not require model calls.

Use the original reference-call list in each case: synthetic tool calls; native
evaluation_criteria.actions. Count that list once, not again through milestone or
unit representations. Exclude synthetic terminal signals SUCCESS, FAILED,
CANCELLED and HUMAN_IN_THE_LOOP, matching the existing structural convention.
Native transfer_to_human_agents is a real reference call and remains included.

Shared measures:
- reference_tool_interactions: number of nonterminal entries, including repeats.
- distinct_reference_tool_names: number of distinct included function names.
- repeated_reference_calls: entries minus distinct names; not necessarily redundant work.
- reference_argument_leaves: scalar argument values across included calls; null counts
  as one supplied value, an empty collection as zero. This measures representation
  size, not required operations, tool execution, reasoning or validation complexity.

An explicit empty reference list is zero listed calls, not zero required work.
When a case has neither reference actions nor explicit completion references, retain
missing reference evidence as unavailable. Do not convert it to a zero count. Native
retail 57 is such a case. Its difficulty score remains usable from goal/policy.
Python reference expressions are read statically with AST, never executed. Unresolved
argument expressions leave the argument-leaf feature unavailable while literal call
names can still be counted.
Every count retains the source path, locator and hash. No completed agent trace is used.

Compute Spearman association with the already-frozen numeric score, by dataset and
domain, with paired sample size, missingness and ties. Constant-feature correlations
remain undefined. P-values are exploratory asymptotic values, not independent
validation. Related task variants/workflows are clustered and share evidence with
the judge; do not infer causation or tune any score/weight to improve association.

Operations, business-check groups and distinct coordination events keep their
existing semantic definitions in design_counting_rulebook_v0.1/v0.2. They are not
reference-list length, parameter counts, assertion counts or actor counts. Synthetic
source-bound profiles exist; equivalent native profiles have not been authored.
Report those native features as unavailable, with no invented tags or zero values.
Completing that part of #50 requires source-bound native semantic annotations, not
renaming these exact observables. Keep #50 and parent #71 open until that work is done.
