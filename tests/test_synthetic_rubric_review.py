"""Offline review evidence must not be mistaken for independent outcome grading."""
import json
import tempfile
import unittest
from pathlib import Path

from baseline.review_synthetic_rubric import (
    DEFAULT_OUT, ROOT, build_review, final_user_markers, replay_reference, select_sample,
)


class MockReference:
    test_case_id = "review_validation_only"
    expected_tool_calls = [{"name": "operation", "tool_inputs": {"amount": 1}}]

    def operation(self, amount: int) -> dict:
        # It executes successfully but the simulated business outcome is a failure.
        return {"status": "failed"}


class InvalidTypedReference(MockReference):
    expected_tool_calls = [{"name": "operation", "tool_inputs": {"amount": None}},
                           {"name": "operation", "tool_inputs": {"amount": 1}}]


class SyntheticRubricReviewTests(unittest.TestCase):
    def test_passing_reference_replay_does_not_verify_business_outcome(self):
        result = replay_reference(MockReference)
        self.assertEqual(result["self_reference_evaluation"]["status"], "passed_reference")
        self.assertTrue(result["terminal_claim_is_not_independent_outcome_evidence"])
        self.assertEqual(result["errors"], [])

    def test_validation_failure_is_distinguished_from_direct_mock_acceptance(self):
        result = replay_reference(InvalidTypedReference)
        self.assertEqual(result["reference_calls"], 2)
        self.assertEqual(result["calls_without_execution_error"], 1)
        self.assertEqual(result["self_reference_evaluation"]["status"], "invalid_reference")
        self.assertEqual(result["errors"][0]["direct_mock_invocation"]["status"],
                         "returned_without_exception")

    def test_stop_marker_comes_from_final_user_message_not_agent_claim(self):
        trace = {"conversation": [{"role": "user", "content": "###STOP###"},
                                  {"role": "user", "content": "###OUT-OF-SCOPE###"},
                                  {"role": "assistant", "content": "SUCCESS ###STOP###"}]}
        self.assertEqual(final_user_markers(trace), ["###OUT-OF-SCOPE###"])

    def test_sampling_is_deterministic_and_deduplicates_terminal_examples(self):
        def row(task, status, reason="user_stop"):
            return {"domain": "sample", "task_id": task, "trial": "0",
                    "evaluation_status": status, "termination_reason": reason,
                    "trace_file": task}
        rows = [row("invalid", "invalid_reference"),
                row("active", "failed_reference", "workflow_terminal"),
                row("quiet", "failed_reference")]
        traces = {"invalid": {"tool_events": []}, "active": {"tool_events": [1, 2]},
                  "quiet": {"tool_events": []}}
        selected = select_sample(rows, traces)
        self.assertEqual([r["task_id"] for r in selected], ["invalid", "active"])
        self.assertEqual(selected, select_sample(list(reversed(rows)), traces))

    def test_output_cannot_overwrite_historical_results_or_supplied_data(self):
        for path in (ROOT, ROOT / "data", ROOT / "results", ROOT / "results/framework",
                     ROOT / "results/baseline/v2_synthetic_full"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                build_review(output_dir=path)

    def test_full_offline_review_preserves_scores_and_matches_saved_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            summary = build_review(output_dir=directory)
            self.assertEqual(summary["reference_replay_counts"],
                             {"passed_reference": 47, "invalid_reference": 17})
            self.assertEqual(summary["termination_counts"],
                             {"user_stop": 254, "workflow_terminal": 2})
            self.assertEqual(summary["sample_categories"], 7)
            sample = json.loads((Path(directory) / "sample.json").read_text())
            self.assertEqual(len(sample), 16)
            self.assertTrue(all(r["new_reward"] is None and
                                r["human_adjudication"] == "pending" for r in sample))
            # Regeneration is deterministic from the same saved evidence.
            for name in ("summary.json", "sample.json", "reference_replay.json", "input_manifest.json"):
                self.assertEqual((Path(directory) / name).read_bytes(), (DEFAULT_OUT / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
