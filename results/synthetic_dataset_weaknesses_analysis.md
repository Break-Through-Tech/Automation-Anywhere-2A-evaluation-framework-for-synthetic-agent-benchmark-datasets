# Synthetic dataset weaknesses: evidence review

**Prepared for:** Issue #67, “Identify synthetic dataset weaknesses”  
**Evidence snapshot:** frozen scoring handoff at commit `357d1d5527145a7283395f8fe9b3007ecaaf35ea`; domain validation handoff at `564f8e9d6953a0f2ac460d2b990096a2f3d62607`.  
**Scope:** source/label coverage and designed difficulty. This review does not evaluate agent execution outcomes.

## Summary

The strongest evidence-backed weaknesses are thin workflow depth, missing declared workflows, a narrow task-type mix, and a compressed designed-difficulty distribution. The synthetic inventory has 64 tasks. Its selected Coverage score is 87.95/100 versus 95.18/100 for τ²-bench, while finalized designed Difficulty is nearly tied at 63.75 versus 64.15. The selected 50/50 combined index is 75.85 versus 79.67; about 95% of that 3.82-point difference is Coverage-driven.

These scores support targeted review of the synthetic inventory. They do not establish universal dataset quality: the workflow catalogs differ, the synthetic groups are small, and the designed-difficulty metric is interpretive and source-only.

## Findings and recommended follow-up

| Priority | Finding | Evidence | Recommended follow-up |
| --- | --- | --- | --- |
| 1 | Workflow coverage is incomplete and represented workflows are often shallow. | 51/59 declared synthetic workflows are represented (86.4% catalog coverage); 8 have no test cases. Of the represented workflows, 38 have exactly one task. The selected dataset Coverage score is 87.95/100. | Review the eight missing workflows against the intended scope, then add cases for those that are valid targets. Add varied cases to high-priority singleton workflows so each is exercised under more than one state or outcome. |
| 2 | The task-type mix is concentrated in creation and verification/compliance. | 32/64 tasks (50.0%) are creation and 27/64 (42.2%) are verification/compliance, together 92.2%. There are zero troubleshooting and cancellation/refund tasks, two record-modification tasks, one information-lookup task, and two policy-edge/refusal tasks. | Ask domain reviewers which underrepresented task forms are authentic for each synthetic domain. Expand only the relevant categories; τ² task labels are useful context, not a quota, because its domains differ. |
| 3 | The synthetic difficulty distribution has few low- and high-end cases. | Synthetic median is 65, IQR 60–70, and range 45–80. Its 64 scores include 11 in 40–59, 52 in 60–79, one in 80–100, and none below 40. τ² has median 65, IQR 55–75, range 30–90, with 34/278 scores in 80–100 and 2/278 in 20–39. | Decide whether the benchmark is intended to span a broader difficulty range. If so, add deliberately simpler and more demanding cases, and inspect the five dimension ratings (workload, reasoning, tool use, dependencies, information discovery) to understand which aspects are missing. Do not add complexity just to raise the mean. |
| 4 | Synthetic task counts are uneven across its four domains. | Banking has 27/64 tasks (42.2%), healthcare 18 (28.1%), insurance 10 (15.6%), and manufacturing 9 (14.1%). Banking customer onboarding has 4/8 declared workflows missing; banking accounts/deposits has 2/8 missing; insurance claims intake and manufacturing purchase-to-pay each have 1 missing. | Review the banking workflow gaps first. Rebalance domain counts only if the project has a target scope or domain allocation; equal counts are not inherently required. |

## Comparisons to report carefully

- τ²-bench has 21/21 represented workflows; synthetic has 51/59. Mean normalized workflow entropy is about 0.90 for τ² and 0.89 for synthetic. The near-equal entropy does not erase missing synthetic workflows or singleton depth: a group can have high entropy when many workflows occur once.
- The synthetic task-type distribution differs sharply from τ², but the datasets cover different domains. Treat this as an inventory-design prompt, not proof that synthetic should copy τ²’s categories.
- The four synthetic domains (banking, healthcare, insurance, manufacturing) are not matched to τ²’s airline, retail, and telecom catalogs. Do not claim a direct domain-by-domain coverage ranking.
- The selected 50/50 index is a project reporting convention. Keep Coverage, Difficulty, sensitivity settings, task counts, and distributions visible. Do not average domain composite scores to reproduce the dataset headline because Coverage and Difficulty use different aggregation rules.

## Limitations

- Coverage workflows are based on declared project catalogs; catalog scope and labels need domain review. Missing from a catalog means “no task for a declared workflow,” not automatically “the benchmark lacks an entire real-world capability.”
- Vendi is a separate text-diversity diagnostic. Its normalized score depends on inventory size and repeated descriptions, so it should not replace workflow coverage or task-type counts.
- Designed Difficulty estimates task-design complexity from source material. It does not run agents, measure task success/failure, prove numerical ground truth, or establish dataset quality.
- Synthetic workflow groups contain only 6–13 tasks. Individual tasks can materially move group-level summaries.
- The current checkout is at `521d7c8`, while the analysis uses the issue’s frozen `357d1d5` scoring handoff. Reconcile the snapshot before copying these findings into a report on another branch.

## Sources

- [Selected coverage-and-challenge index and sensitivity analysis](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/blob/357d1d5527145a7283395f8fe9b3007ecaaf35ea/results/scoring/final_index_v1/README.md)
- [Coverage distributions and task-type summary](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/blob/357d1d5527145a7283395f8fe9b3007ecaaf35ea/results/coverage/summaries/README.md)
- [Finalized designed-difficulty metric and interpretation](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/blob/357d1d5527145a7283395f8fe9b3007ecaaf35ea/results/difficulty/designed_final_v27/README.md)
- [Difficulty distributions and domain summaries](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/blob/357d1d5527145a7283395f8fe9b3007ecaaf35ea/results/difficulty/designed_final_v27/summary.json)
- [Domain validation and catalog/aggregation caveats](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/blob/564f8e9d6953a0f2ac460d2b990096a2f3d62607/results/domain_validation_v1/README.md)

