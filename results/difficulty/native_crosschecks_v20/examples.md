# Equal-reference-count examples

These pairs were selected after scoring to illustrate variation. They are not held-out validation or proof that the judge is correct. The scores and all model ratings remain unchanged.

## tau2/airline: 0 reference calls, 40-point score gap

### 46 — 30.00/100

Transfer the unresolved insurance-only cancellation and refund request to a human, without cancelling the flight or insurance or offering a refund. This is an intended endpoint, not an observed outcome.

**Saved judge explanation:** The agent must distinguish insurance-only removal from cancelling the flight and choose the out-of-scope transfer rule while avoiding an unsupported refund. The transfer procedure specifies one simple tool with an issue summary; no booking write or complex argument binding is needed.

Source excerpt (`completion_design`):

> Agent does not cancel insurance or offer a refund.

### 10 — 70.00/100

Communicate that an outbound-only cabin upgrade is unavailable and assess the conditionally acceptable reservation-wide business proposal with the May 24 date change. If its actual extra cost is under $1000 and the user explicitly confirms, update the complete reservation; otherwise explain the constraint or price and do not make a date-only or underpriced change. The sources do not establish that a qualifying May 24 itinerary or price exists.

**Saved judge explanation:** The agent must reconcile the user's outbound-only preference with the reservation-wide cabin rule, keep the date change coupled to business class, and apply the strict cost ceiling to the actual proposal. Locating the appropriate reservation and searching for replacement flights require binding retrieved identifiers and itinerary details; any permitted update takes the cabin, payment ID, and the entire new flight list, including unchanged segments.

Source excerpt (`scenario`):

> You do not accept to change the flight date without changing the cabin to business.

**Interpretation:** Both reference lists contain zero calls, but the policy/scenario can still require lookup, cost comparison, confirmation or a transfer. These zero counts are source-list facts, not a claim that no tools are needed.

## tau2/retail: 5 reference calls, 35-point score gap

### 10 — 50.00/100

Transfer to a human with a summary of the unsupported crossed-refund request, followed by the required transfer message. This is an intended endpoint, not an observed outcome.

**Saved judge explanation:** The agent must apply the delivered-order refund restriction to two different original payment methods and recognize the requested cross-refunds are unsupported. The selected path binds lookup results to user and order reads, then supplies an issue summary to the transfer tool; it requires no complex write arguments.

Source excerpt (`policy_1`):

> The refund must either go to the original payment method, or an existing gift card.

### 104 — 85.00/100

Subject to policy checks and user confirmations, request the three specified delivered-order returns, change the pending order's address and item option, and provide the requested tracking number. The scenario also invokes a cancelled order, so its status and tracking details must be verified rather than assumed from the supplied records.

**Saved judge explanation:** The agent must distinguish cancellation language from eligible delivered-order returns, group items by order, apply refund and variant rules, and preserve the pending order's modifiability until its address is changed. Across the required units, authentication and user, order, and product retrieval feed three returns and two distinct pending-order writes. Repeated order-item-payment binding and a multi-field profile-address transfer require substantial argument reconciliation beyond any one unit.

Source excerpt (`policy_1`):

> Generally, you can only take action on pending or delivered orders.

**Interpretation:** The same five listed calls can represent an unsupported refund request or multiple returns and pending-order changes. Tool count alone does not encode argument binding or applicable policy.

## tau2/telecom: 1 reference calls, 25-point score gap

### [service_issue]airplane_mode_on|break_apn_settings|lock_sim_card_pin|overdue_bill_suspension[PERSONA:Hard] — 50.00/100

Transfer to a human agent for the unfixable locked-SIM issue while service remains unavailable; give the prescribed transfer message. This is an intended endpoint, not an observed outcome.

**Saved judge explanation:** The agent must distinguish fixable No Service causes from the locked-SIM escalation rule and avoid transferring solely on the initial complaint. Customer lookup and user-mediated status checks require choosing the appropriate tools and using their results; the eventual transfer itself has a simple summary argument.

Source excerpt (`policy_2`):

> If it is ON, guide the user to use `toggle_airplane_mode()` to turn it OFF.

### [service_issue]break_apn_settings|contract_end_suspension|lock_sim_card_pin|unseat_sim_card[PERSONA:Hard] — 75.00/100

A justified transfer to a human agent while service remains unavailable, rather than a claim that signal was restored. The policy also calls for the specified transfer message after the tool call.

**Saved judge explanation:** The agent must distinguish fixable device conditions from a SIM-security escalation and a contract-ended suspension that cannot be lifted even after payment. The path calls for selecting and linking customer, line, bill, and user-device diagnostics or fixes before a transfer with a summary; it does not require assuming every available tool is used.

Source excerpt (`policy_1`):

> You are allowed to lift the suspension after the user has paid all their overdue bills.

**Potential consistency concern:** Both documented outcomes are transfers, and both designs contain a locked-SIM condition. The manual says to escalate when the SIM is locked. The higher score explanation also charges account/bill investigation and additional fault handling; this may exceed the necessary path once a decisive escalation condition is known. The general policy also says to try to resolve the problem before transfer, so source-backed path interpretation matters. This pair should be reviewed before treating the 25-point gap as justified complexity. No score has been patched and no agent was run.

Source: `tau2-bench/data/tau2/domains/telecom/tech_support_manual.md`, SIM Card Issues: “If it shows "Locked" (due to incorrect PIN or PUK entries), **escalate to technical support for assistance with SIM security**.”

