import json
import unittest

from difficulty.llm_judge import (
    build_system_prompt,
    compute_judge_difficulty,
    load_rubric,
    _parse_judgment,
)


class LlmJudgeRubricTests(unittest.TestCase):
    def setUp(self):
        self.milestones = [{"step": 1, "description": "Complete the requested operation"}]

    def test_rubric_is_versioned_and_used_in_prompt(self):
        text, version, status = load_rubric()
        self.assertEqual(version, "synthetic_milestones_v0.1_draft")
        self.assertIn("proposed", status)
        prompt = build_system_prompt(text)
        self.assertIn("REFERENCE RUBRIC", prompt)
        self.assertIn("Unverifiable", prompt)

    def test_judgment_retains_evidence_and_supports_unverifiable(self):
        response = {
            "task_judgment": "unverifiable",
            "task_rationale": "The trace does not show the final state.",
            "task_evidence": [],
            "task_contradictions": [],
            "milestones": [{
                "step": 1,
                "applicable": True,
                "material": True,
                "applicability_basis": "It is required by the task.",
                "judgment": "unverifiable",
                "rationale": "No operation result is present.",
                "evidence": [],
                "contradictions": [],
            }],
        }
        parsed = _parse_judgment(json.dumps(response), self.milestones)
        self.assertEqual(parsed["task_judgment"], "unverifiable")
        self.assertEqual(parsed["milestones"][0]["judgment"], "unverifiable")

    def test_met_judgment_requires_evidence(self):
        response = {
            "task_judgment": "met",
            "task_rationale": "The task was completed.",
            "task_evidence": [],
            "task_contradictions": [],
            "milestones": [{
                "step": 1,
                "applicable": True,
                "material": True,
                "applicability_basis": "It is required by the task.",
                "judgment": "met",
                "rationale": "The task was completed.",
                "evidence": [],
                "contradictions": [],
            }],
        }
        with self.assertRaisesRegex(ValueError, "requires evidence"):
            _parse_judgment(json.dumps(response), self.milestones)

    def test_difficulty_excludes_unverifiable_and_invalid_trials(self):
        rows = [
            {"domain": "sample", "task_id": "task-1", "status": "valid", "task_judgment": "met"},
            {"domain": "sample", "task_id": "task-1", "status": "valid", "task_judgment": "unmet"},
            {"domain": "sample", "task_id": "task-1", "status": "valid", "task_judgment": "unverifiable"},
            {"domain": "sample", "task_id": "task-1", "status": "invalid", "task_judgment": "unverifiable"},
        ]
        result = compute_judge_difficulty(rows)[0]
        self.assertEqual(result["n_eligible"], 2)
        self.assertEqual(result["n_unverifiable"], 1)
        self.assertEqual(result["n_invalid"], 1)
        self.assertEqual(result["difficulty"], 0.5)


if __name__ == "__main__":
    unittest.main()
