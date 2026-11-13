"""Frozen pilot selection and offline reliability checks; never invent judge scores."""
import copy
import json
from statistics import mean

from .inputs import CaseBuilder, unique
from .rubric import ROOT, digest

CALIBRATION_VERSION = "design_calibration_v1"
THRESHOLDS = {"max_repeat_range": 10, "max_mean_repeat_range": 5,
              "max_perturbation_delta": 10, "min_control_pair_delta": 10}
PILOT_IDS = ["DigitalAccountOpening_DigitalAccountOpening_W1_TC1",
             "DigitalAccountOpeningAgent_W1_TC2",
             "InsuranceClaimsIntakeAndTriageAgent_W8_TC1"]


def pilot_cases(rows):
    byid = {r["task_id"]: r for r in rows if r["dataset"] == "synthetic"}
    if any(i not in byid for i in PILOT_IDS):
        raise ValueError("Frozen pilot IDs are missing from inventory")
    return [byid[i] for i in PILOT_IDS]


def control_cases():
    """Prepare separate controls, with expected comparisons withheld from the model."""
    path = ROOT / "docs/evaluation/numeric_design_controls_v1.json"
    document = json.loads(path.read_text())
    rows = []
    for index, item in enumerate(document["cases"]):
        b = CaseBuilder("validation_fixture", "control", item["id"], "fixture_two_steps", ROOT)
        b.add("scenario", item["scenario"], path, f"#/cases/{index}/scenario", "scenario")
        b.add("tools", document["tool_contracts"], path, "#/tool_contracts", "tool_contracts")
        b.add("endpoint", item["endpoint"], path, f"#/cases/{index}/endpoint", "completion_requirements")
        for si, text in enumerate(item["steps"]):
            sid = f"step_{si+1}"
            b.add(sid, text, path, f"#/cases/{index}/steps/{si}", "workflow_step")
            b.unit(sid, sid, "workflow_step")
        b.row["comparison_only"] = {"validation_fixture": True, "not_benchmark_data": True}
        rows.append(b.finish())
    reordered = copy.deepcopy(rows[0])
    reordered["task_id"] = "C04"
    reordered["payload"]["case_key"] = digest(["validation_fixture", "control", "C04"])[:24]
    reordered["payload"]["source_catalog"].reverse()
    reordered["input_sha256"] = digest(reordered["payload"])
    rows.append(reordered)
    return unique(rows)


def reliability(report):
    rows = [r for r in report["tasks"] if r["status"] == "scored" and r["n_planned_judgments"] >= 2]
    ranges = [r["repeat_score_range"] for r in rows]
    return {"version": CALIBRATION_VERSION, "thresholds": THRESHOLDS,
            "n_repeated_tasks": len(rows), "max_observed_repeat_range": max(ranges) if ranges else None,
            "mean_observed_repeat_range": mean(ranges) if ranges else None,
            "repeat_check": "not_run" if not ranges else "pass" if max(ranges) <= THRESHOLDS["max_repeat_range"] and mean(ranges) <= THRESHOLDS["max_mean_repeat_range"] else "fail",
            "perturbation_check": "not_run", "control_pair_check": "not_run", "held_out_check": "not_run",
            "go_no_go": "not_established", "independent_human_validation": False,
            "note": "A valid response or a three-task pilot is not full calibration. Repeat, controlled-pair, paraphrase/order and held-out source checks remain separate requirements."}


def compare_variants(baseline_report, variant_report, pairs, kind):
    """Explicit source-reviewed pairs; callers must not fit pairs to get a pass."""
    if kind not in {"perturbation", "controlled_complexity"}:
        raise ValueError("Unsupported calibration comparison")
    if (baseline_report.get("rubric_version") != variant_report.get("rubric_version") or
        baseline_report.get("protocol_fingerprints") != variant_report.get("protocol_fingerprints") or
        baseline_report.get("returned_models") != variant_report.get("returned_models")):
        raise ValueError("Calibration pairs must use the same rubric/model protocol")
    lookup_a = {r["case_key"]: r for r in baseline_report["tasks"]}
    lookup_b = {r["case_key"]: r for r in variant_report["tasks"]}
    results = []
    seen = set()
    for pair in pairs:
        a, b = pair["baseline_case_key"], pair["variant_case_key"]
        if (a, b) in seen or not pair.get("source_review_rationale", "").strip():
            raise ValueError("Pairs need unique identities and a prespecified source rationale")
        seen.add((a, b))
        first, second = lookup_a[a], lookup_b[b]
        usable = first["status"] == second["status"] == "scored"
        delta = second["score"]-first["score"] if usable else None
        passed = (abs(delta) <= THRESHOLDS["max_perturbation_delta"] if kind == "perturbation"
                  else delta >= THRESHOLDS["min_control_pair_delta"]) if usable else None
        results.append({**pair, "delta": delta, "passes_prespecified_tolerance": passed})
    return {"version": CALIBRATION_VERSION, "kind": kind, "pairs": results,
            "status": "not_run" if not results else "pass" if all(r["passes_prespecified_tolerance"] is True for r in results) else "needs_review",
            "independent_validation": False}
