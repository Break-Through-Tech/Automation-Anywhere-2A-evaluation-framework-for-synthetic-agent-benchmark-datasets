# Workflow coverage attributes

This rebuild adds workflow labels to the same 278 tau2 base tasks and 64
synthetic tasks used in the October coverage results. It supports the
November within-domain analysis in the challenge overview. The old task-type
labels group telecom under troubleshooting; these attributes show which
problems those troubleshooting tasks actually cover.

This step creates and checks labels. Recomputing Attribute Diversity, Vendi,
validation experiments, and charts is the next task. Existing scores and
plots still use the old attributes.

## Run

From the repository root with the project environment active:

```bash
python labeling/workflows.py
python -m unittest discover -s tests -p test_workflow_labels.py -v
```

The build uses Python and PyYAML from the project requirements. It makes no
API calls and does not execute agents. No tau2 checkout is needed for a
normal run. To keep a separate copy, use `--output-dir PATH`.

## Where the labels come from

| Dataset/group | Sources reviewed | Label method |
| --- | --- | --- |
| Synthetic, all seven agents | Agent role, goals, guidelines and workflows in `agent_definition.yaml`; Python case workflow/title; JSON input conditions | Keep the existing workflow IDs and names. Join Python and JSON cases within each agent using the workflow/case number, exact title and workflow agreement. |
| Tau2 telecom | Main policy, technical support manual/workflow, task IDs and generator condition definitions | Extract the source workflow family and issue conditions from each task ID. Check every condition against the generator definitions. |
| Tau2 retail and airline | Domain policy, full task goal/instructions, task purpose and reference actions | Curate requested workflow families per task in `workflow_task_map.csv`, using the definitions in `workflow_rules.json`. These are project labels, not official tau2 annotations. |

Tau2's agent system prompt inserts the domain policy. The saved prompt and
policies are in `workflow_sources/tau2/policy/`. Synthetic workflow definitions
are already part of each agent's YAML prompt. A workflow ID such as `W1` is
only meaningful within its own agent, so every output key includes the
dataset and agent category.

The tau2 snapshot uses commit
`dd8757d4c8791dad7b3cdaf02a105a3d5f9d86bd`, the revision recorded in
`baseline/baseline_config.yaml`. Its base split IDs, descriptions and reference
actions were checked against `data/processed/tasks.jsonl`. The snapshot
includes the full selected task instructions, source URLs, file hashes, and
the upstream license. It does not claim to cover other tau2 splits.

To rebuild the source snapshot from that pinned checkout:

```bash
python labeling/snapshot_workflow_sources.py --tau2-root /path/to/tau2-bench
```

The source files must match the saved pinned hashes. Updating the benchmark
revision requires a separate review of the snapshot, selected tasks and labels.

## Label rules

- A workflow family describes the requested business goal, not every tool
  call used to accomplish it. A task can have more than one family.
- Keep explicit conditional requests. For example, airline task 45 requests
  cancellation, then a flight change, then insurance if earlier options fail.
- Keep refused or unsupported requests because they test policy handling.
  A cancellation task with no reference tool calls is still a cancellation
  scenario. A label does not mean the action succeeded or was allowed.
- Do not label negated requests. Cancelling insurance is not cancelling a
  flight; abandoning a modification request is not cancelling a reservation.
- A reference implementation can contain extra steps. Airline task 29 uses
  cancellation/rebooking in the reference, but its requested goals are flight
  and baggage changes. Reference tools are retained in separate fields.
- Routine lookups and transaction totals do not add an information workflow.
  Independent balance, status or other information requests do. Choosing
  baggage/passengers while booking is part of booking; changing an existing
  reservation's baggage/passengers is a separate family.
- Telecom conditions are a separate multi-label attribute. Persona is retained
  separately, so a different user personality does not create a new workflow.
- Synthetic labels describe the declared case workflow. Input conditions are
  saved as evidence, not turned into guessed scenario labels. This does not
  establish that the synthetic reference or execution is correct.

## Files to review

Outputs are in `coverage/labels/workflows/`:

| File | Contents |
| --- | --- |
| `workflow_labels.csv` | One row per task; workflow keys, telecom conditions, persona, separate assistant/user reference tools, method and notes. Pipe-separated fields contain distinct labels. |
| `workflow_catalog.csv` | Definitions, source, scope, task counts and agent-level denominators. Includes declared synthetic workflows with zero selected cases. |
| `workflow_counts.csv` | Workflow and telecom condition counts for review. These are not diversity scores. |
| `workflow_evidence.jsonl` | Task/policy references, definition sources, telecom condition descriptions, synthetic input conditions and notes. |
| `checks.json` | Source/code/output hashes, versions, task counts and checks performed. Scoring status is `not_run`. |

`legacy_task_type` is copied from the old label CSVs for traceability; this
build does not validate or revise those model-generated labels. Reference
tools are expected tools, not observed execution logs. Telecom user tools
are kept separate from assistant tools.

## What the label rebuild shows

Telecom's 114 tasks now have three source workflow families:

| Family | Tasks |
| --- | ---: |
| MMS issues | 49 |
| Mobile data issues | 36 |
| Service issues | 29 |

There are also 19 observed issue-condition labels, including combinations
within each family. The source snapshot defines 20 conditions; one is not
represented in this selected split. Tasks with the same short description
can therefore have different conditions. This is the variation a single
troubleshooting label hid.

For synthetic data, 51 of 59 declared workflows have selected Python test
cases. These eight have no cases in the current 64-task evaluation set:

| Agent | Unrepresented workflow IDs |
| --- | --- |
| Banking accounts/deposits | W4, W5 |
| Banking customer onboarding | W2, W3, W5, W8 |
| Insurance claims intake | W9 |
| Manufacturing purchase to pay | W9 |

This is a gap between agent definitions and the selected Python cases. It
does not mean the workflows are missing from every source JSON file or that
the agent cannot execute them. The next review can decide whether to add
cases or change which cases the framework loads.

## Checks and limitations

The build rejects duplicate/missing task IDs, unknown workflow or telecom
condition IDs, changed pinned sources, stale curated mappings, Python/JSON
title or workflow mismatches, and changed reference tools. Synthetic IDs
use different prefixes in some Python and JSON files; the join checks the
agent, terminal workflow/case number and exact title instead of trusting
the prefix alone. Python cases are parsed without importing agent code.

Tests cover those source checks, refusal and negation cases, conditional
goals, multiple goals, tool roles, the zero-count catalog and reproducible
outputs. The CSVs and evidence are deterministic; `checks.json` also records
the environment versions, which may differ between machines.

These checks establish source consistency, not independent human agreement
with every curated label. A teammate should review the taxonomy and task
evidence before using it for final results. New or edited tasks require
reviewing the mappings rather than silently applying old labels.

## Handoff: recompute and validate coverage

1. Review the definitions and a sample from every domain, including the
   conditional/refused cases above. Record any disagreements and resolve
   them before freezing labels for scoring.
2. Read `workflow_labels.csv` and join by `(dataset, task_id)`. Tau2 IDs
   include the domain prefix, matching the old coverage label files.
3. Compute workflow attributes within domains/agent categories. For telecom,
   report family coverage and condition coverage separately. Count a task
   once per label; use all tasks in its group as the denominator. Multi-label
   percentages can exceed 100% when added together.
4. Define how multi-label attributes enter Attribute Diversity before
   recomputing it. Splitting pipe-separated labels into one categorical
   string would incorrectly treat each combination as a new workflow.
   Keep the catalog fixed during removal experiments, including zero counts.
5. Compare within-domain patterns and declared-workflow representation.
   Different domains have different vocabularies and catalog sizes; a raw
   count of local workflow names is not a fair overall dataset ranking.
   A shared cross-domain mapping would need a separately checked definition.
6. Rerun controlled removals and matched-size comparisons, saving selected
   task IDs and before/after counts. Report the actual changes. Neither
   normalized Vendi (`VS/n`) nor entropy is guaranteed to fall under every
   removal. Do not change labels just to force tau2 to score higher.
7. Decide separately whether to enrich the text used for Vendi. The current
   Vendi script embeds descriptions, so adding CSV labels alone does not
   change embeddings or Vendi scores. If using workflow/context text, document
   the same construction rules for both datasets and recompute both.
8. Regenerate summaries only after scoring and validation. Link each claim
   to the new inputs so the final report supports actionable recommendations
   and the challenge overview's reproducibility requirements.
