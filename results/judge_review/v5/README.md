# Context diagnostic stopped after two requests

Offline follow-up is now recorded in `offline_adjudication.json` and
`docs/evaluation/evaluation_expectations_v0.1.md`. R01 and R15 remain excluded
under explicit working evidence expectations, with source-backed reasons and
no new paid calls. These decisions do not overwrite human or model labels.

The planned test had at most three sequential GPT-6 Astra requests. Each would
be checked before another was made. Both R01 and R15 passed structure, citation,
and policy checks but were unverifiable. The spending guard stopped immediately:
R07 was not called, and there was no expansion to sixteen.

Unlike the earlier run, these requests included the reconstructed agent-visible
system prompt and runtime tool schemas, plus separately marked reference YAML
workflows and descriptions. The source hashes match the original baseline
manifest. Reconstruction uses the current schema library; exact historical
per-trial schema serialization was not separately archived. Human labels and
earlier judge answers were not sent to the model. The human-labeled successful
case was a diagnostic candidate, not a forced positive or held-out example.

## Offline diagnosis

R01: The agent did not open the account. The actual runtime schemas permit
partial customer objects, while the workflow still requires meaningful owner
identity and compliance verification. The recorded customer offered sensitive
details through a secure channel but did not actually provide them in the
conversation. Whether the existing data supported proper execution remains
unresolved. This is not proof that an environmental blocker existed or that
the agent's extra information demands were mandatory. Permissive validation
alone does not demonstrate proper completion.

R15: The saved tool outputs disagree with the supplied matching-travel scenario.
The scenario specifies device DEV-200002 and recent Miami travel; the tool
returns DEV-998877 and a profile with New York/Chicago travel. The reference
expects risk 25, while execution returns 15. Source inspection confirms that
`retrieve_transaction_details` in `data/banking_fraud_monitoring/test_cases.py`
returns a fixed literal dictionary at line 206; the alert ID is only logged.
The runtime SUCCESS tool reports completion/result data rather than establishing
a separate approval mutation, while the YAML workflow assigns approval and case
updating to that step. The business endpoint is therefore ambiguous under the
full-outcome rule. These are concrete evaluation-design/source issues, not an
API-format failure or proof that the agent failed the task.

The added context fixes an input omission, but it does not resolve these two
cases. Do not continue spending credits merely to obtain varied labels. Next,
resolve what the simulation's accepted completion evidence is and classify
source/reference contradictions offline with the team lead. Preserve supplied
data unless a separately versioned repair is explicitly approved. Keep workflow
checks and blocker recognition as diagnostics when full success is unassessable.

`run_summary.json` records the two calls, skipped attempt, stop reason, context
and prompt hashes, and token usage. `case_diagnosis.json` retains judgments and
supporting environment/recognition findings. Raw requests and responses remain
under `.cache/judge_review/v5/canary_with_context/`. No difficulty score was
computed, and original human answers and supplied source files are unchanged.
