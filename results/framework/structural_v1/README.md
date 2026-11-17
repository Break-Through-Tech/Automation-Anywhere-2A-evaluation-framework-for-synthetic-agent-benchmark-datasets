# Local framework run with proposed structural features

This run completed on 2026-11-05 using real CPU embeddings from the pinned
public sentence-transformer model. The model was downloaded because the local
cache was incomplete. No paid API calls or new agent attempts were made.

The run includes all 342 framework tasks. The 64 synthetic tasks have the
optional `designed_` columns in `difficulty_tasks.csv`; the 278 tau2 tasks have
blank values for those synthetic-only columns. `run_metadata.json` records
feature and source hashes. `integration_check.json` records the identity,
column, and historical-score preservation checks.

Historical write counts and empirical outcomes match the earlier framework
output. Synthetic empirical difficulty of 1.0 is the existing original-grader
result, not a new milestone-judge finding or proof of intrinsic difficulty.
No new correlations or combined score were computed for the proposed structural
signals. Their status remains awaiting validated outcomes.

The separate human review packet and private judge runs are not merged into
these historical scores. The next API test remains on hold for issue 51.
