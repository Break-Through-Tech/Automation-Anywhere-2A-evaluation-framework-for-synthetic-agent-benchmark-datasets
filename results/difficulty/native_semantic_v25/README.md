# Native required-work profiles: first three examples

**This adds source-linked explanations alongside the saved difficulty scores, using zero API credits. It does not change any score.**

The distinction is practical: a reference call is a listed tool interaction; an operation is required work; a business check is an evaluation; coordination is a distinct response, approval or handoff obligation.

## First examples

- **Airline 14:** 15 provisional operations, 5 business-check groups, 2 coordination events. The two reference calls are cancellation and booking, but the task also requires balance totals, itinerary comparison, eligibility checks, payment allocation, disclosure and authorization. Arithmetic aggregation is an operation, not an additional business check. The two authorization events each carry approval and external-response tags; they are counted once per event. Prior primary LLM score: 75/100. The experimental clarified score of 85 is a separate observation and is not joined here.
- **Retail 107:** 12 provisional operations, 5 business-check groups, 2 coordination events. Its two reference calls exchange items in separate orders. Authentication, per-order eligibility, variant matching, payment collection and confirmations are also required. Shared discovery and payment collection are grouped; the automatically generated email is not an extra agent operation. Prior primary LLM score: 75/100.
- **Telecom locked/missing SIM:** complete semantic counts are **unresolved**, not zero. Six documented operations, two check groups and one handoff are retained only as partial observations. Identification, SIM inspection, reseating, reassessment and transfer are supported. The complete pre-SIM diagnostic order is not uniquely specified, and the generic policy says to try to resolve the issue before transfer. The profile therefore does not pretend to provide a complete path. Prior primary LLM score: 75/100; the earlier clarified 50 is not substituted.

These grouping choices are assistant interpretations with prior scores visible. The airline and retail profiles count distinct action authorizations separately even if gathered in one conversational turn. No claim of independent numerical validation or exact atomic work is made.

## Coverage and remaining work

Of all **278 native tasks**, **2 have provisional complete profiles**, **1 has an unresolved path**, and **275 are not yet authored**. The full coverage file preserves every task, including missing features. No correlations are calculated from the two selected usable profiles. The saved primary dataset scores remain native **65.35/100** and synthetic **64.30/100**.

Next: extend the source-bound annotations across the remaining tasks and resolve path ambiguity where the sources permit it. The score-free queue includes the 275 untouched tasks and the unresolved telecom case. This is progress on #50/#71, not completion; the separate 24-call repeatability phase also remains unrun and unauthorized.

## Files and verification

- [Coverage CSV](coverage.csv): all 278 tasks; missing counts remain empty.
- [Profiles and source evidence](profiles.json): authored operation/event explanations, counts, uncertainties, exclusions and exact source bindings.
- [Remaining queue](remaining_queue.json): identities and statuses without LLM scores or proposed count suggestions.
- [Verification](verification.json): source/rule/code fingerprints and unchanged primary-output checks.
- `frozen_inventory.json.gz`: original source-bound native inputs for offline reproduction.

The targeted checks passed: **64 tests** across numeric design, native reference checks, calibration preparation and the new semantic validator. The new tests cover source mismatches, duplicate events, score identity changes and keeping missing/partial counts out of complete features. Original source hashes for all 278 native inputs were verified. All 80 protected user files and published numeric scores are unchanged. No production judge code was changed.

To reproduce from the repository root (with the pinned original native sources available):

```bash
PYTHONPATH=. python -m difficulty.native_semantic_profiles \
  --inventory results/difficulty/native_semantic_v25/frozen_inventory.json.gz \
  --annotations difficulty/native_semantic_annotations_v1.json \
  --scores results/difficulty/tau2_final_v19/comparison.json \
  --out .cache/native_semantic_replay_v25.json
```

The inventory preserves the original source-root path. On a different machine, relocate only `source_root` to the local pinned `tau2-bench` checkout; retain all payloads, source hashes and case identities.
