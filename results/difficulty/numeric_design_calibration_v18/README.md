# Current-format practical calibration

Decision: **proceed_bounded_provisional_scoring**. Ten tasks (one from each synthetic/native domain), three identical-input judgments each. Maximum observed range 5/100; mean range 2.5/100. Frozen tolerances: maximum 10, mean at most 5.

Separate controls: C01 simple 40, C02 more interacting requirements with the same two steps 75; paraphrase C03 40, source-order C04 40. Complexity gap 35 exceeds 10; harmless-change gaps 0 are within 10. Controls never enter dataset means.

The original v16 generation cohort made twenty-seven new API calls (v18 revalidation made zero): three native initial judgments, twenty repeats, four controls. Seven synthetic first judgments were reused unchanged from the published final run, with exact request equality and provenance; no repeat was retried or selected for agreement. Three equal repetitions were inspected as legitimate ties, not failures. The controller initially flagged the 35-point difference ACROSS control cases as if it were a repeat range; this orchestration-only check was corrected before the remaining control, without changing requests, rubric or saved outputs.

Evidence review: airline cancellation with no insurance needs policy interpretation but no forced write; retail exchange binds eligible item/options/payment after lookup; telecom MMS requires coordinated user and assistant actions across several fault states. Source notes separate fixture setup from agent work, and reference actions from executed traces. All ten repeated tasks are purposive diagnostics, not representative independent validation. Required/optional and conflicting-source handling has offline regression coverage and source-backed model observations; no exhaustive independent semantic assessment is claimed.

This passes bounded practical consistency checks, not gold difficulty validation. All scores remain provisional. Supplied labels and structural features are post-scoring cross-checks, not tuning targets. Model gpt-6-sol; low reasoning; same frozen five-dimension 20% rubric, prompt v1.3/schema v1.4 citation-ID protocol as the full synthetic run. See task_scores.csv, reliability.json and control_comparisons.json.

Validation v1.4 derives the fixed total locally from unchanged ratings, preserving model-reported totals and mismatch diagnostics. All calibration requests/raw outputs were rebound unchanged offline; no new calibration calls.
