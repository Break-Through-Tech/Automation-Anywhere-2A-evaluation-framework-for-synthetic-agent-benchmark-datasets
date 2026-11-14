# Weekend scoring and reporting plan

All deadlines are in **America/New_York, November 2026**. Saturday is **November 14**; Sunday is **November 15**. This plan follows Mila's revised schedule rather than the older dates in the assignment table.

## What is already ready

Difficulty v1.1 is complete: **τ²-bench 64.15/100 (278 tasks)** and **synthetic 63.75/100 (64 tasks)**. Use the unrounded saved values in `results/difficulty/designed_final_v27/task_scores.json`, not the earlier 65.35/64.30 results. Keep the five internal difficulty weights at 20% each.

Workflow coverage is on main at `results/coverage/workflow/README.md`. Its dataset summaries describe coverage relative to each dataset's own declared catalogs; they do not establish a shared universal quality scale. All 342 coverage task identities match the finalized difficulty inventory after stripping the native domain prefix. Frozen coverage inputs and deterministic trial outputs are in `results/scoring/weekend_weight_trials_v1`.

## Saturday: yellow — formula, trials, consolidated scores

- **#60, Zayd and Ronnit:** freeze the common inputs, normalization and interpretation by **noon Saturday**, so all trials change only the outer Coverage/Difficulty weights.
- **#61:** five reviewers run one setting each, returning checked contributions, a short rationale and caveats by **6 PM Saturday**. The hard group deadline remains end of Saturday.
- **#62, Mila lead, with Ronnit and Sana:** consolidate the five reviews and record the selected convention and rationale by **11:59 PM Saturday**. Keep all five sensitivity results even if one is chosen as the headline.

Trial assignments, in Mila's requested order:

1. **Zayd (`zaydn4321`, #78): 70% Coverage / 30% Difficulty.** Coverage-heavy contrast.
2. **Ronnit (`ronnitrana`, #79): 60% / 40%.** Moderate coverage preference.
3. **Divya (`divyabapanapalli`, #80): 50% / 50%.** Neutral comparison baseline, not automatically the winning choice.
4. **Sana (`sanagrao6`, #81): 40% / 60%.** Moderate challenge preference.
5. **Mila (`bondmila`, #82): 30% / 70%.** Challenge-heavy contrast.

These trials do not change the five 20% difficulty weights and require **zero new LLM/API calls**. A shared calculator avoids five incompatible implementations; each teammate should verify and interpret their setting rather than duplicate the pipeline.

## Common proposed trial convention

Use a **relative coverage-and-challenge index**, not a validated universal quality ranking:

- Catalog completeness `A = total represented workflows / total declared workflows`. Include declared workflows with no tasks in the denominator.
- Balance `E = unweighted mean of normalized workflow entropy across the dataset's groups`. This is the README's macro-group convention; it is distinct from equal-task difficulty weighting.
- Proposed Coverage summary `C = 0.5 A + 0.5 E`. This equal split is an explicit project assumption for the trials, not a formula claimed by the coverage README or advisor-approved weights.
- Difficulty `D = finalized dataset difficulty / 100`.
- Candidate overall index `Q(w) = 100 × [w C + (1 − w) D]`.

Recompute unrounded A/E from the frozen labels and fixed catalogs; verify against the rounded coverage CSV. Do not min–max normalize using only these two datasets. Telecom conditions and Vendi remain separate diagnostics and are not double-counted in C. Do not average raw per-group Vendi values into a dataset Vendi score.

Higher D is positive under this **challenge-oriented convention**, not a theorem that harder tasks are higher quality. Differences in catalog definitions and group counts remain visible. A universal quality claim would need a shared reference scope or additional validation. Choosing weights because a preferred dataset wins is not an acceptable justification. Five weight settings are not independent samples for a statistical significance test: describe practical score changes, gaps and rank stability.

## Sunday: orange and blue — use Saturday's frozen outputs

- **#63, Zayd and Fatma:** side-by-side figures, component contributions and the five-weight sensitivity comparison. Due **November 15, end of day**; depends on #62.
- **#64, Anju and Divya:** strengths/weaknesses supported by original evidence and scope limitations, not only the composite ordering. Due **November 15, end of day**; depends on #62/#63.
- **#65, Ronnit, Mila and Sana:** domain-level Coverage and Difficulty analysis. Due **November 15, end of day**. Preserve domain task counts and catalog definitions; no cross-domain universal quality ranking is implied.
- **#66, Mila, Anju and Sana:** verify whether within-dataset differences are meaningful and explain source, sample-size and weighting limits. Due **November 15, end of day**; depends on #65.

## Monday and Tuesday: purple — findings before recommendations

- **#67, Divya and Anju:** identify synthetic weaknesses in workflow coverage, task depth and difficulty distribution. Due **Monday November 16, end of day**; use #63–#66.
- **#68, Fatma, Zayd and Sana:** prioritize proposed improvements by impact and feasibility. Due **Tuesday November 17, end of day**; depends on #67. Do not edit supplied synthetic data as part of this analysis.

## Red: report structure now, final assembly after findings

- **#69, Fatma and Zayd:** start the report scaffold immediately using `weekend_final_report_template.md`; fill sections as artifacts arrive. Final assembly follows #68 rather than the obsolete November 15 target.
- **#70, Sana and Fatma:** review the completed report after #69. The assignment's existing **November 18 submission target** is retained; no submission is performed by this plan.

## Handoff requirements

Each weight reviewer supplies their parameter values, two dataset scores, separate Coverage/Difficulty contributions, frozen input hashes, reproduction command, rationale and limitations. Mila records the final selection only after those reviews. Orange/blue work may prepare layouts now but must label unfinished values as pending. Missing inputs are not zeros. Preserve original datasets and historical reports.

## Live assignment links

- [[Yellow · Nov 14] Zayd: test Coverage 70% / Difficulty 30%](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/78) — assigned to @zaydn4321; added to project 144.
- [[Yellow · Nov 14] Ronnit: test Coverage 60% / Difficulty 40%](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/79) — assigned to @ronnitrana; added to project 144.
- [[Yellow · Nov 14] Divya: test Coverage 50% / Difficulty 50%](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/80) — assigned to @divyabapanapalli; added to project 144.
- [[Yellow · Nov 14] Sana: test Coverage 40% / Difficulty 60%](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/81) — assigned to @sanagrao6; added to project 144.
- [[Yellow · Nov 14] Mila: test Coverage 30% / Difficulty 70%](https://github.com/Break-Through-Tech/Automation-Anywhere-2A-evaluation-framework-for-synthetic-agent-benchmark-datasets/issues/82) — assigned to @bondmila; added to project 144.

The shared code and frozen input snapshots are on `codex/weekend-scoring-plan`. Work in your own branch based on that version, or copy those unchanged inputs and the calculator into your existing branch. Change the CLI weight, not the input definitions.
