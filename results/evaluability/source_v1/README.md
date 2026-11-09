# Offline evaluability source audit

`calibration_controls.json` provides three separate assistant-authored diagnostic
examples: proper simulated completion, a created result with its mandatory check
skipped, and a missing-document blocker correctly recognized by the agent.
These are not original benchmark tasks or independent human gold labels. Their
private answer keys are separate from `judge_input` and must never be sent to
the judge. All three were subsequently graded correctly by GPT-6 Astra; see
`results/judge_review/v6/README.md`. This checks basic rule interpretation,
not judge accuracy on the benchmark. A subsequent offline inspection of three
original candidates is recorded in `results/evaluability/original_subset_v1/`.

All 64 original tasks across seven domains were checked without API calls,
new tool execution, or changes to supplied data, historical rewards, or human
reviews. `source_audit.json` records source paths/lines, hashes, literal field
comparisons, endpoint candidates, and preserved reference-execution errors.
`review_queue.json` orders follow-up work without assigning difficulty or risk scores.

The findings overlap:

- 17 tasks have reference-call execution errors already recorded in the earlier
  offline replay. These are historical execution diagnostics, not newly graded failures.
- 32 tasks have at least one difference between an expected literal field and
  a statically inspected candidate tool output. The audit found 97 such field
  differences. Materiality still needs review; generated IDs or benign numerical
  differences must not become automatic failures.
- 15 tasks contain a workflow step that mentions a business action while listing
  only system/control tools. Source review cleared one reporting-only batch
  completion phrase; the other 14 are contract-review candidates, not confirmed defects.
- One task's expected tool list includes a tool not listed in its YAML workflow.

There are 47 tasks with at least one raw triage flag and 17 without a flag.
Unflagged does not mean valid or ready for paid judging. The audit compared only
unique exact top-level expected-state fields against single literal dictionary
returns. It found 88 literal subset matches and left 490 fields unmapped by that
narrow method. Aliases, nested state, dynamic returns, and actual reachability
need additional interpretation. A method can raise before reaching a literal
return; source inspection does not prove that an action would execute successfully.

Do not interpret this audit as 47 broken tasks, an oracle pass rate, a new outcome
grader, or proof that any task is impossible. The saved reference replay remains
a self-consistency diagnostic, not independent outcome validation. Original
task judgments and difficulty eligibility are deliberately not assigned.

Review execution errors first, material reference/output conflicts second, and
completion-contract candidates third. The spending guard remains active: no
broad paid run should follow merely because the source audit completed. A future
small canary needs source-checked examples with clear accepted endpoints and
prerequisites; include separately labeled calibration controls rather than assume
that an unflagged original task is a known success.

Reproduce to a fresh directory:

```bash
python -m difficulty.audit_evaluability --out results/evaluability/source_repeat
python -m unittest discover -s tests -p 'test_evaluability_audit.py'
```
