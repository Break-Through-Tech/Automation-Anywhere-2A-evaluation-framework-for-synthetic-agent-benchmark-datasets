# Dataset strengths and weaknesses (#64)

τ²-bench scores **79.67** and synthetic **75.85** under the selected
50% Coverage / 50% designed Difficulty formula. About **95% of the
3.82-point gap comes from Coverage**. Average Difficulty is nearly tied.

## Results

| Measure | τ²-bench | Synthetic |
| --- | ---: | ---: |
| Cases scored | 278/278 | 64/64 |
| Combined index, 0–100 | 79.67 | 75.85 |
| Coverage component, 0–100 | 95.18 | 87.95 |
| Workflows represented | 21/21 | 51/59 |
| Mean group workflow entropy, 0–1 | 0.904 | 0.895 |
| Represented workflows with one case | 1 | 38 |
| Designed Difficulty mean, 0–100 | 64.15 | 63.75 |
| Difficulty median | 65 | 65 |
| Middle 50% of Difficulty scores | 55–75 | 60–70 |
| Difficulty range | 30–90 | 45–80 |

Coverage combines workflow completeness and mean group entropy equally.
The combined index then weights Coverage and Difficulty equally. Vendi and
telecom conditions remain separate diagnostics.

## τ²-bench

**Strengths**

- All 21 categories in the current catalog have cases, with only one
  workflow represented by a single case. This provides more examples per
  category, although count alone does not establish variety.
- Difficulty spans a wider range, which can support testing across more
  challenge levels. Its larger sample and different task mix also matter.
- Mean reasoning and information-discovery ratings are higher than
  synthetic's: **2.65 vs 2.33** and **2.41 vs 2.05**, on the 0–4 scale.

**Weaknesses and limitations**

- Retail is concentrated in item changes (**73/114 cases**). Its workflow
  entropy is **0.81**, compared with airline's **0.92**, despite both
  representing all nine categories.
- Telecom's 114 cases have only three distinct processed descriptions.
  Raw Vendi stays around **2.5**, missing variation captured by its
  **19/20 represented problem conditions**. This limits description-based
  measurement rather than proving the cases are repetitive in every respect.
- Airline and retail categories were defined from existing tasks. Their
  100% coverage does not prove all intended or real-world workflows are
  tested and can favor τ²-bench against synthetic's supplied workflow list.

## Synthetic

**Strengths**

- Fraud monitoring and both healthcare agents represent every declared
  workflow, with high balance (**entropy 0.97–0.98**).
- Average designed Difficulty is close to τ²-bench's despite fewer cases.
- Mean workload, tool-use and dependency ratings are higher:
  **2.86 vs 2.74**, **2.94 vs 2.55** and **2.58 vs 2.47**. This indicates
  a different challenge profile, especially for linked work and tool use.
- Explicit workflow definitions make missing selected cases easy to identify.

**Weaknesses**

- Eight declared workflows lack selected cases: accounts/deposits misses
  **2/8**, customer onboarding **4/8**, insurance **1/9**, and manufacturing
  **1/9**.
- **38/51 represented workflows have one case.** Balanced counts therefore
  do not establish testing of alternative inputs, exceptions or failure paths.
- Difficulty is concentrated around **60–70**, providing a narrower challenge
  range. Each agent has only **6–13 cases**, so individual cases can move
  group scores noticeably.

## Interpretation

- The combined gap mainly reflects missing synthetic workflows, rather than
  a large difference in workflow balance or average Difficulty.
- τ²-bench remains higher across all five weight settings, but the gap varies
  from **2.45 to 5.18 points**. Since it is higher on both components,
  this ordering follows mathematically; it is not independent validation.
- Airline has higher Coverage and retail higher Difficulty. Their combined
  scores (**77.62 vs 77.67**) are effectively tied and reverse with a small
  weight change. Neither is a clear overall winner.
- Different domains and workflow catalogs limit direct comparisons. The
  selected index is a project reporting convention, not a universal quality
  ranking. Greater Difficulty does not automatically mean better quality.
- Difficulty estimates documented complexity; it does not measure agent
  success or verify case correctness. The 0.40-point mean difference does
  not establish a meaningful separation.
- Completeness pools workflows, entropy averages groups equally, and Difficulty
  averages cases equally. Dataset scores cannot be reconstructed by simply
  averaging domain composites. Telecom condition coverage also has no
  standardized synthetic equivalent.

## Next steps

- Add selected cases for the eight missing synthetic workflows.
- Expand single-case workflows with relevant alternative inputs and exceptions.
- Review concentrated areas such as retail item changes and the intended
  difficulty mix before expanding either dataset.
- Present component scores and distributions alongside the combined index.
  Prioritize useful tests within each agent's responsibilities.
