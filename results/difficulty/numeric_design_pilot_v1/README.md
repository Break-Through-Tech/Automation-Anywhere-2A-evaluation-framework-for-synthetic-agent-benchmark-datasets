# GPT-6 Sol pilot — two accepted scores, one response rejected

Start with [PILOT_REVIEW.md](PILOT_REVIEW.md) for the results, limits, diagnosed failure and proposed next call.

Premium/instant-funding account: 60/100. Standard/micro-deposit account: 65/100.
The insurance response was rejected and has no accepted score. No extra retry was run.

The two-task mean, 62.5, is a selected-subset summary, not an estimate for all 64 synthetic tasks.
No τ²-bench task was scored. Calibration and repeat checks are incomplete.

- `pilot_evidence.json`: original judgments, acceptance status, exact evidence and usage; the rejected proposal remains explicitly excluded.
- `source_bindings.json`: canonical task IDs, source pointers and hashes.
- `run_manifest.json`: model, protocol, usage and original implementation version.
- `task_scores.csv`: all 342 framework task identities, including pending and source/format error statuses.

Original exact requests and raw responses remain in the local frozen packet. Use implementation commit `9fa5640` to regenerate this v1 report.
Prompt v1.1 fixes the schema/prompt mismatch; the separately authorized insurance retry is reported below.

A separately approved prompt-v1.1 insurance retry has now passed at 70/100: [retry report](../numeric_design_insurance_retry_v11/README.md). This does not alter the original pilot results or permit pooling prompt versions.

For the current same-prompt comparison, see [the matched v1.1 pilot](../numeric_design_matched_pilot_v11/README.md): accepted scores 65, 65 and 70. The historical v1 results above remain separate.
