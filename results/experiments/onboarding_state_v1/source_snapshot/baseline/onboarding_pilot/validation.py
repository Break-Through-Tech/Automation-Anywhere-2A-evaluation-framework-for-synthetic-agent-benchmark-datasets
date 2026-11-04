"""Offline validation scenarios; these plans are never exposed to the live agent."""
import json
from pathlib import Path

from baseline.onboarding_pilot.environment import OnboardingEnvironment
from baseline.onboarding_pilot.grader import grade_state
from baseline.synthetic_environment import execute, tools_for

CASES = Path(__file__).with_name("cases.json")


def load_fixtures():
    data = json.loads(CASES.read_text())
    fixtures = data["cases"]
    if len(fixtures) != 6 or len({f["task_id"] for f in fixtures}) != 6:
        raise ValueError("Pilot requires six unique onboarding tasks")
    for f in fixtures:
        names = {p["name"] for p in f["identities"]}
        if not names or not names <= {d["name"] for d in f["documents"] if d["id_number"]}:
            raise ValueError(f"Missing identity document in {f['task_id']}")
        if set(f["sanctions"]) != names | {f["customer"]["name"]}:
            raise ValueError(f"Incorrect sanctions subjects in {f['task_id']}")
        if {d["file_id"] for d in f["documents"] if d["availability"] == "initial"} != set(f["application"]["document_files"]):
            raise ValueError(f"Initial documents differ from the application in {f['task_id']}")
    return data


def valid_workflow(fixture, alternative=False):
    """Use service-returned facts and IDs to exercise two different valid paths."""
    env = OnboardingEnvironment(fixture)
    tools, _ = tools_for(env)
    events = []
    def call(name, **arguments):
        event = execute(tools, {"name": name, "arguments": arguments})
        events.append(event)
        if event["error"]:
            raise AssertionError((fixture["task_id"], name, event["output"]))
        return event["output"]
    app_id = fixture["application"]["application_id"]
    app = call("get_application", application_id=app_id)
    if alternative:
        call("get_application", application_id=app_id)  # harmless extra read
        for name in [app["customer_profile"]["name"], *app["beneficial_owners"]]:
            call("screen_sanctions_lists", customer_data={"name": name})
        risk = call("calculate_aml_risk_score", profile_data=app["risk_profile"])
    extracted = call("extract_kyc_documents", document_files=app["available_documents"])["documents"]
    for doc in sorted((d for d in extracted if d["id_number"]), key=lambda d: d["name"], reverse=alternative):
        call("validate_identity", extracted_data=doc, id_type=doc["id_type"], id_number=doc["id_number"])
    if not alternative:
        call("screen_sanctions_lists", customer_data={"name": app["customer_profile"]["name"], "owner_names": app["beneficial_owners"]})
        risk = call("calculate_aml_risk_score", profile_data=app["risk_profile"])
    if app["followup_required"]:
        followup = call("request_missing_documents", application_id=app_id, reason="Please provide supporting documents")
        call("extract_kyc_documents", document_files=followup["new_documents"])
        if app["address_reconciliation_required"]:
            call("confirm_current_address", application_id=app_id, evidence_files=followup["new_documents"])
    app = call("get_application", application_id=app_id)
    customer = {**app["customer_profile"], "kyc_status": "verified", "risk_level": risk["risk_level"],
                "documents": app["available_documents"]}
    created = call("create_core_banking_customer", customer_data=customer, account_type=app["account_type"],
                   authorized_signers=app["beneficial_owners"])
    if alternative:
        call("create_core_banking_customer", customer_data=customer, account_type=app["account_type"],
             authorized_signers=app["beneficial_owners"])  # idempotent retry
    crm = call("create_crm_profile", customer_id=created["customer_id"], risk_level=risk["risk_level"],
               kyc_documents=app["available_documents"])
    call("send_welcome_communication", customer_id=created["customer_id"], communication_type="welcome",
         content="Your account is ready." if alternative else "Welcome! Your onboarding is complete.",
         delivery_method=app["preferred_channel"])
    if not alternative:
        call("SUCCESS", message="Completed", result_data={**created, **crm})
    return env, events, grade_state(fixture, env._snapshot())


def validate_pilot():
    data = load_fixtures()
    results = []
    for fixture in data["cases"]:
        for alternative in (False, True):
            _, events, grade = valid_workflow(fixture, alternative)
            if grade["reward"] != 1:
                raise ValueError(f"A known valid workflow failed: {fixture['task_id']} {grade}")
            results.append({"task_id": fixture["task_id"], "alternative": alternative,
                            "tool_calls": [e["name"] for e in events], **grade})
    return results
