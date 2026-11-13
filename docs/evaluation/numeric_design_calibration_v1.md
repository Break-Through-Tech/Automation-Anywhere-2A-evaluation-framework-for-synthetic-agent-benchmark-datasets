# Calibration protocol before broad paid scoring

Version: `design_calibration_v1`
Status: development repeats and source controls completed; nine-case domain repeat check passed. Airline source/context and unit-identity failure keep full calibration incomplete. See [the domain review](../../results/difficulty/numeric_design_domains_v12/README.md).

1. Run offline contract, mapping, citation, schema, arithmetic and spending-gate tests.
2. With explicit API authorization, score three synthetic cases sequentially:
   accounts/deposits W1 TC1, the same workflow's TC2, and insurance claims W8 TC1.
   The first pair shares workflow steps but has different scenario requirements.
   The third tests linked records and coordination. This is a purposive development
   sample; it is not representative, held-out or independent validation.
3. Stop at the first API, incomplete response, schema, citation or input failure.
   Stop and inspect three identical scores or two consecutive unscorable judgments.
   Equal scores are not necessarily wrong. Diagnose before another paid call; never
   retry to obtain desired agreement or silently replay an interrupted request.
4. Review the pilot's source quotations, applicability decisions, step difficulty,
   task dimensions, endpoint and arithmetic. JSON validity alone is insufficient.
5. With separate authorization, repeat a domain-diverse subset (at least one task
   from each synthetic domain and each included τ-bench domain) three times. Keep
   the rubric, model and decoding fixed. Candidate tolerances: maximum within-task
   range 10/100 and mean range at most 5/100. Report every case and sample size.
   These practical tolerances are assumptions, not empirically derived confidence bounds.
6. Use separately labeled source-only control fixtures: one simple case versus a
   case with the same number of listed steps but more interacting constraints,
   tool binding, and dependencies. Predefine the expected complexity direction from
   the source changes; candidate expected gap at least 10/100. Also include identical
   cases and defensible ties. Fixture responses used by unit tests are simulated,
   never presented as real model scores or independent difficulty ground truth.
7. Test harmless paraphrases and reordered source catalogs that preserve dependency
   meanings. Candidate score difference at most 10/100. Do not reorder actual
   temporal prerequisites and then assume the design is unchanged.
8. Freeze the final prompt/rubric before a distinct held-out domain/workflow sample.
   Check source-backed explanations as well as stability, document disagreements,
   and record an explicit go/no-go assessment. If any criterion is unmet, keep scores
   exploratory and revise/retest; do not silently optimize thresholds after seeing results.

New human review is optional under the requested schedule. AI self-consistency and
source agreement do not establish independent human validity. Supplied tags and
structural features are compared afterward (#50); do not tune to copy labels or
force τ-bench above synthetic scores. Any rubric revision creates a new protocol
version and a new run; old and new scores must not be silently pooled.
