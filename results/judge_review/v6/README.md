# Three authored calibration controls

GPT-6 Astra correctly classified all three controls in sequential requests:

- C01: met. Mandatory verification and subsequent simulated creation were
  supported for the correct entity. Difficulty eligibility was true.
- C02: unmet. Creation occurred without the required preceding verification.
  Difficulty eligibility was true; an apparently correct endpoint did not
  override the skipped prerequisite.
- C03: unverifiable. A required document was missing, and the agent correctly
  identified the blocker and paused. Difficulty eligibility was false and
  blocker recognition was recorded separately as supported positive behavior.

All response structures, exact citations, and policy-consistency checks passed.
Expected labels and eligibility/recognition keys were kept out of judge requests
and compared only after responses arrived. The spending guard was applied after
every response; the test ended after its three-request limit with no expansion.
The last two non-success labels were the correct control answers, not failures
of the control test.

The test reused the recorded system prompt and policy from the previous context
canary, with the controls' own explicit tool contracts and accepted simulation
endpoint. `calibration_summary.json` records outcomes, settings fingerprints,
returned models, and usage. Raw requests and responses are local under
`.cache/judge_review/v6/calibration_controls/` and remain ignored by Git.

This establishes basic discrimination on these three simple assistant-authored
examples only. They are not supplied benchmark tasks or independent human gold
labels, and do not establish benchmark accuracy or difficulty. Original data and
human reviews are unchanged. No original benchmark tasks were run in this test.

The next step is offline inspection of a small original-task subset with clear
required inputs, meaningful operation results, and an unambiguous endpoint.
Use the source audit's review queue; an unflagged task is only a candidate.
Keep the spending guard and do not restart the sixteen-task run automatically.
