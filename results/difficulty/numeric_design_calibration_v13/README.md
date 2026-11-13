# Revised-format calibration: nine complete cases; quotation failure stopped the run

26 of 27 newly approved calls completed: **59/60 cumulative domain calls used**, one
unused. Nine cases have three usable judgments each. Maximum repeat range **5**, mean
range **2.78**, pass the frozen practical 10/5 tolerances. Full calibration did not finish;
the decision remains **stop and review**, not permission for broad paid scoring.

- Accounts/deposits: 65/70/65; customer onboarding: 65/65/65; fraud: 60/55/60.
- Patient onboarding: 70/65/65; prior authorization: 60/60/60; denied claim: 60/55/55.
- Manufacturing: 65/65/65; airline: 50/50/50 (cached compatible calls); retail: 70/75/70.
- Telecom: valid 80, rejected proposed 80, third response not requested.

## Telecom diagnosis

The citation changed “If a user is traveling...” in the policy to “If the user is
traveling...”. Similar meaning does not make an exact quotation. It was correctly
rejected; the score is excluded and telecom has judge_error. This is a judge evidence-
format problem, not task-agent failure or proof of defective benchmark data. No paid
retry followed the error, and no raw response or supplied source was edited.

The next fix is to constrain source/excerpt choices in the API schema so quotations are
selected rather than freely recopied. Version that generation change and retain this
rejection. Do not relax the validator or silently pool protocols to obtain a pass.

## Coverage and interpretation

Usable means cover **7/64 synthetic** tasks (selected-subset mean **62.62**) and **2/278
native tau2** tasks (selected-subset mean **60.83**). These tiny selected subsets do not
establish final dataset scores or an ordering. Dataset composition and source context
differ. Retail case 57 remains source-preflight-blocked.

The full 342-task CSV retains pending/error/source statuses. The chart shows observed
repeat ranges, not confidence intervals, and explicitly excludes telecom. Evidence,
source bindings, version/model settings, raw outputs and usage remain in the JSON files.
Tags and structural features are compared only afterward; shared sources, small samples,
ties and multiple comparisons limit these exploratory checks. No thresholds or weights
were tuned to labels or desired dataset differences.

No grader code changed during this batch; its frozen implementation previously passed
146 offline tests. Five 20% dimensions remain provisional. Source gaps are reported
separately from complexity. No task agent ran. See the [reporting handoff](../../../docs/evaluation/numeric_design_reporting_handoff.md)
for #59/#63/#65/#69/#26 integration. Further paid work requires a checked format and API scope.
