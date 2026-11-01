import copy
import unittest
import json

from openai import APIConnectionError

from baseline.onboarding_pilot.environment import OnboardingEnvironment
from baseline.onboarding_pilot.grader import grade_state
from baseline.onboarding_pilot.validation import load_fixtures, valid_workflow, validate_pilot
from baseline.onboarding_pilot.run import DATASET_VERSION, run_trial
from baseline.synthetic_environment import execute, tools_for


class OutcomePilotTests(unittest.TestCase):
    def test_both_valid_workflows_pass_for_all_six_cases(self):
        results = validate_pilot()
        self.assertEqual(len(results), 12)
        self.assertTrue(all(r["reward"] == 1 for r in results))
        self.assertNotEqual(results[0]["tool_calls"], results[1]["tool_calls"])

    def test_claiming_success_does_not_create_a_successful_outcome(self):
        for fixture in load_fixtures()["cases"]:
            env = OnboardingEnvironment(fixture)
            env.SUCCESS("Done", {"onboarding_status": "success"})
            self.assertEqual(grade_state(fixture, env._snapshot())["reward"], 0)

    def test_unsafe_account_creation_is_rejected_without_mutation(self):
        fixture = load_fixtures()["cases"][0]
        env = OnboardingEnvironment(fixture)
        before = env._snapshot()
        with self.assertRaises(ValueError):
            env.create_core_banking_customer({**fixture["customer"], "kyc_status": "verified",
                "risk_level": "low", "documents": [d["file_id"] for d in fixture["documents"]]},
                fixture["application"]["account_type"])
        self.assertEqual(env._snapshot(), before)

    def test_incorrect_outcomes_fail_independent_state_checks(self):
        fixture = load_fixtures()["cases"][0]
        env, _, _ = valid_workflow(fixture)
        original = env._snapshot()
        mutations = [
            lambda db: next(iter(db["accounts"].values())).update(account_type="business_checking"),
            lambda db: next(iter(db["customers"].values())).update(name="Wrong Person"),
            lambda db: db["crm"].clear(),
            lambda db: next(iter(db["accounts"].values()))["compliance_at_creation"].update(identities=[]),
            lambda db: next(iter(db["accounts"].values()))["compliance_at_creation"].update(risk=None),
            lambda db: next(iter(db["communications"].values())).update(recipient="wrong@example.com"),
            lambda db: next(iter(db["customers"].values())).update(kyc_status="failed"),
        ]
        for mutate in mutations:
            db = copy.deepcopy(original)
            mutate(db)
            self.assertEqual(grade_state(fixture, db)["reward"], 0)

    def test_business_requires_all_owner_identities(self):
        fixture = next(f for f in load_fixtures()["cases"] if len(f["identities"]) == 2)
        env, _, _ = valid_workflow(fixture)
        db = env._snapshot()
        next(iter(db["accounts"].values()))["compliance_at_creation"]["identities"].pop()
        self.assertFalse(grade_state(fixture, db)["checks"]["identities_verified_before_creation"])

    def test_followup_document_access_requires_a_request(self):
        fixture = next(f for f in load_fixtures()["cases"] if f["address_reconciliation_required"])
        env = OnboardingEnvironment(fixture)
        followup = fixture["application"]["additional_documents"]
        with self.assertRaises(ValueError):
            env.extract_kyc_documents(followup)
        with self.assertRaises(ValueError):
            env.confirm_current_address(fixture["application"]["application_id"], followup)

    def test_grader_has_no_reference_sequence_or_terminal_claim_input(self):
        fixture = load_fixtures()["cases"][0]
        env, events, grade = valid_workflow(fixture, alternative=True)
        self.assertNotIn("SUCCESS", [e["name"] for e in events])
        self.assertEqual(grade["reward"], 1)
        self.assertEqual(grade_state(fixture, env._snapshot()), grade)

    def test_exposed_tools_do_not_include_grading_or_database_access(self):
        env = OnboardingEnvironment(load_fixtures()["cases"][0])
        tools, _ = tools_for(env)
        self.assertNotIn("grade_state", tools)
        self.assertNotIn("_snapshot", tools)
        self.assertTrue(execute(tools, {"name": "grade_state", "arguments": {}})["error"])

    def test_live_loop_grades_persisted_state_and_isolates_task_ids(self):
        fixture = load_fixtures()["cases"][0]
        _, events, _ = valid_workflow(fixture)
        class Model:
            index = 0
            def complete(self, history, side):
                if side == "user":
                    text = "Please onboard application " + fixture["application"]["application_id"]
                else:
                    event = events[self.index]
                    self.index += 1
                    text = "Thought: continue\nAction: " + json.dumps({"name": event["name"], "arguments": event["arguments"]})
                return text, {"side": side, "model": "offline-test", "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
        row, trace = run_trial(fixture, 0, 42, {"max_steps": 200}, Model())
        self.assertEqual(row["reward"], 1)
        self.assertTrue(row["task_id"].startswith(DATASET_VERSION + "::"))
        self.assertNotEqual(row["task_id"], fixture["task_id"])
        self.assertEqual(grade_state(fixture, trace["final_state"]), trace["evaluation"])
        self.assertNotIn("compliance_at_creation", trace["agent_prompt"])
        self.assertNotIn("risk_result", trace["user_prompt"])

    def test_live_loop_does_not_treat_connection_errors_as_failures(self):
        class BrokenModel:
            def complete(self, history, side):
                raise APIConnectionError(request=None)
        row, _ = run_trial(load_fixtures()["cases"][0], 0, 42, {"max_steps": 200}, BrokenModel())
        self.assertIsNone(row["reward"])
        self.assertEqual(row["evaluation_status"], "infrastructure_error")


class OutcomePilotFailureTests(unittest.TestCase):
    def assert_creation_blocked(self, fixture, events, skip=lambda event: False):
        """Replay public tools; require the attempted creation to fail atomically."""
        env = OnboardingEnvironment(fixture)
        tools, _ = tools_for(env)
        for event in events:
            if skip(event):
                continue
            before = env._snapshot()
            result = execute(tools, {"name": event["name"], "arguments": event["arguments"]})
            if event["name"] == "create_core_banking_customer":
                self.assertTrue(result["error"], result)
                self.assertEqual(env._snapshot(), before)
                self.assertFalse(before["customers"])
                self.assertFalse(before["accounts"])
                env.SUCCESS("Claimed complete", {})
                self.assertEqual(grade_state(fixture, env._snapshot())["reward"], 0)
                return
        self.fail("Replay never attempted account creation")

    def test_sanctions_matches_and_high_risk_block_creation_for_every_case(self):
        for original in load_fixtures()["cases"]:
            _, events, _ = valid_workflow(original)
            for subject in original["sanctions"]:
                with self.subTest(task=original["task_id"], sanctions_subject=subject):
                    fixture = copy.deepcopy(original)
                    fixture["sanctions"][subject] = "exact"
                    self.assert_creation_blocked(fixture, events)
            with self.subTest(task=original["task_id"], risk="high"):
                fixture = copy.deepcopy(original)
                fixture["risk_result"] = {"score": 95, "risk_level": "high"}
                self.assert_creation_blocked(fixture, events)

    def test_invalid_documents_and_wrong_identity_inputs_block_creation(self):
        for original in load_fixtures()["cases"]:
            _, events, _ = valid_workflow(original)
            for document in original["documents"]:
                with self.subTest(task=original["task_id"], invalid_file=document["file_id"]):
                    fixture = copy.deepcopy(original)
                    next(d for d in fixture["documents"] if d["file_id"] == document["file_id"])["valid"] = False
                    self.assert_creation_blocked(fixture, events)
            for person in original["identities"]:
                with self.subTest(task=original["task_id"], wrong_id_for=person["name"]):
                    altered = copy.deepcopy(events)
                    identity = next(e for e in altered if e["name"] == "validate_identity"
                                    and e["arguments"]["extracted_data"]["name"] == person["name"])
                    identity["arguments"]["id_number"] = "INVALID-ID"
                    self.assert_creation_blocked(original, altered)

    def test_missing_documents_and_unresolved_address_block_creation(self):
        for fixture in load_fixtures()["cases"]:
            _, events, _ = valid_workflow(fixture)
            for document in fixture["documents"]:
                with self.subTest(task=fixture["task_id"], missing_file=document["file_id"]):
                    altered = copy.deepcopy(events)
                    # Keep all other extractions, isolating the omitted document.
                    for event in altered:
                        if event["name"] == "extract_kyc_documents":
                            event["arguments"]["document_files"] = [
                                f for f in event["arguments"]["document_files"] if f != document["file_id"]]
                    self.assert_creation_blocked(fixture, altered)
            if fixture["address_reconciliation_required"]:
                with self.subTest(task=fixture["task_id"], address="unresolved"):
                    self.assert_creation_blocked(fixture, events,
                        skip=lambda event: event["name"] == "confirm_current_address")

    def test_incorrect_business_owners_block_creation_and_fail_grading(self):
        for fixture in load_fixtures()["cases"]:
            owners = fixture["application"].get("beneficial_owners", [])
            if not owners:
                continue
            env, events, _ = valid_workflow(fixture)
            for wrong_owners in ([], owners + ["Unknown Owner"]):
                with self.subTest(task=fixture["task_id"], owners=wrong_owners):
                    altered = copy.deepcopy(events)
                    next(e for e in altered if e["name"] == "create_core_banking_customer")["arguments"]["authorized_signers"] = wrong_owners
                    self.assert_creation_blocked(fixture, altered)
                    state = env._snapshot()
                    next(iter(state["accounts"].values()))["authorized_signers"] = wrong_owners
                    grade = grade_state(fixture, state)
                    self.assertEqual(grade["reward"], 0)
                    self.assertIn("correct_owners", grade["failed_checks"])

    def test_delivery_errors_cannot_satisfy_welcome_outcome(self):
        for fixture in load_fixtures()["cases"]:
            env, events, _ = valid_workflow(fixture)
            for field, value in (("status", "failed"), ("recipient", "wrong@example.com"),
                                 ("channel", "unsupported"), ("content", "  "),
                                 ("account_id", "unknown"), ("customer_id", "unknown")):
                with self.subTest(task=fixture["task_id"], field=field):
                    state = env._snapshot()
                    next(m for m in state["communications"].values() if m["type"] == "welcome")[field] = value
                    grade = grade_state(fixture, state)
                    self.assertEqual(grade["reward"], 0)
                    self.assertIn("welcome_actually_sent", grade["failed_checks"])
            for invalid_arguments in ({"customer_id": "unknown"}, {"delivery_method": "unsupported"},
                                      {"content": "  "}):
                with self.subTest(task=fixture["task_id"], invalid_send=invalid_arguments):
                    fresh = OnboardingEnvironment(fixture)
                    tools, _ = tools_for(fresh)
                    for event in events:
                        if event["name"] == "send_welcome_communication":
                            before = fresh._snapshot()
                            result = execute(tools, {"name": event["name"],
                                "arguments": {**event["arguments"], **invalid_arguments}})
                            self.assertTrue(result["error"])
                            self.assertEqual(fresh._snapshot(), before)
                            self.assertEqual(grade_state(fixture, before)["reward"], 0)
                            break
                        self.assertFalse(execute(tools, {"name": event["name"],
                            "arguments": event["arguments"]})["error"])


if __name__ == "__main__":
    unittest.main()
