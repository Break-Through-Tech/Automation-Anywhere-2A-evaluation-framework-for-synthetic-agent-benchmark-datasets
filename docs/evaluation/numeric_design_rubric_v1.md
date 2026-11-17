# Numeric designed difficulty: how to read the score

Version: `design_numeric_v1.0_provisional`
Status: frozen implementation candidate; not calibrated or approved by Sandra.

This score estimates the work an adequately capable agent would need to understand
and perform the documented task in a functioning environment. It reads the design;
it does not run an agent or measure correctness, completion probability, elapsed
time, or runtime failure rates. One test case receives one score. A shared workflow
does not imply that all its cases receive the same score.

## Scoring rule

The LLM assigns five task-level integer ratings from 0 to 4. Each dimension has the
same provisional weight (20%). **Score = 5 × sum of the five ratings**, from 0 to
100 in five-point increments. Equal weights avoid privileging a dimension without
evidence; they are an explicit modeling assumption, not learned or advisor-approved
weights. The old 40/40/20 structural-count candidate is not used.

These anchored ratings are a provisional index, not an established interval or ratio
scale: 80 is not proven twice as hard as 40. Means are descriptive summaries under
this convention. Validate stability and inspect sensitivity before strong comparisons.

## Anchors

**Workload** (breadth of required active work):
0: no active work; 1: one narrow objective with little follow-through;
2: several routine stages for one objective; 3: substantial multi-stage or repeated
work across entities; 4: extensive heterogeneous subgoals or repeated multi-entity
work. Do not equate a listed step or reference call with one fixed unit of effort.

**Reasoning** (within-step decisions and business rules):
0: no interpretation; 1: direct rule or lookup; 2: several explicit checks or a
meaningful branch; 3: integrating interacting constraints or case-dependent tradeoffs;
4: nested/interdependent decisions with substantial reconciliation. Domain prestige
and jargon alone are not reasoning difficulty.

**Tool use** (semantic selection and argument burden):
0: no tools required; 1: an explicit simple call; 2: choosing tools and binding
ordinary outputs to inputs; 3: complex/nested arguments, alternatives or repeated
entity binding; 4: heterogeneous tool orchestration requiring substantial state and
argument reconciliation. A long list of tools alone does not establish level 4.

**Dependencies** (cross-step state and coordination):
0: no dependency; 1: simple local sequence; 2: conditional prerequisites or linked
state across stages; 3: multiple linked records, approvals, handoffs or external
responses with dependent continuation; 4: interacting branches/parties/recovery paths
that require extensive state tracking. Waiting is a dependency, not an active action
or measured time cost. Do not add duplicate mentions of the same obligation.

**Information** (required discovery and reconciliation):
0: nothing to discover; 1: inputs are clear and complete; 2: ordinary retrieval,
verification or a small gap to resolve; 3: distributed/ambiguous/conflicting inputs
that the documented task requires resolving; 4: substantial multi-source discovery
and reconciliation. Missing documentation or a broken supplied tool is a source
quality issue, not automatically level 4.

## How steps inform the task score

Review all supplied workflow steps and milestones separately, with applicability
and reasoning/tool/information ratings. Milestones are requirements, not additional
operations by default. Exclude unselected alternatives, passive context, terminal
status signals, and duplicate descriptions from required workload. Include documented
task-specific requirements omitted from the reference sequence; flag conflicts.

The task's reasoning, tool-use and information ratings must be at least the maximum
of the required/selected units' corresponding levels, and may be higher only with
an explanation of cross-unit interaction. Workload and dependencies are assessed
over the whole required path. This preserves difficult steps without assuming that
averaging many easy steps makes the task easier, and accounts for breadth and
coordination separately. Dimensions can overlap; report this limitation.

Use initial triggers and scenario values to identify the applicable path. Success,
failure, escalation or cancellation exits describe intended endpoints. A case may
legitimately request escalation; no source-only review proves that any endpoint was
actually reached. Temporal prerequisites matter as design dependencies; this is not
a test that an observed transcript completed milestones in order.

## Evidence and source quality

Every positive/scored dimension, required unit and intended endpoint needs an exact
source quotation and a short rationale. Quotations establish provenance, not truth.
Explicitly note ambiguous applicability and contradictions. Mark the task unscorable
if missing/conflicting design sources prevent a defensible assessment; otherwise
retain a limited score with specific uncertainty flags. Never score parser/API errors.

Keep supplied easy/medium/hard labels, label-bearing class names, prior features and
scores, and observed outcomes outside the judge input. Compare labels afterward as
an annotation-consistency check, including same-workflow cases. They are not gold
truth. Use the same rubric and scale for every dataset; equal synthetic and τ-bench
scores can be valid. Do not tune anchors to force a preferred dataset ordering.

## Dataset summary and validation

Average repeat judgments within a task first; then give every usable task equal
weight in the dataset mean. Publish median, IQR/range, domain/workflow breakdowns,
and scored/total coverage. An incomplete mean is a scored-subset mean. Missing
scores are never zero; an all-missing dataset has no score. A secondary domain-
balanced summary must be labeled with its weighting convention.

Offline tests can verify mappings, source coverage, arithmetic, schemas and gates.
They cannot validate LLM judgments. Use a small authorized sequential pilot, then
repeat/perturbation and held-out checks under the frozen protocol. New human review
is optional, but automated consistency is not independent human validation. Inspect
structural features and label alignment separately; shared source evidence limits
their independence. Higher difficulty does not establish higher dataset quality.
