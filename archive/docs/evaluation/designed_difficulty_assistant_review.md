# Completed assistant review of designed difficulty

## Result

Proposed easiest to hardest: **A < B < (C = D = E) < F**. The equal signs mean an unresolved comparison, not evidence that the tasks have identical true difficulty.

Reviewed by: Codex assistant | Date: 11 November 2026

This is an assistant assessment for discussion with Sandra. The assistant had already seen the supplied tags and extracted counts. This is not a blind or independent human review and cannot validate its own feature proposal. Original review fields and supplied data remain unchanged.

## What this ranking means

A has a narrow lookup-and-report goal. B adds a resolved exception and approval dependency. C, D and E involve different types of work that we cannot fairly order without agreed feature definitions. F appears more involved because it coordinates linked claims and several specialist roles. This is a qualitative proposal, not a numeric difficulty score.

## A Check an approved authorization

**Required work:** Look up the authorization, interpret the returned status, and communicate the approval to the provider.

**Business choices:** Choose the status-specific response from the lookup result. Approval is fixed by this scenario; this does not establish an independent branching count.

**Placement and reason:** Group 1. The narrowest requested outcome, with no intended recovery loop, payment approval dependency, or linked records.

**Confidence:** Moderate for its placement as simplest; action granularity remains provisional.

**Separate uncertainty or data issue:** The scenario omits the reference ID. That is a separate feasibility issue. The workflow also bundles EHR updating with notification, so the exact action count needs confirmation.

## B Resolve an invoice mismatch

**Required work:** Match the invoice against the order and receipt, evaluate the variance, route it to accounts payable, and process payment after approval.

**Business choices:** Determine whether the variance requires review and whether approval permits payment. The scenario fixes a resolved review; do not count an unused escalation as performed work.

**Placement and reason:** Group 2. Adds exception handling and an approval dependency beyond A, but the intended path is narrower than the broader multi-system tasks in the next group.

**Confidence:** Moderate; if approval is entirely handled outside the agent, its contribution should be reduced.

**Separate uncertainty or data issue:** Receiving an already supplied invoice and signaling completion are not automatically substantive actions. Human review dependency should not be confused with the agent making the approval decision.

## C Recover from inactive insurance

**Required work:** Extract demographics and insurance, check coverage, request and incorporate updated insurance, recheck coverage, create the patient record, schedule the appointment, and send confirmation.

**Business choices:** React to inactive coverage, select the updated-insurance route rather than self-pay, and proceed after a successful recheck. Some choices are fixed by the scenario, and a final success decision may duplicate the recheck.

**Placement and reason:** Group 3. The recovery loop and state update add complexity. There is not enough agreed weighting to place it strictly above or below D and E.

**Confidence:** Moderate that it belongs above B; low for a strict ordering within C, D and E.

**Separate uncertainty or data issue:** Separate passive waiting from active work. Whether updated insurance is actually delivered by the environment is a data issue, not an extra designed action.

## D Escalate a high risk transaction

**Required work:** Gather transaction, customer and history information; cross-check device and fraud data; calculate risk; assemble the investigation package; and route the case to an analyst.

**Business choices:** Determine the appropriate risk route and ensure the package supports the handoff. The workflow is already selected in the reference, so do not assume all route selection is left to the agent.

**Placement and reason:** Group 3. Combines several information sources and a justified handoff. This differs from C’s recovery loop and E’s dispatch workflow, without establishing which is harder.

**Confidence:** Moderate for the middle group; low for ordering it against C or E.

**Separate uncertainty or data issue:** The risk threshold is in workflow trigger conditions. The current wording detector does not inspect those conditions. Tool-failure handling is separate from business decision complexity.

## E Handle an emergency property claim

**Required work:** Extract the loss, classify it, validate coverage, assess emergency severity, create the claim, dispatch mitigation, assign the team, and acknowledge the customer.

**Business choices:** Use coverage, severity and claim classification to select appropriate actions. The scenario already specifies active coverage and emergency severity, which limits the choices remaining open.

**Placement and reason:** Group 3. Requires several operational actions and coordination. Its linear intended path does not obviously outweigh C’s recovery or D’s evidence gathering.

**Confidence:** Moderate for the middle group; low for a strict ordering against C and D.

**Separate uncertainty or data issue:** The input marks catastrophe_event false while the reference assigns the CAT team. Resolve that source tension separately rather than raising the designed difficulty score.

## F Handle a commercial interruption claim

**Required work:** Extract and classify the loss, validate property and business interruption coverage, assess the loss, create linked claims, coordinate the large loss team and specialists, dispatch experts, and acknowledge the insured.

**Business choices:** Apply both coverage scopes and select the specialist route while preserving links between claims. The exact independent choices remain unconfirmed because the scenario fixes the intended path.

**Placement and reason:** Group 4. Provisional highest complexity because it adds linked claim entities and multiple specialist roles to the insurance workflow in E. Equal tool counts do not express those additional requirements.

**Confidence:** Moderate relative to E; lower for claiming it is definitively harder than every other domain.

**Separate uncertainty or data issue:** One tool may encapsulate several outputs or actions. Linked entities and coordination need consistent definitions before they become numerical features.

## Recommendation for the metric

Start with necessary actions, business choices and dependencies. Keep repeated checks and updates visible. Consider linked entities and coordination as candidate features. Keep waiting, terminal signals and environment defects separate until their treatment is agreed. Do not use supplied tags as an input if agreement with those same tags will be used as validation.

These examples show why raw workflow length and tool counts are incomplete. They do not establish weights or prove that F deserves a specific numeric score.

## Next step

Bring this completed assessment to Sandra and agree what counts as an action or a decision. Then freeze a simple candidate feature rule and check it on additional tasks. If an independent validation claim is needed, reviewers who have not seen these recommendations must provide their own judgments.
