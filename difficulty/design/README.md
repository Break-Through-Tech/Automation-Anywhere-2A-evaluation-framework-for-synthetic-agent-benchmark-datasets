# Source-only numeric difficulty

The current release is **v1.1 required-path designed difficulty**, covering all 342 tasks. Use [the final report and charts](../../results/difficulty/designed_final_v27/README.md), [fixed method](../../docs/evaluation/designed_difficulty_metric_v1.1.md), and [root replay instructions](../../README.md#reproduce-current-difficulty-without-api-credits).

An LLM reads task scenarios, applicable steps, milestones, tools, policies and intended exit requirements. It rates workload, reasoning, tool use, dependencies and information discovery from 0–4. Each has 20% weight; compute `5 × sum(levels)` locally, average repeats within task, then average tasks equally. No live task agent is run. Evidence checks establish source linkage and format, not independent numerical validity.

This package supplies adapters and validators shared by the current clarified runner. The earlier package-only CLI also remains available for historical packets; it does not automatically add the v1.1 clarification. Use `difficulty.clarified_design_run` and `difficulty.clarified_framework` for the current protocol. Replaying saved results needs no new API credits.

The [archived numeric-development guide](../../archive/guides/previous_numeric_design_README.md) preserves preparation, model-format diagnostics and original-protocol CLI instructions. Its 64.30/65.35 scores and pending statements are historical. Do not pool those scores with v1.1, or infer permission for new paid runs from old examples. [API spending guard](../../docs/evaluation/api_spending_guard.md).
