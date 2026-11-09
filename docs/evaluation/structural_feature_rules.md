# Proposed structural difficulty signals

These features describe the supplied tasks and their intended workflows. They do
not measure agent success, validate the judge, or establish empirical difficulty.
The extraction uses no model calls and does not modify the supplied dataset.
Version `structural_features_v0.1_proposed` remains a proposed feature definition.
Seven examples have a completed AI-assisted source review at the user's request;
this does not establish independent human validation of all 64 tasks.

The main output is `results/difficulty/structural_v1/task_features.json`, with one
record per canonical Python `test_case_id`. It includes source paths, class line
numbers, workflow pointers, and hashes for all 21 input files. Test cases are read
as Python syntax without executing their classes, mocks, or tool methods.

## Counting rules

- Class difficulty tag: the final `easy`, `medium`, or `hard` token in the Python
  class name. The separate class `difficulty` field is retained for comparison;
  disagreement is flagged. Tags are supplied labels, not validated scores.
- Workflow steps: the number of entries in the referenced YAML workflow's `steps`
  list. A class workflow such as `W1 - Standard Personal Account Onboarding` maps
  to YAML workflow ID `W1`. Missing or ambiguous mappings stop extraction.
- Workflow tool mentions: each name in each step's `tools_used` list counts once
  per appearance. Multiple tools in one step and repeated mentions are counted.
  These mentions are not necessarily actual calls or requirements for every path.
- Reference tool interactions: names from the task's expected tool-call sequence.
  Repeated names count as repeated calls. The unique-name count is also reported.
  `SUCCESS`, `FAILED`, `CANCELLED`, and `HUMAN_IN_THE_LOOP` are counted separately
  as system/control calls rather than domain interactions. Their exclusion from
  the domain-tool count does not imply that escalation has no complexity.
- Milestones: the number of milestone entries in the JSON task reference. A
  milestone is not assumed to equal a YAML step or a tool call.
- Decision cues: count YAML steps whose descriptions contain at least one of
  `if`, `unless`, `otherwise`, `whether`, `depending`, `based on`, `approve`,
  `approval`, `reject`, `rejection`, `escalate`, or `escalation`, ignoring case and
  matching whole words/phrases. Count each matching step once and retain its text
  and matched cues. This is a reproducible wording heuristic, not a branch count.
  Unconditional approval can match; decisions expressed with other wording can
  be missed. Global workflow-selection rules and trigger conditions are not
  included in this step-description cue count.

All workflow counts describe the shared workflow definition. Task-specific path
steps and exact decision-point counts remain null until reviewed. Tools expected
by a task but absent from its workflow's tool lists are flagged for inspection;
this can reflect reference differences rather than a confirmed defect.

Keep the features separate. There is no weighted or combined difficulty score.
Tasks sharing one workflow share some features, so they are not independent
examples of different workflow lengths. Later correlations need validated
success outcomes and should account for domain and workflow grouping.

## Review status

The completed document is `results/difficulty/structural_v1/REVIEW.md`. Its seven
examples, one per domain, were checked with AI assistance and have recorded notes
in `review_sample.json`. The user waived the pending human-review step for this
structural review. No independent human judgment or reviewer identity is claimed.
The extractor still creates blank review forms when run in a fresh output folder.
Seven examples are a spot check, not approval of every task or counting rule.
Task-path and exact decision counts remain unknown; they are not filled by guesswork.
This waiver does not change the separate independent human judge-review study.

## Reproduce

```bash
python difficulty/structural_features.py --out results/difficulty/structural_v2
python -m unittest discover -s tests -p 'test_structural_features.py'
```

Use a fresh output folder; extraction refuses to overwrite an existing feature
file or human review sample. The source dataset remains read-only.
