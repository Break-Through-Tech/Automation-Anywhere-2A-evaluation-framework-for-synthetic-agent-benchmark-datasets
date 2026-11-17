# Completed sixteen attempt development sample

The remaining thirteen attempts were judged with GPT-6 Astra using the exact
prompt and provisional policy from the three-attempt retry. The three existing
responses were reused without new requests. All sixteen responses were received;
there were no API errors. Requests, raw responses, settings, and provenance
remain private under `.cache/judge_review/v3/full_sample_gpt6_provisional/`.

Initially, fifteen responses passed citation validation. R10 was rejected only
because whole JSON values were quoted without serialization whitespace. The
validator was corrected to accept the same complete structured value with
different JSON formatting whitespace. It still rejects changed strings or
values, omitted fields, duplicate keys, reordered arrays, and paraphrases.
The saved response was revalidated offline without modifying it or making
another paid call. All sixteen now pass structure and citation checks.

`validation_history.json` retains the before/after status. The original run
manifest and validation files were not rewritten. `run_summary.json` records
the new validator hash, thirteen new requests, three reused responses, and
the unchanged prompt and policy hashes. `task_comparison.json` contains the
task-only comparison; `case_comparison.json` records every model label and
rationale alongside the original human label.

Ten of sixteen labels match the submitted human labels. The other six are
R01, R03, R05, R08, R15, and R16. This 62.5 percent descriptive agreement is not
accuracy: the human labels were collected under the earlier draft, while the
model received an additional provisional policy. Reviewer independence is not
certified, and R04's human submission referenced the historical grader. No
overlapping second reviews or human milestone labels were supplied.

Review the six differences before expanding to the full saved dataset. R01/R03
raise observable noncompletion versus reasonable behavior under blockers;
R05 needs consistency review against that interpretation; R08 raises whether
contradictory history makes the selected branch unassessable; R15/R16 raise
whether completing listed checks establishes the full requested approval
outcome. These are review topics, not adjudications or changes to human labels.

Sandra's policy review remains pending. No human answers, supplied tasks,
historical rewards, or framework scores were changed. No empirical difficulty
or milestone-agreement metric was calculated, and the other 240 saved attempts
were not judged in this run.
