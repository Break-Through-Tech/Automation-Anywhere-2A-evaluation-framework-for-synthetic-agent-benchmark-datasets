# Three attempt GPT 6 retry

The user authorized proceeding with a provisional outcome rule while Sandra's
reply remains pending. `docs/evaluation/provisional_outcome_policy.md` records
the interpretation: clear demonstrated noncompletion is unmet; uncertainty
that prevents a defensible outcome assessment is unverifiable. Environmental
observations and reasonable agent behavior are recorded separately.

All three GPT-6 Astra responses passed response-structure and exact-citation
checks. R01 was unmet, R06 unverifiable, and R07 unmet. Each response retained
separate environmental observations. The three human answers were not sent to
the model, and all sixteen original human submissions remain unchanged.

The model's R01 label differs from Sana's original unverifiable label. Under
the provisional rule, it treats demonstrated noncompletion as decisive without
claiming that the agent was at fault or that the task was feasible. This is a
policy-sensitive difference to review, not proof that the human answer is wrong.

`retry_summary.json` records identities, judgments, rationales, policy/prompt
hashes, returned models, token usage, and response fingerprints. Exact requests,
raw responses, receipt metadata, and validated per-milestone evidence are local
under `.cache/judge_review/v3/retry_gpt6_provisional/`. That directory is ignored
by Git. The run used medium reasoning, a 12000 completion-token cap per request,
no temperature parameter, and no automatic SDK retries.

Passing citation checks is not proof of semantic accuracy. This is a purposive
development sample under a changed prompt and policy, not held-out validation.
No agreement percentage or difficulty score was computed. No further paid run
was started. Review the R01 interpretation and Sandra's eventual decision
before expanding to all sixteen or presenting final scoring claims.
