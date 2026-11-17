import ast
import csv
import copy
import gzip
import json
import re
import unittest
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import patch
from openai import APIConnectionError

from baseline import run_synthetic_baseline as runner
from baseline.compute_difficulty import run as compute_empirical
from baseline.retry_synthetic_errors import retry
from baseline.synthetic_environment import (
    SyntheticSystemTools, evaluate_trajectory, execute, load_cases, reference_preflight, tools_for,
)


class ExampleCase(SyntheticSystemTools):
    expected_tool_calls = [
        {"name": "lookup", "tool_inputs": {"record_id": "A"}},
        {"name": "write", "tool_inputs": {"record_id": "A", "amount": 10}},
        {"name": "SUCCESS", "tool_inputs": {"message": "Done", "result_data": {"record_id": "A"}}},
    ]

    def lookup(self, record_id: str) -> dict:
        """Look up a record."""
        return {"record_id": record_id}

    def write(self, record_id: str, amount: int) -> dict:
        """Write an amount to a record."""
        if amount < 0:
            raise ValueError("Negative amount")
        return {"record_id": record_id, "amount": amount}


class SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.tools, _ = tools_for(ExampleCase())
        self.events = [execute(self.tools, {"name": c["name"], "arguments": c["tool_inputs"]})
                       for c in ExampleCase.expected_tool_calls]

    def score(self, events):
        return evaluate_trajectory(ExampleCase, events, {"write"})["reward"]

    def test_success_requires_reference_and_structured_outcome(self):
        self.assertEqual(self.score(self.events), 1)
        self.assertEqual(self.score(self.events[-1:]), 0)
        changed = copy.deepcopy(self.events)
        changed[-1]["arguments"]["result_data"]["record_id"] = "B"
        self.assertEqual(self.score(changed), 0)

    def test_wrong_write_and_unexpected_writes_fail(self):
        changed = copy.deepcopy(self.events)
        changed[1]["arguments"]["amount"] = 11
        self.assertEqual(self.score(changed), 0)
        extra = execute(self.tools, {"name": "write", "arguments": {"record_id": "B", "amount": 10}})
        self.assertEqual(self.score([extra, *self.events]), 0)

    def test_extra_reads_and_paraphrased_summary_allowed(self):
        changed = copy.deepcopy(self.events)
        changed[-1]["arguments"]["message"] = "The requested update is complete."
        self.assertEqual(self.score([self.events[0], *changed]), 1)

    def test_invalid_reference_is_unscored_and_tool_errors_are_not_success(self):
        self.assertIsNone(evaluate_trajectory(ExampleCase, self.events, {"write"}, ["invalid"])["reward"])
        event = execute(self.tools, {"name": "write", "arguments": {"record_id": "A", "amount": -1}})
        self.assertTrue(event["error"])
        self.assertEqual(self.score([self.events[0], event, self.events[-1]]), 0)
        self.assertTrue(execute(self.tools, {"name": "exec", "arguments": {}})["error"])

    def test_argument_schema_validation(self):
        self.assertTrue(execute(self.tools, {"name": "write", "arguments": {"record_id": "A"}})["error"])
        self.assertTrue(execute(self.tools, {"name": "write", "arguments": {"record_id": "A", "amount": 10, "extra": 1}})["error"])

    def test_invalid_references_are_not_labeled_as_infrastructure_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "trials.csv"
            path.write_text("domain,task_id,trial,reward,passed,evaluation_status\n"
                            "banking,a,0,,0,invalid_reference\n"
                            "banking,b,0,,0,infrastructure_error\n"
                            "banking,c,0,0,0,failed_reference\n")
            summary = compute_empirical([path], root / "scores")["ALL"]
            self.assertEqual(summary["tasks_with_invalid_references"], 1)
            self.assertEqual(summary["tasks_with_infra_errors"], 1)
            self.assertEqual(summary["n_scored"], 1)

    def test_parser_matches_fixed_tau_agent(self):
        tree = ast.parse((runner.ROOT / "baseline/react_agent.py").read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parse_action")
        namespace = {"json": json, "Optional": Optional, "ACTION_RE": runner.ACTION_RE}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "original_parser", "exec"), namespace)
        for text in ["", "hello", 'Thought: lookup\nAction: {"name":"lookup","arguments":{"record_id":"A"}}',
                     'Action: {"name":"respond","arguments":null}', 'Action: {"name":"lookup"} trailing text']:
            self.assertEqual(runner.parse_action(text), namespace["parse_action"](text))

    def test_saved_prompt_matches_fixed_tau_agent(self):
        tree = ast.parse((runner.ROOT / "baseline/react_agent.py").read_text())
        constants = [n for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id in {"REACT_INSTRUCTION", "SYSTEM_PROMPT"}
                             for t in n.targets)]
        namespace = {}
        exec(compile(ast.Module(body=constants, type_ignores=[]), "original_prompt", "exec"), namespace)
        expected = namespace["SYSTEM_PROMPT"].format(instruction=namespace["REACT_INSTRUCTION"],
                                                   domain_policy="{domain_policy}", tools="{tools}")
        self.assertEqual(runner.PROMPT.read_text().strip(), expected)

    def test_real_fixtures_and_references_are_classified(self):
        cases = load_cases()
        self.assertEqual(len(cases), 64)
        valid = invalid = 0
        for _, cls in cases:
            issues = reference_preflight(cls)
            tools, _ = tools_for(cls())
            events = [execute(tools, {"name": c["name"], "arguments": c.get("tool_inputs", {})})
                      for c in cls.expected_tool_calls]
            score = evaluate_trajectory(cls, events, set(tools), issues)
            if issues:
                invalid += 1
                self.assertIsNone(score["reward"])
            else:
                valid += 1
                self.assertEqual(score["reward"], 1)
        self.assertEqual((valid, invalid), (47, 17))

    def test_schemas_match_original_runner_on_reference_inputs(self):
        from langchain_core.tools import StructuredTool
        for _, case in load_cases():
            instance = case()
            tools, _ = tools_for(instance)
            for call in case.expected_tool_calls:
                method = getattr(instance, call["name"])
                original = StructuredTool.from_function(method, description=method.__doc__ or call["name"])
                def accepts(model):
                    try:
                        model.model_validate(call.get("tool_inputs", {}))
                        return True
                    except ValueError:
                        return False
                self.assertEqual(accepts(original.args_schema), accepts(tools[call["name"]][1]),
                                 (case.test_case_id, call["name"]))

    def test_trial_loop_with_fake_model_and_no_oracle_leakage(self):
        domain, cls = load_cases()[0]
        class FakeClient:
            index = 0
            def complete(self, messages, side):
                if side == "user":
                    self.assert_safe(messages[0]["content"])
                    text = "Please process my application."
                else:
                    self.assert_safe(messages[0]["content"])
                    call = cls.expected_tool_calls[self.index]
                    self.index += 1
                    text = "Thought: continue\nAction: " + json.dumps({"name": call["name"], "arguments": call["tool_inputs"]})
                return text, {"side": side, "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
            def assert_safe(self, prompt):
                if "expected_tool_calls" in prompt or "expected_state" in prompt:
                    raise AssertionError("Oracle leaked into prompt")
        row, trace = runner.trial(domain, cls, 0, 42, {"max_steps": 200}, FakeClient(), [], set())
        self.assertEqual(row["reward"], 1)
        self.assertEqual(row["agent_calls"], len(cls.expected_tool_calls))
        self.assertEqual(len(trace["tool_events"]), len(cls.expected_tool_calls))

    def test_api_error_has_no_numeric_reward(self):
        domain, cls = load_cases()[0]
        class BrokenClient:
            def complete(self, messages, side):
                raise APIConnectionError(request=None)
        row, trace = runner.trial(domain, cls, 0, 42, {"max_steps": 200}, BrokenClient(), [], set())
        self.assertIsNone(row["reward"])
        self.assertEqual(row["evaluation_status"], "infrastructure_error")
        self.assertEqual(trace["evaluation"]["error"]["type"], "APIConnectionError")

    def test_retry_preserves_original_errors_and_does_not_rerun_evaluated_trials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {"sources": {}, "config": {"max_concurrency": 1},
                        "planned_trials": 2, "completed_trials": 2}
            (root / "manifest.json").write_text(json.dumps(manifest))
            rows = []
            for index, status in enumerate(("failed_reference", "infrastructure_error")):
                row = dict.fromkeys(runner.COLUMNS, "")
                row.update(domain="banking", task_id="example", trial=index, seed=42,
                           reward=0 if index == 0 else "", passed=0, evaluation_status=status,
                           trace_file=f"trace{index}.json.gz")
                rows.append(row)
                (root / row["trace_file"]).write_bytes(gzip.compress(json.dumps({"original": index}).encode()))
            with (root / "trials.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=runner.COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            def replacement(*args):
                return {**rows[1], "reward": 0, "evaluation_status": "failed_reference"}, {"retried": True}
            with patch("baseline.retry_synthetic_errors.load_cases", return_value=[("banking", type("Case", (), {"test_case_id": "example"}))]), \
                 patch("baseline.retry_synthetic_errors.reference_preflight", return_value=[]), \
                 patch.object(runner, "CompletionClient"), patch.object(runner, "trial", side_effect=replacement) as call, \
                 patch.object(runner, "emit"):
                retry(root)
            self.assertEqual(call.call_count, 1)
            self.assertEqual(json.loads(gzip.decompress((root / "retries/round001/trace1.json.gz").read_bytes())), {"original": 1})
            self.assertEqual(json.loads(gzip.decompress((root / "trace0.json.gz").read_bytes())), {"original": 0})
            self.assertEqual(json.loads((root / "manifest.json").read_text())["evaluation_status_counts"], {"failed_reference": 2})


if __name__ == "__main__":
    unittest.main()
