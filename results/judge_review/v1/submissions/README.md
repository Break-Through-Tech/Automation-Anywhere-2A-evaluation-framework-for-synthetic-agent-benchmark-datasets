# Human review submissions

Current status on 2026-11-07: all sixteen primary task-level judgments have been imported. Sana submitted R01–R04 in [issue 51](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/51#issuecomment-6716465470). The earlier retrieval notes below describe the 2026-11-05 state. The group 1 prerequisite is now satisfied; no paid test has been run. Sandra’s policy clarification is still pending. See `POLICY_FOLLOW_UP.md`.

Retrieved on 2026-11-05. Groups 2–4 submitted twelve task-level judgments:

- Group 2: Zayd Nadir, [issue 52 comment](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/52#issuecomment-6645481687).
- Group 3: Shrutika, [issue 53 comment](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/53#issuecomment-6645765064).
- Group 4: Anjana Kummetha, [issue 54 comment](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/54#issuecomment-6645499276).

No comments were present on issue 51 at the earlier 2026-11-05 retrieval. R01–R04 were blank at that time; their answers were imported on 2026-11-07.
No API tests were run, and the prepared local retry stops before creating its
API client while those group 1 labels are missing.

The `issue_*.json` snapshots retain comment text, author, comment ID, and source
URL. `imported_reviews.json` separates the twelve submissions by review ID and
fingerprints their source comments. The matching Word and Markdown sheets and
`../sample/human_reviews.json` contain the submitted answers, with attribution.
Reviewer outcomes were transcribed without adjudication or inferred changes.

The submissions are a first pass, not detailed milestone reviews. Milestone
fields remain blank. Evidence prose, including ranges and possible citation
mistakes, is preserved; it is not presented as exact validated quotations.
The optional second reviews were not submitted. Software cannot certify that
reviewers were independent of model outputs.

`task_comparison_readiness.json` now reports sixteen received task reviews and no
pending task-level labels, with no agreement metrics. The default full comparison still requires
detailed human milestone judgments. After group 1 submits, import its actual
answers and refresh readiness. Do not fill the four labels with model judgments.
Later model results must still pass format, identity, rubric, and exact-citation
checks before comparison. The user has prohibited API tests until group 1 is complete.

Open questions retained from submissions include whether correct pauses or
escalations under contradictory fixtures are unmet or unverifiable, and whether
the intended milestones capture the whole requested outcome. Imported labels
are not silently changed to resolve policy or adjudication questions.
