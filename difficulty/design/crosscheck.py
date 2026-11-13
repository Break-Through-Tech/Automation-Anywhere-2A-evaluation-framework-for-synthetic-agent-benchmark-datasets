"""Post-scoring diagnostics; supplied tags never enter a judge request."""
from collections import defaultdict
import itertools
import math

from .rubric import digest

FEATURES = ("proposed_operation_unit_count", "reference_tool_interactions", "business_check_groups", "distinct_coordination_events")


def association(pairs):
    n = len(pairs)
    if n < 3:
        return {"n": n, "rho": None, "p_value": None, "reason": "fewer_than_three_pairs"}
    x, y = zip(*pairs)
    if len(set(x)) < 2 or len(set(y)) < 2:
        return {"n": n, "rho": None, "p_value": None, "reason": "constant_values"}
    from scipy.stats import spearmanr
    result = spearmanr(x, y)
    return {"n": n, "rho": float(result.statistic), "p_value": float(result.pvalue),
            "ties_x": n-len(set(x)), "ties_y": n-len(set(y)),
            "reason": "exploratory_asymptotic_p_value_not_independent_validation"}


def compare(report, inventory, features=None):
    bykey = {(r["dataset"], r["domain"], r["task_id"]): r for r in inventory}
    if len(bykey) != len(inventory):
        raise ValueError("Duplicate comparison inventory")
    feature_rows = {}
    if features is not None:
        source_hashes = features.get("source_sha256", {})
        expected = {s["path"]: s["sha256"] for r in inventory if r["dataset"] == "synthetic" for s in r["sources"].values()}
        if source_hashes != expected:
            raise ValueError("Structural feature provenance differs from scoring sources")
        for row in features["tasks"]:
            key = (row.get("dataset", "synthetic"), row["domain"], row["task_id"])
            if key in feature_rows or key not in bykey:
                raise ValueError("Duplicate/unknown structural comparison task")
            feature_rows[key] = row
    joined = []
    for row in report["tasks"]:
        key = (row["dataset"], row["domain"], row["task_id"])
        if key not in bykey or row["input_sha256"] != bykey[key]["input_sha256"]:
            raise ValueError("Score/comparison inventory differs")
        original = bykey[key]
        annotation = original["comparison_only"]
        tag = annotation.get("class_tag")
        if tag not in {"easy", "medium", "hard"}:
            tag = None
        joined.append({**row, "supplied_tag_comparison_only": tag,
                       "declared_tag_conflict": bool(annotation.get("declared_label") and annotation["declared_label"] != tag),
                       "features": {k: feature_rows.get(key, {}).get(k) for k in FEATURES}})
    groups = {"all": joined}
    for ds in sorted({r["dataset"] for r in joined}):
        groups[ds] = [r for r in joined if r["dataset"] == ds]
        for domain in sorted({r["domain"] for r in groups[ds]}):
            groups[ds + "/" + domain] = [r for r in groups[ds] if r["domain"] == domain]
    summaries = {}
    order = {"easy": 0, "medium": 1, "hard": 2}
    for name, rows in groups.items():
        scored = [r for r in rows if r["status"] == "scored"]
        summaries[name] = {"n_total": len(rows), "n_scored": len(scored),
                           "n_missing_tags": sum(r["supplied_tag_comparison_only"] is None for r in rows),
                           "n_conflicting_tags": sum(r["declared_tag_conflict"] for r in rows),
                           "tag_association": association([(order[r["supplied_tag_comparison_only"]], r["score"]) for r in scored if r["supplied_tag_comparison_only"] is not None]),
                           "feature_associations": {k: association([(r["features"][k], r["score"]) for r in scored
                                                                     if type(r["features"][k]) in {int, float} and math.isfinite(r["features"][k])]) for k in FEATURES}}
    within = defaultdict(list)
    for row in joined:
        if row["workflow_id"]:
            within[(row["dataset"], row["domain"], row["workflow_id"])].append(row)
    pairs = []
    for group, rows in within.items():
        for a, b in itertools.combinations(rows, 2):
            pairs.append({"dataset": group[0], "domain": group[1], "workflow_id": group[2],
                          "task_ids": [a["task_id"], b["task_id"]], "scores": [a["score"], b["score"]],
                          "supplied_tags": [a["supplied_tag_comparison_only"], b["supplied_tag_comparison_only"]],
                          "delta": b["score"]-a["score"] if a["status"] == b["status"] == "scored" else None})
    return {"status": "post_scoring_diagnostics" if any(r["status"] == "scored" for r in joined) else "prepared_no_judgments_yet",
            "score_report_sha256": digest(report), "feature_document_sha256": digest(features) if features else None,
            "groups": summaries, "within_workflow_pairs": pairs, "tasks": joined,
            "limitations": ["Tags are supplied annotations, not verified gold difficulty.",
                            "Shared sources and overlapping dimensions limit independence of structural comparisons.",
                            "Pooled-domain effects, small samples and ties require caution; associations are descriptive.",
                            "No thresholds or weights were tuned to force a dataset ordering."]}
