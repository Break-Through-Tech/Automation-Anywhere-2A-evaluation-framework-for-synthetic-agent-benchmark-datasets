"""Offline regression checks. Stub judgments below are NOT measured model scores."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from difficulty.design import inputs, judge, reporting, rubric, calibration, crosscheck


def fixture_case(root, name="case", dataset="synthetic"):
    source = Path(root) / "source"
    source.mkdir(exist_ok=True)
    p = source / "requirements.txt"
    p.write_text("Look up the input; apply the stated rule; record the result. Complete the requested record.")
    b = inputs.CaseBuilder(dataset, "fixture", name, "W1", source)
    b.add("S", p.read_text(), p, "whole fixture", "completion_requirements")
    b.unit("U1", "S", "workflow_step")
    b.row["comparison_only"] = {"class_tag": "hard", "difficulty_reasoning": "withheld tag rationale"}
    return b.finish()


def stub_judgment(row, level=2):
    evidence = [{"source_id": "S", "excerpt": "apply the stated rule"}]
    return {"version": rubric.OUTPUT_VERSION, "case_key": row["payload"]["case_key"], "status": "scored",
            "units": [{"unit_id": "U1", "applicability": "required", "applicability_rationale": "Explicit required operation",
                       "evidence": evidence, "levels": dict.fromkeys(rubric.STEP_DIMENSIONS, level), "rationale": "Offline test rating only"}],
            "dimensions": {k: {"level": level, "rationale": "Offline test rating only", "evidence": evidence} for k in rubric.DIMENSIONS},
            "overall_score": level * 25, "intended_endpoint": {"description": "Requested record completed", "evidence": evidence},
            "dependency_reasoning": "Rule application precedes recording", "score_rationale": "Offline fixture only, not a real judgment",
            "uncertainties": [], "source_quality_flags": [], "unscorable_reason": ""}


class FakeResponse:
    def __init__(self, value):
        self.output_text = json.dumps(value)
    def model_dump(self, **kwargs):
        return {"status": "completed", "model": "offline-stub-model", "id": "offline-stub-response",
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": self.output_text}]}]}


def fake_client(values):
    client = Mock()
    client.responses.create.side_effect = [v if isinstance(v, Exception) else FakeResponse(v) for v in values]
    return client


class NumericRubricTests(unittest.TestCase):
    def test_frozen_arithmetic_is_equal_weight_and_not_rank(self):
        self.assertEqual(rubric.score(dict.fromkeys(rubric.DIMENSIONS, 0)), 0)
        self.assertEqual(rubric.score(dict.fromkeys(rubric.DIMENSIONS, 4)), 100)
        self.assertEqual(rubric.score(dict.fromkeys(rubric.DIMENSIONS, 2)), 50)
        self.assertIn(rubric.VERSION, rubric.rubric_text())
        for bad in [dict.fromkeys(rubric.DIMENSIONS, True), dict.fromkeys(rubric.DIMENSIONS, 4.0), dict.fromkeys(rubric.DIMENSIONS, 5), {}]:
            with self.assertRaises(ValueError):
                rubric.score(bad)

    def test_clean_hides_label_fields_and_class_ids_not_semantic_values(self):
        value = {"difficulty": "hard", "difficulty_reasoning": "label rationale", "class_name": "TestCase_hard",
                 "data": [{"tier": "premium", "deposit": 5000, "note": "Difficulty: hard; TestCase_hard"}]}
        clean = inputs.clean(value, ["TestCase_hard"])
        self.assertNotIn("difficulty", clean)
        self.assertNotIn("hard", json.dumps(clean))
        self.assertEqual(clean["data"][0]["deposit"], 5000)

    def test_nested_customer_names_are_not_tool_names(self):
        result = inputs.tool_definitions({"system_tools": [{"name": "SUCCESS", "args": []}],
                                          "domain_tools": [{"name": "lookup", "args": [{"name": "customer"}]}]})
        self.assertEqual(set(result), {"SUCCESS", "lookup"})
        with self.assertRaises(ValueError):
            inputs.tool_definitions([{"name": "x", "args": []}, {"name": "x", "args": []}])

    def test_control_sources_have_equal_steps_and_no_expected_scores_in_payload(self):
        rows = calibration.control_cases()
        self.assertEqual([len(r["payload"]["units"]) for r in rows], [2, 2, 2, 2])
        self.assertNotEqual(rows[0]["payload"]["source_catalog"], rows[1]["payload"]["source_catalog"])
        self.assertEqual(rows[0]["payload"]["source_catalog"], list(reversed(rows[3]["payload"]["source_catalog"])))
        self.assertTrue(all("minimum_gap" not in json.dumps(r["payload"]) for r in rows))


class NumericAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.synthetic = inputs.synthetic_cases()
        cls.tau = inputs.tau_cases()

    def test_all_tasks_keep_canonical_ids_and_immutable_sources(self):
        self.assertEqual(len(self.synthetic), 64)
        self.assertEqual(len(self.tau), 278)
        self.assertEqual(len({r["domain"] for r in self.synthetic}), 7)
        self.assertFalse([r for r in self.synthetic if r["preflight_errors"]])
        inputs.verify_sources(self.synthetic + self.tau)

    def test_label_information_does_not_enter_judge_visible_payloads(self):
        for row in self.synthetic:
            text = json.dumps(row["payload"])
            self.assertNotIn(row["task_id"], text)
            self.assertNotIn("class_tag", text)
            self.assertNotIn("difficulty_reasoning", text)
            self.assertNotIn("class_name", text)
            self.assertIn(row["comparison_only"]["class_tag"], {"easy", "medium", "hard"})
            self.assertFalse(any("path" in s or "locator" in s for s in row["payload"]["source_catalog"]))

    def test_same_workflow_scenarios_remain_distinct_and_exit_design_is_present(self):
        a, b, _ = calibration.pilot_cases(self.synthetic)
        self.assertEqual(a["workflow_id"], b["workflow_id"])
        steps = lambda r: [s for s in r["payload"]["source_catalog"] if s["kind"] == "workflow_step"]
        self.assertEqual(steps(a), steps(b))
        self.assertNotEqual(a["input_sha256"], b["input_sha256"])
        for row in (a, b):
            catalog = {s["source_id"]: s for s in row["payload"]["source_catalog"]}
            self.assertIn("escalation", catalog["exit_conditions"]["text"])
            self.assertIn("failure", catalog["exit_conditions"]["text"])
            self.assertIn("global_plan", catalog)
            self.assertIn("tool_contracts", catalog)

    def test_native_contracts_policies_and_missing_completion_are_explicit(self):
        telecom = next(r for r in self.tau if r["domain"] == "telecom")
        kinds = {s["source_id"] for s in telecom["payload"]["source_catalog"]}
        self.assertTrue({"policy_1", "policy_2", "tools_assistant", "tools_user", "completion_design"}.issubset(kinds))
        self.assertIsNone(telecom["workflow_id"])
        self.assertEqual(telecom["comparison_only"], {})
        self.assertTrue(all(u["kind"] != "milestone" for u in telecom["payload"]["units"]))
        blocked = [r for r in self.tau if r["preflight_errors"]]
        self.assertEqual([(r["domain"], r["task_id"]) for r in blocked], [("retail", "57")])


class NumericValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.row = fixture_case(self.tmp.name)
        self.good = stub_judgment(self.row)

    def test_valid_fixture_and_strict_rejections(self):
        judge.validate_judgment(self.good, self.row)
        changes = [lambda x: x.update(overall_score=51), lambda x: x.update(overall_score=True),
                   lambda x: x.update(case_key="another"), lambda x: x.update(extra="field"),
                   lambda x: x.update(units=[]), lambda x: x["dimensions"]["reasoning"].update(level=1),
                   lambda x: x["dimensions"]["tool_use"].update(evidence=[]),
                   lambda x: x["units"][0]["evidence"][0].update(excerpt="made up text"),
                   lambda x: x["units"][0].update(applicability="optional_not_selected"),
                   lambda x: x.update(dependency_reasoning="")]
        for change in changes:
            value = copy.deepcopy(self.good)
            change(value)
            with self.assertRaises(Exception):
                judge.validate_judgment(value, self.row)

    def test_unscorable_does_not_have_a_numeric_score(self):
        value = copy.deepcopy(self.good)
        value.update(status="unscorable", overall_score=None, units=[], unscorable_reason="Missing necessary context",
                     source_quality_flags=["missing_context"])
        for dimension in value["dimensions"].values():
            dimension["level"] = None
        judge.validate_judgment(value, self.row)
        value["overall_score"] = 100
        with self.assertRaises(ValueError):
            judge.validate_judgment(value, self.row)

    def test_api_schema_rejects_numeric_context_levels_before_local_validation(self):
        value = copy.deepcopy(self.good)
        value['units'][0]['applicability'] = 'context'
        value['units'][0]['levels'] = dict.fromkeys(rubric.STEP_DIMENSIONS, 0)
        with self.assertRaises(Exception):
            judge.Draft202012Validator(rubric.response_schema()).validate(value)
        value['units'][0]['levels'] = dict.fromkeys(rubric.STEP_DIMENSIONS, None)
        judge.Draft202012Validator(rubric.response_schema()).validate(value)

    def test_api_schema_requires_numeric_levels_for_active_units(self):
        value = copy.deepcopy(self.good)
        value['units'][0]['levels']['reasoning'] = None
        with self.assertRaises(Exception):
            judge.Draft202012Validator(rubric.response_schema()).validate(value)

    def test_same_task_cross_reference_is_flagged_not_rejected(self):
        b = inputs.CaseBuilder("synthetic", "fixture", "other", "W1", Path(self.tmp.name) / "source")
        source = Path(self.tmp.name) / "source/requirements.txt"
        b.add("S", source.read_text(), source, "original")
        b.add("T", "Other independent source", source, "separate")
        b.unit("U1", "T", "workflow_step")
        row = b.finish()
        value = stub_judgment(row)
        judge.validate_judgment(value, row)
        self.assertEqual(judge.evidence_diagnostics(value, row)[0]["unit_id"], "U1")
        value["units"][0]["evidence"][0]["excerpt"] = "Invented quotation"
        with self.assertRaisesRegex(ValueError, "absent"):
            judge.validate_judgment(value, row)

    def test_exact_quotes_allow_decoded_json_strings_not_fuzzy_or_joined_text(self):
        text = json.dumps({"tool": {"doc": "First line\nsecond line."}, "other": "Third line."})
        self.assertTrue(judge.quotation_in_source("First line\nsecond line.", text))
        self.assertFalse(judge.quotation_in_source("First line second line.", text))
        self.assertFalse(judge.quotation_in_source("second line.Third line.", text))
        self.assertFalse(judge.quotation_in_source(" \n", text))


class NumericRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.row = fixture_case(self.root)

    def packet(self, rows=None, repeats=1, name="packet", model="offline-model"):
        out = self.root / name
        judge.prepare_packet(rows or [self.row], out, model, repeats)
        return out

    def test_request_schema_limits_units_to_the_supplied_case(self):
        packet = self.packet()
        manifest, rows, requests = judge.load_packet(packet)
        schema = requests[0]["api_request"]["text"]["format"]["schema"]
        self.assertEqual(manifest["schema_version"], rubric.SCHEMA_VERSION)
        value = stub_judgment(self.row)
        judge.Draft202012Validator(schema).validate(value)
        value["units"][0]["unit_id"] = "invented_eligibility_check"
        with self.assertRaises(Exception):
            judge.Draft202012Validator(schema).validate(value)
        with self.assertRaisesRegex(ValueError, "Unknown or duplicate"):
            judge.validate_judgment(value, self.row)
        empty_schema = rubric.response_schema([])
        self.assertEqual(empty_schema["properties"]["units"]["maxItems"], 0)

    def test_no_client_construction_or_api_without_explicit_authorization(self):
        packet = self.packet()
        with patch("openai.OpenAI", side_effect=AssertionError("Must not construct a client")):
            with self.assertRaises(PermissionError):
                judge.run_packet(packet)
        self.assertFalse((packet / "raw").exists())
        self.assertEqual(judge.load_packet(packet)[0]["api_calls_during_preparation"], 0)
        api = judge.load_packet(packet)[2][0]["api_request"]
        self.assertNotIn("hard", api["input"][1]["content"])
        self.assertEqual(api["text"]["format"]["type"], "json_schema")

    def test_cache_resumption_does_not_repeat_completed_calls(self):
        packet = self.packet()
        client = fake_client([stub_judgment(self.row)])
        judge.run_packet(packet, authorize_paid=True, client=client)
        audit = judge.run_packet(packet, authorize_paid=True, client=client)
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertEqual(audit["new_api_calls"], 0)
        self.assertEqual(reporting.aggregate([self.row], [packet])["datasets"]["synthetic"]["mean"], 50)

    def test_request_source_and_raw_result_tampering_are_rejected(self):
        packet = self.packet()
        client = fake_client([stub_judgment(self.row)])
        judge.run_packet(packet, authorize_paid=True, client=client)
        req = judge.load_packet(packet)[2][0]
        p = packet / "results" / (req["request_id"] + ".json")
        changed = json.loads(p.read_text())
        changed["judgment"] = stub_judgment(self.row, 3)
        p.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, "raw response"):
            reporting.aggregate([self.row], [packet])
        (self.root / "source/requirements.txt").write_text("Changed")
        with self.assertRaisesRegex(ValueError, "Changed"):
            judge.load_packet(packet)

    def test_request_and_rubric_fingerprints_are_checked(self):
        packet = self.packet()
        p = packet / "requests.json"
        original = p.read_text()
        p.write_text(original.replace("offline-model", "different-model"))
        with self.assertRaisesRegex(ValueError, "changed"):
            judge.load_packet(packet)
        p.write_text(original)
        with patch.object(judge, "rubric_text", return_value="Changed rubric"):
            with self.assertRaisesRegex(ValueError, "changed"):
                judge.load_packet(packet)

    def test_first_api_failure_stops_and_cannot_be_automatically_retried(self):
        other = fixture_case(self.root, "second")
        packet = self.packet([self.row, other])
        client = fake_client([RuntimeError("offline simulated failure"), stub_judgment(other)])
        result = judge.run_packet(packet, authorize_paid=True, client=client)
        self.assertEqual(result["stopped_reason"], "failure_requires_diagnosis")
        self.assertEqual(client.responses.create.call_count, 1)
        with self.assertRaisesRegex(ValueError, "Previous"):
            judge.run_packet(packet, authorize_paid=True, client=client)

    def test_first_format_failure_stops(self):
        other = fixture_case(self.root, "second")
        bad = stub_judgment(self.row)
        bad["overall_score"] = 99
        packet = self.packet([self.row, other])
        client = fake_client([bad, stub_judgment(other)])
        result = judge.run_packet(packet, authorize_paid=True, client=client)
        self.assertEqual(result["new_api_calls"], 1)
        self.assertEqual(result["stopped_reason"], "failure_requires_diagnosis")
        statuses = [r["status"] for r in reporting.aggregate([self.row, other], [packet])["tasks"]]
        self.assertEqual(statuses, ["judge_error", "pending"])

    def test_interrupted_intent_is_not_replayed_and_limit_is_bounded(self):
        packet = self.packet()
        (packet / "intents").mkdir()
        req = judge.load_packet(packet)[2][0]
        judge.write_json(packet / "intents" / (req["request_id"] + ".json"), {"interrupted": True})
        client = fake_client([])
        with self.assertRaisesRegex(ValueError, "Interrupted"):
            judge.run_packet(packet, authorize_paid=True, client=client)
        client.responses.create.assert_not_called()
        for limit in (0, 4, True):
            with self.assertRaises(ValueError):
                judge.run_packet(packet, authorize_paid=True, max_calls=limit, client=client)

    def test_preflight_block_does_not_spend_and_is_separate_from_failure(self):
        self.row["preflight_errors"] = ["missing_tool_definition"]
        packet = self.packet()
        client = fake_client([])
        result = judge.run_packet(packet, authorize_paid=True, client=client)
        client.responses.create.assert_not_called()
        self.assertEqual(result["new_api_calls"], 0)
        report = reporting.aggregate([self.row], [packet])
        self.assertEqual(report["tasks"][0]["status"], "source_preflight_blocked")
        self.assertIsNone(report["datasets"]["synthetic"]["mean"])

    def test_repeat_calls_are_averaged_per_task_before_dataset_mean(self):
        other = fixture_case(self.root, "second")
        first = self.packet(repeats=2)
        judge.run_packet(first, authorize_paid=True, client=fake_client([stub_judgment(self.row, 1), stub_judgment(self.row, 3)]))
        second = self.packet([other], name="second-packet")
        judge.run_packet(second, authorize_paid=True, client=fake_client([stub_judgment(other, 1)]))
        report = reporting.aggregate([self.row, other], [first, second])
        self.assertEqual(report["datasets"]["synthetic"]["mean"], 37.5)
        self.assertEqual(calibration.reliability(report)["repeat_check"], "fail")
        self.assertEqual(report, reporting.aggregate([self.row, other], [first, second]))
        self.assertIsNone(reporting.aggregate([self.row], [self.packet(repeats=2, name="pending")])["datasets"]["synthetic"]["mean"])

    def test_missing_repeats_and_unscorable_are_not_success_only_average(self):
        packet = self.packet(repeats=2)
        judge.run_packet(packet, authorize_paid=True, max_calls=1, client=fake_client([stub_judgment(self.row)]))
        report = reporting.aggregate([self.row], [packet])
        self.assertIsNone(report["tasks"][0]["score"])
        self.assertEqual(report["tasks"][0]["status"], "pending")
        value = stub_judgment(self.row)
        value.update(status="unscorable", overall_score=None, units=[], unscorable_reason="Missing sources", source_quality_flags=["missing_sources"])
        for d in value["dimensions"].values():
            d["level"] = None
        judge.run_packet(packet, authorize_paid=True, client=fake_client([value]))
        report = reporting.aggregate([self.row], [packet])
        self.assertEqual(report["tasks"][0]["status"], "unscorable")
        self.assertIsNone(report["tasks"][0]["score"])

    def test_uniform_scores_stop_for_inspection_and_do_not_assert_failure(self):
        rows = [fixture_case(self.root, str(i)) for i in range(4)]
        packet = self.packet(rows)
        client = fake_client([stub_judgment(r) for r in rows])
        result = judge.run_packet(packet, authorize_paid=True, client=client)
        self.assertEqual(client.responses.create.call_count, 3)
        self.assertIn("require_inspection_not_automatic_failure", result["stopped_reason"])
        with self.assertRaisesRegex(ValueError, "Previous stop gate"):
            judge.run_packet(packet, authorize_paid=True, client=client)
        self.assertEqual(client.responses.create.call_count, 3)

    def test_source_only_framework_mode_does_not_embed_or_run_trials(self):
        import run_all
        p = self.root / "inventory.json"
        p.write_text(json.dumps([self.row]))
        args = run_all.parser().parse_args(["--difficulty-mode", "source-only", "--design-inventory", str(p),
                                           "--output-dir", str(self.root / "framework")])
        with patch.object(run_all, "embed", side_effect=AssertionError("No embeddings")), \
             patch.object(run_all, "load_inputs", side_effect=AssertionError("No legacy task/trial loading")):
            result = run_all.evaluate(args)
        self.assertIsNone(result["datasets"]["synthetic"]["mean"])

    def test_mixed_model_protocols_and_duplicate_packets_are_rejected(self):
        other = fixture_case(self.root, "second")
        first = self.packet()
        second = self.packet([other], name="other-packet", model="other-model")
        with self.assertRaisesRegex(ValueError, "mixed"):
            reporting.aggregate([self.row, other], [first, second])
        with self.assertRaisesRegex(ValueError, "multiple packets"):
            reporting.aggregate([self.row], [first, first])

    def test_dataset_summaries_keep_missingness_and_all_missing_unavailable(self):
        other = fixture_case(self.root, "second")
        packet = self.packet()
        judge.run_packet(packet, authorize_paid=True, client=fake_client([stub_judgment(self.row, 1)]))
        report = reporting.aggregate([self.row, other], [packet])
        summary = report["datasets"]["synthetic"]
        self.assertEqual((summary["mean"], summary["coverage"], summary["mean_label"]), (25, .5, "scored_subset_mean"))
        empty = reporting.aggregate([other])["datasets"]["synthetic"]
        self.assertIsNone(empty["mean"])
        self.assertEqual(empty["mean_label"], "unavailable")
        out = self.root / "report"
        reporting.write_report(report, out)
        self.assertEqual(len((out / "task_scores.csv").read_text().splitlines()), 3)
        with self.assertRaises(ValueError):
            reporting.write_report(report, out)

    def test_crosschecks_have_no_false_correlations_or_invented_tau_tags(self):
        self.assertIsNone(crosscheck.association([(1, 1)] * 3)["rho"])
        report = reporting.aggregate([self.row])
        compared = crosscheck.compare(report, [self.row])
        self.assertEqual(compared["status"], "prepared_no_judgments_yet")
        self.assertEqual(compared["tasks"][0]["supplied_tag_comparison_only"], "hard")
        self.assertEqual(calibration.reliability(report)["repeat_check"], "not_run")


if __name__ == "__main__":
    unittest.main()
