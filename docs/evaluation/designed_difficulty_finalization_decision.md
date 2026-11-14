# Finalizing designed difficulty tonight

## Read this first

**The scoring formula is ready. The clarified judge passed the planned repeatability checks. Some source interpretations and rating boundaries remain subjective, so we cannot honestly promise absolutely no ambiguity.**

A practical final project metric can be versioned and reproducible while retaining those limits. “Final” would mean the chosen rules, model and results are frozen for reporting; it would not mean the scores are independently proven true.

## The proposed fixed method

Read each task's scenario, applicable workflow steps, milestones, tools, policies and intended exits. Do not run the task agent or grade an observed execution.

Rate five dimensions from 0–4: **workload, reasoning, tool use, dependencies and information discovery**. Use the existing anchors; each dimension has 20% weight. Compute locally:

**Task judgment score = 5 × sum of the five levels**, on a 0–100 scale.

A hard step is preserved through the existing maximum-required-unit rule for reasoning, tool use and information. Workload and dependencies describe the whole applicable path. The judge must provide source evidence and rationales, not merely count steps.

Average the planned usable judgments within a task first. Average usable task means equally for the dataset score. Report domains, distributions and scored/total coverage. A partial result is labeled as a subset; missing/error/unscorable tasks are never zero. Do not combine results from different prompt versions.

Original easy/medium/hard tags and structural counts are comparisons after scoring. They do not determine the score. Equal synthetic/native means can be legitimate; do not tune weights to force an ordering. The earlier 40/40/20 count proposal is not used.

## The required-path rule

Use a source-supported sufficient path to the valid endpoint, including discovery, identity checks, applicable prerequisites and required handoff preparation. A valid endpoint can be completion, escalation, refusal or cancellation.

Once a decisive mandatory exit is established, exclude later work unless sources independently require it before that exit. Do not assume an oracle finds the exit immediately. Initial records shown to the judge do not become facts already known by the task agent. Do not add all unused branches together.

This is the exact clarification tested; this sheet does not silently add a new precedence rule or redefine the frozen rating anchors. The precise addendum remains in `required_path_clarification_draft_v1.md` and the saved API requests.

## What remains interpretive

- **Rating boundaries:** words such as routine versus substantial require judgment. Repeated airline scores span 75–85 even under identical inputs. The formula is exact; the difficulty judgment is not.
- **Multiple reasonable paths:** telecom documents do not uniquely order every diagnostic action. The clarified judge explains its chosen sufficient path and flags that uncertainty.
- **Conflicting or abbreviated sources:** a fraud package example omits fields listed in the tool contract. This discrepancy stays visible; it is not repaired or turned into a difficulty penalty.

The existing rule is to retain a defensible score with specific flags when possible, and mark the task **unscorable** when missing/conflicting design sources prevent a defensible assessment. This is a source-only assessment status, not agent failure. An API or parser error also does not become a score.

## Evidence available now

The completed paired study has three judgments for six cases under each prompt. The clarified arm meets the frozen limits: largest range **10**, average range **3.33**, complex-versus-simple gap **35**. Airline's paired mean is unchanged at **80**; the fraud judge retains investigation and the full package before handoff. The SIM mean changes from **75** to **51.67**, reflecting the required-path interpretation. These findings support practical consistency, not independent accuracy or elimination of source ambiguity.

Full report: `results/difficulty/required_path_repeatability_v26/README.md`.

## The decision needed before further spending

**Recommendation:** accept the clarified rubric as an explicitly interpretive, source-backed designed-difficulty metric, freeze its version, then compute all tasks under that one protocol. No additional weight search or all-task human review is required for this operational decision. Broader validity work can remain a limitation/future task.

The prepared full run needs at most **341 new calls**: 342 tasks, 348 planned judgments, seven exact cached judgments reused. It preserves the original repeat convention. No such calls have started. Stop and diagnose errors; do not automatically retry, alter sources or tune scores.

The user's permission was conditional on there being absolutely no ambiguity. That condition is not met, so the proposed full run remains **not authorized**. Approval to proceed despite the specific documented rating/source uncertainty is needed. Otherwise, use the existing versioned results tonight: **native 65.35/100; synthetic 64.30/100**, with their original prompt and known path-interpretation limitation.
