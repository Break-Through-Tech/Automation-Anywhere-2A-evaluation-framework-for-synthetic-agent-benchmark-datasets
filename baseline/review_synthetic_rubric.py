"""Build offline evidence for issue #45; never assign new outcome rewards.

python -m baseline.review_synthetic_rubric
Outputs: results/rubric_review/v1/. No model or network calls are made.
"""
import argparse
import ast
import contextlib
import copy
import csv
import gzip
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from baseline.synthetic_environment import (
    ROOT, evaluate_trajectory, execute, load_cases, tools_for,
)

MARKERS = ("###STOP###", "###TRANSFER###", "###OUT-OF-SCOPE###")
DEFAULT_RUN = ROOT / "results/baseline/v2_synthetic_full"
DEFAULT_OUT = ROOT / "results/rubric_review/v1"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def final_user_markers(trace):
    message = next((m["content"] for m in reversed(trace["conversation"])
                    if m["role"] == "user"), "")
    return [marker for marker in MARKERS if marker in message]


def select_sample(rows, traces):
    """Two purposive examples per category, plus every workflow-terminal attempt."""
    selected = []
    for domain in sorted({r["domain"] for r in rows}):
        group = sorted((r for r in rows if r["domain"] == domain),
                       key=lambda r: (r["task_id"], int(r["trial"])))
        invalid = [r for r in group if r["evaluation_status"] == "invalid_reference"]
        evaluated = [r for r in group if r["evaluation_status"] == "failed_reference"]
        if not evaluated:
            raise ValueError(f"No reference-failed attempts for sample in {domain}")
        def count(row):
            return len(traces[row["trace_file"]]["tool_events"])
        selected.extend([invalid[0] if invalid else min(evaluated, key=count),
                         max(evaluated, key=count)])
    selected.extend(r for r in rows if r["termination_reason"] == "workflow_terminal")
    unique = {}
    for row in selected:
        unique.setdefault((row["domain"], row["task_id"], int(row["trial"])), row)
    return list(unique.values())


def source_locations(path, class_name):
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    locations = {"class": node.lineno}
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    locations[target.id] = item.lineno
    return locations


def replay_reference(case):
    """Replay supplied calls verbatim, including after errors, for diagnostics only."""
    tools, _ = tools_for(case())
    events, errors = [], []
    for index, call in enumerate(case.expected_tool_calls):
        event = execute(tools, {"name": call["name"], "arguments": call.get("tool_inputs", {})})
        events.append(event)
        if event["error"]:
            # Direct invocation isolates validation from mock implementation behavior.
            # Raw acceptance does NOT establish compatibility with the original runner.
            raw_tools, _ = tools_for(case())
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    raw_tools[call["name"]][0](**copy.deepcopy(call.get("tool_inputs", {})))
                native = {"status": "returned_without_exception"}
            except Exception as exc:
                native = {"status": "raised", "error": type(exc).__name__, "message": str(exc)}
            errors.append({"reference_call_index": index, "tool": call["name"],
                           "adapter_error": event["output"], "direct_mock_invocation": native})
    oracle = evaluate_trajectory(case, events, set(), errors)
    return {"task_id": case.test_case_id, "reference_calls": len(events),
            "calls_without_execution_error": sum(not e["error"] for e in events),
            "errors": errors, "self_reference_evaluation": oracle,
            "executed_names": [e["name"] for e in events],
            "terminal_claim_is_not_independent_outcome_evidence": True}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def build_review(run_dir=DEFAULT_RUN, output_dir=DEFAULT_OUT):
    run_dir, output_dir = Path(run_dir).resolve(), Path(output_dir).resolve()
    # Outputs are intentionally isolated from supplied data and historical results.
    protected = [ROOT / "data", ROOT / "results/baseline", ROOT / "results/archive",
                 ROOT / "results/experiments", ROOT / "results/framework"]
    if output_dir == ROOT or any(output_dir == p or output_dir.is_relative_to(p)
                                 or p.is_relative_to(output_dir) for p in protected):
        raise ValueError("Review output must not overlap source data or saved benchmark evidence")
    with (run_dir / "trials.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    traces, inputs = {}, {}
    for row in rows:
        path = (run_dir / row["trace_file"]).resolve()
        if not path.is_relative_to(run_dir):
            raise ValueError("Trace must be inside its saved run")
        trace = json.loads(gzip.decompress(path.read_bytes()))
        if (trace["domain"], trace["task_id"], int(trace["trial"])) != (
                row["domain"], row["task_id"], int(row["trial"])):
            raise ValueError("Trace identity does not match trial CSV")
        recorded_reward = trace["evaluation"]["reward"]
        if (row["evaluation_status"] != trace["evaluation"]["status"] or
                row["reward"] != ("" if recorded_reward is None else str(recorded_reward))):
            raise ValueError("Trace evaluation does not match trial CSV")
        traces[row["trace_file"]] = trace
        inputs[str(path.relative_to(ROOT))] = sha256(path)
    keys = [(r["domain"], r["task_id"], int(r["trial"])) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate trial identities")
    cases = {(d, c.test_case_id): c for d, c in load_cases()}
    if set((r["domain"], r["task_id"]) for r in rows) != set(cases):
        raise ValueError("Saved run must cover the original task inventory exactly")
    replays = [{"domain": d, **replay_reference(c)} for (d, _), c in sorted(cases.items())]
    saved_preflight = json.loads((run_dir / "reference_preflight.json").read_text())
    if {(r["domain"], r["task_id"]) for r in replays if r["errors"]} != {
            (r["domain"], r["task_id"]) for r in saved_preflight}:
        raise ValueError("Current reference failures differ from the saved preflight")
    sample = []
    for row in select_sample(rows, traces):
        domain, task = row["domain"], row["task_id"]
        trace = traces[row["trace_file"]]
        case = cases[(domain, task)]
        source = ROOT / "data" / domain / "test_cases.py"
        expected = trace["evaluation"].get("missing_tool")
        sample.append({"review_id": f"R{len(sample)+1:02d}", "domain": domain,
                       "task_id": task, "trial": int(row["trial"]),
                       "trace_file": str((run_dir / row["trace_file"]).relative_to(ROOT)),
                       "trace_sha256": inputs[str((run_dir / row["trace_file"]).relative_to(ROOT))],
                       "source_file": str(source.relative_to(ROOT)),
                       "source_lines": source_locations(source, case.__name__),
                       "milestones": case.milestones,
                       "original_evaluation": trace["evaluation"],
                       "termination_reason": row["termination_reason"],
                       "final_user_markers": final_user_markers(trace),
                       "events": [{"index": i, "name": e["name"], "error": e["error"]}
                                  for i, e in enumerate(trace["tool_events"])],
                       "original_missing_tool_also_present_at_event_indices": [
                           i for i, e in enumerate(trace["tool_events"]) if e["name"] == expected],
                       "human_adjudication": "pending", "new_reward": None})
    stop_counts = Counter(marker for r in rows if r["termination_reason"] == "user_stop"
                          for marker in final_user_markers(traces[r["trace_file"]]))
    summary = {"rubric_version": "synthetic_milestones_v0.1_draft", "issue": 45,
               "status": "draft_pending_team_adjudication", "recorded_attempts": len(rows),
               "tasks": len(cases), "original_evaluation_counts": dict(Counter(r["evaluation_status"] for r in rows)),
               "termination_counts": dict(Counter(r["termination_reason"] for r in rows)),
               "user_stop_marker_counts": dict(stop_counts),
               "user_stop_without_known_marker": sum(r["termination_reason"] == "user_stop" and not final_user_markers(traces[r["trace_file"]]) for r in rows),
               "reference_replay_counts": dict(Counter(r["self_reference_evaluation"]["status"] for r in replays)),
               "reference_errors_by_execution_layer": dict(Counter(
                   e["direct_mock_invocation"]["status"] for r in replays for e in r["errors"])),
               "sample_attempts": len(sample), "sample_unique_tasks": len({(r["domain"],r["task_id"]) for r in sample}),
               "sample_categories": len({r["domain"] for r in sample}),
               "selection": "Per category: lexicographically first invalid-reference attempt (or least tool-active failed-reference attempt if none); most tool-active failed-reference attempt. Ties: task ID then trial. Add every workflow-terminal attempt and deduplicate identities.",
               "limitations": ["Purposive sample is not representative and is not a calibrated human gold set.",
                               "Reference self-evaluation matches its own calls by construction; it is not independent proof of semantic correctness.",
                               "Reference replay continues after individual errors for diagnostics; it is not a viable completed workflow.",
                               "Direct mock invocation bypasses schema validation; acceptance does not prove an adapter bug.",
                               "No new outcome labels or empirical scores are assigned."]}
    for path in [run_dir / "trials.csv", run_dir / "manifest.json", run_dir / "reference_preflight.json",
                 ROOT / "baseline/synthetic_environment.py", ROOT / "baseline/run_synthetic_baseline.py",
                 ROOT / "baseline/synthetic_user_guidelines.md",
                 ROOT / "docs/evaluation/synthetic_milestone_rubric.md"]:
        inputs[str(path.relative_to(ROOT))] = sha256(path)
    for domain in sorted({d for d, _ in cases}):
        for name in ("test_cases.py", "test_cases.json", "agent_definition.yaml"):
            path = ROOT / "data" / domain / name
            inputs[str(path.relative_to(ROOT))] = sha256(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "reference_replay.json", replays)
    write_json(output_dir / "sample.json", sample)
    write_json(output_dir / "input_manifest.json", {"inputs": inputs,
               "generator_sha256": sha256(Path(__file__)), "network_calls": 0})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(build_review(output_dir=args.output_dir), indent=2))


if __name__ == "__main__":
    main()
