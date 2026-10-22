"""Shared label vocabulary. Use the SAME lists for tau-bench and the synthetic set,
otherwise 'diversity' just measures differences in wording, not in the data."""

TASK_TYPES = {
    "information_lookup": "User only wants facts retrieved or explained; nothing in the system changes.",
    "record_modification": "Change an existing record/order/booking/account (update, exchange, modify).",
    "cancellation_or_refund": "Cancel something or return/refund money.",
    "new_creation": "Create something new (book, open account, apply, onboard, file a claim).",
    "troubleshooting": "Diagnose and fix a problem step by step (device/service not working).",
    "verification_or_compliance": "Check, validate, approve or deny something against rules or policy (fraud review, prior authorization, invoice matching, budget approval, eligibility checks).",
    "policy_edge_case_or_refusal": "Correct behaviour is to refuse, push back, or apply a tricky policy rule.",
    "other": "None of the above fit (explain in rationale).",
}