"""Checks for workflow extraction, source joins, and the committed label set."""

import contextlib
import copy
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workflows", ROOT / "labeling/workflows.py")
workflows = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflows)


class WorkflowLabelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labels, cls.catalog, cls.evidence, cls.provenance = workflows.build()
        cls.by_id = {(r["dataset"], r["task_id"]): r for r in cls.labels}

    def test_selected_tasks_are_preserved(self):
        self.assertEqual(Counter(r["dataset"] for r in self.labels), {"tau2": 278, "synthetic": 64})
        self.assertEqual(len(self.by_id), len(self.labels))
        self.assertEqual(len(self.evidence), len(self.labels))
        self.assertEqual(self.provenance["downstream_scoring_status"], "not_run")

    def test_telecom_families_match_source_goals(self):
        rows = [r for r in self.labels if r["domain"] == "telecom"]
        self.assertEqual(Counter(r["workflow_keys"] for r in rows), {
            "tau2:telecom:mms_issue": 49, "tau2:telecom:mobile_data_issue": 36,
            "tau2:telecom:service_issue": 29})
        self.assertEqual(len({c for r in rows for c in r["telecom_conditions"].split("|")}), 19)

    def test_same_goal_retains_different_conditions(self):
        rows = [r for r in self.labels if r["workflow_keys"] == "tau2:telecom:mms_issue"]
        self.assertEqual(len({r["goal"] for r in rows}), 1)
        self.assertGreater(len({r["telecom_conditions"] for r in rows}), 1)

    def test_persona_does_not_create_a_workflow(self):
        rules = {"mms_issue": "MMS"}
        factors = {"airplane_mode_on": {}}
        normal = workflows.telecom_labels("[mms_issue]airplane_mode_on[PERSONA:None]", rules, factors)
        hard = workflows.telecom_labels("[mms_issue]airplane_mode_on[PERSONA:Hard]", rules, factors)
        self.assertEqual(normal[:2], hard[:2])
        self.assertNotEqual(normal[2], hard[2])

    def test_unknown_telecom_condition_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown telecom"):
            workflows.telecom_labels("[mms_issue]made_up[PERSONA:None]", {"mms_issue": "MMS"}, {})

    def test_refused_request_keeps_its_workflow(self):
        row = self.by_id[("tau2", "airline:0")]
        self.assertEqual(row["reference_assistant_tools"], "")
        self.assertEqual(row["workflow_keys"], "tau2:airline:cancellation")

    def test_negated_request_does_not_get_a_false_label(self):
        self.assertEqual(self.by_id[("tau2", "airline:46")]["workflow_keys"], "tau2:airline:insurance_change")
        self.assertEqual(self.by_id[("tau2", "airline:5")]["workflow_keys"], "tau2:airline:compensation")

    def test_multiple_goals_are_preserved_once(self):
        row = self.by_id[("tau2", "retail:2")]
        self.assertEqual(set(row["workflow_keys"].split("|")), {
            "tau2:retail:information_request", "tau2:retail:return_refund"})

    def test_conditional_goals_in_full_instructions_are_preserved(self):
        for task_id in ("airline:13", "airline:32"):
            self.assertIn("tau2:airline:cabin_change", self.by_id[("tau2", task_id)]["workflow_keys"])
        self.assertEqual(set(self.by_id[("tau2", "airline:45")]["workflow_keys"].split("|")), {
            "tau2:airline:cancellation", "tau2:airline:flight_change", "tau2:airline:insurance_change"})
        self.assertIn("tau2:retail:order_creation_request",
                      self.by_id[("tau2", "retail:77")]["workflow_keys"])

    def test_reference_steps_are_not_extra_requested_goals(self):
        self.assertEqual(self.by_id[("tau2", "airline:29")]["workflow_keys"],
                         "tau2:airline:baggage_change|tau2:airline:flight_change")
        self.assertNotIn("cancellation", self.by_id[("tau2", "airline:34")]["workflow_keys"])
        self.assertEqual(self.by_id[("tau2", "airline:20")]["workflow_keys"], "tau2:airline:booking")

    def test_workflow_ids_are_scoped_to_the_agent(self):
        w1 = [r for r in self.catalog if r["dataset"] == "synthetic" and r["workflow_key"].endswith(":W1")]
        self.assertEqual(len(w1), 7)
        self.assertEqual(len({r["workflow_key"] for r in w1}), 7)

    def test_declared_workflows_without_cases_are_kept(self):
        missing = {r["workflow_key"] for r in self.catalog if r["dataset"] == "synthetic" and r["task_count"] == 0}
        self.assertEqual(missing, {
            "synthetic:banking_accounts_deposits:W4", "synthetic:banking_accounts_deposits:W5",
            "synthetic:banking_customer_onboarding:W2", "synthetic:banking_customer_onboarding:W3",
            "synthetic:banking_customer_onboarding:W5", "synthetic:banking_customer_onboarding:W8",
            "synthetic:insurance_claims_intake:W9", "synthetic:manufacturing_purchase_to_pay:W9"})

    def test_json_prefix_alias_requires_matching_title(self):
        case = {"test_case_id": "AgentLongName_W1_TC2", "workflow": "W1", "title": "Standard account"}
        candidate = {"test_case_id": "Agent_W1_TC2", "title": "Standard account"}
        self.assertEqual(workflows.match_json_case(case, [("W1", candidate)]), candidate)
        candidate["title"] = "Different task"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            workflows.match_json_case(case, [("W1", candidate)])

    def test_ambiguous_json_case_is_rejected(self):
        case = {"test_case_id": "Agent_W1_TC2", "workflow": "W1", "title": "Account"}
        candidate = {"test_case_id": "Agent_W1_TC2", "title": "Account"}
        with self.assertRaisesRegex(ValueError, "found 2"):
            workflows.match_json_case(case, [("W1", candidate), ("W1", candidate)])

    def test_user_tools_are_not_reclassified_as_agent_tools(self):
        rows = [r for r in self.labels if r["domain"] == "telecom"]
        self.assertTrue(any("toggle_airplane_mode" in r["reference_user_tools"] for r in rows))
        self.assertFalse(any("toggle_airplane_mode" in r["reference_assistant_tools"] for r in rows))

    def test_changed_policy_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "labeling/workflow_sources", root / "labeling/workflow_sources")
            shutil.copy(ROOT / "labeling/workflow_rules.json", root / "labeling/workflow_rules.json")
            policy = root / "labeling/workflow_sources/tau2/policy/data/tau2/domains/retail/policy.md"
            policy.write_text("Changed policy")
            with self.assertRaisesRegex(ValueError, "Changed tau2 source snapshot"):
                workflows.build(root)

    def test_duplicate_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            workflows.index_unique([{"id": "1"}, {"id": "1"}], lambda r: r["id"], "task")

    def test_outputs_are_reproducible_and_match_the_saved_files(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            output = Path(directory)
            workflows.write_results(output, self.labels, self.catalog, self.evidence, copy.deepcopy(self.provenance))
            first = {p.name: p.read_bytes() for p in output.iterdir()}
            workflows.write_results(output, self.labels, self.catalog, self.evidence, copy.deepcopy(self.provenance))
            self.assertEqual(first, {p.name: p.read_bytes() for p in output.iterdir()})
            for name in first:
                if name == "checks.json":
                    # Environment versions can differ across teammates' machines.
                    continue
                self.assertEqual(first[name], (workflows.DEFAULT_OUTPUT / name).read_bytes(), name)


if __name__ == "__main__":
    unittest.main()
