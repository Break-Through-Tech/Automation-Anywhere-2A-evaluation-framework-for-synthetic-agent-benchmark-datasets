"""Offline equal-task aggregation; pending/error/unscorable cases are never zero."""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import mean, median, pstdev, quantiles

from .inputs import unique, validate_case
from .judge import load_packet, read_result, safe_output, write_json
from .rubric import DIMENSIONS, VERSION, digest


def distribution(rows):
    values = [r["score"] for r in rows if r["status"] == "scored"]
    q1, q3 = (quantiles(values, n=4, method="inclusive")[::2] if len(values) > 1
              else (values[0], values[0]) if values else (None, None))
    return {"n_total": len(rows), "n_scored": len(values),
            "coverage": len(values) / len(rows) if rows else 0,
            "status_counts": dict(Counter(r["status"] for r in rows)),
            "mean": mean(values) if values else None, "median": median(values) if values else None,
            "min": min(values) if values else None, "max": max(values) if values else None,
            "q1": q1, "q3": q3, "iqr": q3-q1 if values else None,
            "population_stddev": pstdev(values) if values else None,
            "mean_label": "unavailable" if not values else "complete_inventory_mean" if len(values) == len(rows) else "scored_subset_mean",
            "histogram": {f"{low}-{low+19 if low<80 else 100}": sum(low <= v <= (low+19 if low<80 else 100) for v in values)
                          for low in (0, 20, 40, 60, 80)}}


def aggregate(inventory, packets=()):
    unique(inventory)
    for row in inventory:
        validate_case(row)
    cases = {r["payload"]["case_key"]: r for r in inventory}
    requested, results, signatures, returned_models, packet_hashes = {}, defaultdict(list), set(), set(), {}
    seen_requests = set()
    for packet in packets:
        manifest, rows, requests = load_packet(packet)
        signatures.add(digest({k: manifest[k] for k in ("protocol", "rubric_version", "prompt_version", "prompt_sha256", "schema_sha256", "rubric_sha256", "adapter_version", "config")}))
        packet_hashes[str(Path(packet).resolve())] = digest(manifest)
        for row in rows:
            key = row["payload"]["case_key"]
            if key not in cases or row["input_sha256"] != cases[key]["input_sha256"] or row["sources"] != cases[key]["sources"]:
                raise ValueError("Packet is not a matching subset of the full inventory")
            if key in requested:
                raise ValueError("Task occurs in multiple packets; do not overweight duplicated attempts")
            requested[key] = [r for r in requests if r["case_key"] == key]
        for request in requests:
            if request["request_id"] in seen_requests:
                raise ValueError("Duplicate request across packets")
            seen_requests.add(request["request_id"])
            result = read_result(packet, request, cases[request["case_key"]])
            results[request["case_key"]].append(result)
            if result and result["status"] == "validated":
                returned_models.add(result["returned_model"])
    if len(signatures) > 1 or len(returned_models) > 1:
        raise ValueError("Refusing mixed rubric/prompt/model/decoding protocols")
    task_rows = []
    for key, row in cases.items():
        attempts = results.get(key, [])
        status, reason, value, dimensions = "pending", "No complete compatible judgments", None, None
        if row["preflight_errors"]:
            status, reason = "source_preflight_blocked", "; ".join(row["preflight_errors"])
        elif any(r and r["status"] in {"api_error", "format_error"} for r in attempts):
            status, reason = "judge_error", "At least one planned judgment has an API/format error"
        elif any(r and (r["status"] == "preflight_blocked" or r["judgment"]["status"] == "unscorable") for r in attempts):
            status = "unscorable"
            reason = "; ".join(r.get("judgment", {}).get("unscorable_reason", r.get("error", "")) for r in attempts if r)
        elif attempts and all(r and r["status"] == "validated" for r in attempts):
            values = [r["judgment"]["overall_score"] for r in attempts]
            value = mean(values)
            dimensions = {k: mean(r["judgment"]["dimensions"][k]["level"] for r in attempts) for k in DIMENSIONS}
            status, reason = "scored", "All planned repeat judgments usable"
        task_rows.append({"dataset": row["dataset"], "domain": row["domain"], "task_id": row["task_id"],
                          "workflow_id": row["workflow_id"], "case_key": key, "input_sha256": row["input_sha256"],
                          "status": status, "reason": reason, "score": value, "dimensions": dimensions,
                          "n_planned_judgments": len(requested.get(key, [])),
                          "n_saved_judgments": sum(r is not None for r in attempts),
                          "repeat_score_range": (max(r["judgment"]["overall_score"] for r in attempts) - min(r["judgment"]["overall_score"] for r in attempts)) if status == "scored" else None,
                          "source_quality_flags": row["source_quality_flags"]})
    datasets, domains, workflows = {}, {}, {}
    for dataset in sorted({r["dataset"] for r in task_rows}):
        subset = [r for r in task_rows if r["dataset"] == dataset]
        datasets[dataset] = distribution(subset)
        for domain in sorted({r["domain"] for r in subset}):
            group = [r for r in subset if r["domain"] == domain]
            domains[dataset + "/" + domain] = distribution(group)
            for wid in sorted({r["workflow_id"] or "not_defined" for r in group}):
                workflows[dataset + "/" + domain + "/" + wid] = distribution([r for r in group if (r["workflow_id"] or "not_defined") == wid])
    return {"metric": "llm_source_only_designed_difficulty", "rubric_version": VERSION,
            "scale": [0, 100], "task_weighting": "equal_weight_after_mean_of_all_planned_usable_repeats",
            "inventory_sha256": digest(inventory), "packet_manifest_hashes": packet_hashes,
            "protocol_fingerprints": sorted(signatures), "returned_models": sorted(returned_models),
            "calibration_status": "not_established_by_aggregation", "independent_validation": False,
            "datasets": datasets, "domains": domains, "workflows": workflows, "tasks": task_rows,
            "limitations": ["Provisional anchored index; numerical distances are not independently validated.",
                            "Incomplete means describe scored subsets, not omitted tasks.",
                            "Domain composition and available source information affect comparisons.",
                            "Higher difficulty alone is not higher dataset quality."]}


def write_report(report, out):
    out = safe_output(out)
    if out.exists():
        raise ValueError("Use a fresh report directory")
    out.mkdir(parents=True)
    write_json(out / "summary.json", {k: v for k, v in report.items() if k != "tasks"})
    write_json(out / "task_scores.json", report)
    with (out / "task_scores.csv").open("w", newline="") as handle:
        columns = ["dataset", "domain", "task_id", "workflow_id", "status", "score", "reason", "n_planned_judgments", "n_saved_judgments", "repeat_score_range"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: r[k] for k in columns} for r in report["tasks"])
    lines = ["# Designed-difficulty results", "", "Source-only numeric index, 0–100. Equal task weights. Calibration is not established by this report.", ""]
    for name, result in report["datasets"].items():
        lines += [f"## {name}", "", f"Score: {result['mean']} ({result['mean_label']}). Scored: {result['n_scored']}/{result['n_total']}.",
                  f"Median: {result['median']}; IQR: {result['iqr']}; range: {result['min']}–{result['max']}.", ""]
    lines += ["See task_scores.csv for every task and exclusion/pending reason, and summary.json for domain/workflow summaries and histogram counts.",
              "", *report["limitations"]]
    (out / "README.md").write_text("\n".join(lines) + "\n")
