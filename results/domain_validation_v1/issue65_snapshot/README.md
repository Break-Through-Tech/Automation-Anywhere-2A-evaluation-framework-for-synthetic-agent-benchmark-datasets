# Domain-level Coverage and Difficulty (#65)

Compares airline and retail within τ²-bench using the frozen workflow Coverage
inputs and FINAL v1.1 designed Difficulty. Telecom and the seven synthetic
agents are included for context and for #66.

```bash
python coverage/domain_profiles.py
```

No API calls, agent runs, embeddings or reruns. Inputs: the frozen workflow labels,
catalog and coverage CSV in `results/scoring/weekend_weight_trials_v1/inputs/`,
`results/difficulty/designed_final_v27/` (task scores and domain summary) and
`results/framework/metrics_by_domain.csv` (separate diagnostics). Input SHA-256
fingerprints are in `provenance.json`.

## How each domain is scored

- **Coverage** uses each domain's own workflow catalog. Completeness = workflows
  with at least one task / declared workflows; entropy = normalized workflow
  entropy. C = 0.5 × completeness + 0.5 × entropy, the same convention as the
  dataset index. Values are recomputed unrounded from the frozen labels and catalog.
- **Difficulty** is the FINAL v1.1 designed-difficulty mean of each domain's tasks
  (0–100), with the five internal weights at 20% each.
- **Composite** uses the selected #62 weights: 100 × (0.5 C + 0.5 D / 100). It is
  shown for comparison only; each domain is still scored against its own catalog.

The script stops if any check fails. All passed:

- Completeness and entropy match the frozen coverage CSV for all 10 groups.
- Each domain's difficulty mean matches its task scores.
- Weighting the domain means by task count (50 / 114 / 114) reproduces the τ²-bench
  mean of 64.1547 exactly, and the synthetic mean of 63.75.

## τ²-bench domains

| Domain | Tasks | Workflows | Entropy | Coverage C | Difficulty mean (IQR) | Composite 50/50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Airline | 50 | 9 / 9 | 0.923 | 0.962 | 59.10 (50–70) | 77.62 |
| Retail | 114 | 9 / 9 | 0.809 | 0.905 | 64.87 (55–75) | 77.67 |
| Telecom | 114 | 3 / 3 | 0.979 | 0.989 | 65.66 (51–75) | 82.30 |

![τ²-bench domain profiles](tau2_domain_profiles.png)

**Airline vs retail:**

- **Coverage favors airline.** Both domains have tasks for all 9 of their
  workflows, so the difference is balance: retail's tasks pile into item changes
  (73 of 114), giving lower entropy (0.81 vs 0.92) and lower C (0.905 vs 0.962).
- **Difficulty favors retail.** Retail's designed difficulty averages 5.77 points
  higher (64.87 vs 59.10). Airline is more spread out (30–90) with a lower
  middle; retail sits in a tighter, higher band (50–80).
- **The two effects cancel in the composite.** Airline scores 77.62 and retail
  77.67, a 0.05-point difference. The composite hides that the domains are
  strong in opposite ways, so the components should be reported with it.
- Telecom scores highest on both components, but its 3-workflow catalog is
  much smaller than airline's or retail's, so its C is not directly comparable.

## Synthetic agents

| Agent | Tasks | Workflows | Entropy | Coverage C | Difficulty mean | Composite 50/50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Banking accounts/deposits | 8 | 6 / 8 | 0.833 | 0.792 | 66.25 | 72.71 |
| Banking customer onboarding | 6 | 4 / 8 | 0.639 | 0.570 | 67.50 | 62.24 |
| Banking fraud monitoring | 13 | 9 / 9 | 0.973 | 0.987 | 63.46 | 81.06 |
| Healthcare patient onboarding | 9 | 8 / 8 | 0.983 | 0.991 | 65.56 | 82.34 |
| Healthcare prior authorization | 9 | 8 / 8 | 0.983 | 0.991 | 58.33 | 78.73 |
| Insurance claims intake | 10 | 8 / 9 | 0.922 | 0.905 | 65.00 | 77.77 |
| Manufacturing purchase to pay | 9 | 8 / 9 | 0.930 | 0.909 | 61.67 | 76.30 |

Banking customer onboarding is the clear outlier: it is missing 4 of its 8
workflows, which pulls its composite down to 62.24. With 6–13 tasks per agent,
one task changes these scores noticeably.

## Separate diagnostics (not part of the profile)

These come from earlier results and are not blended into Coverage or Difficulty.

| Domain | Vendi / n | Mean write actions | Empirical difficulty (baseline agent) |
| --- | ---: | ---: | ---: |
| Airline | 0.309 | 0.98 | 0.225 |
| Retail | 0.237 | 1.54 | 0.268 |
| Telecom | 0.022 | 4.35 | 0.160 |

- The baseline agent also failed retail tasks more often than airline tasks, which
  agrees with designed difficulty on the airline–retail ordering.
- Telecom disagrees: it has the highest designed difficulty but the lowest
  empirical difficulty. Designed and empirical difficulty measure different things
  and should stay separate.
- Telecom conditions (19 of 20 represented, entropy 0.926) remain a separate
  diagnostic and are not counted as another group.

## Limitations

- Each domain is scored against its own catalog, and catalogs differ in size
  (3 to 9 workflows), so cross-domain differences in C partly reflect catalog
  definitions. Retail and airline workflow labels are curated project labels.
- Designed difficulty is an LLM rating of each task's design, not agent
  performance; harder does not always mean better.
- The 50/50 weights and the 0.5/0.5 split inside C are reporting conventions,
  not validated choices.
- Domains differ in size (50 vs 114 tasks), and no significance test is claimed.
  Whether these differences are meaningful is tested in #66.
