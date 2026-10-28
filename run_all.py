#!/usr/bin/env python3
"""Compute coverage and difficulty for both datasets from the committed base tasks.

Runs local embeddings and saved-trial analysis only; never starts agent trials.
Usage: python run_all.py --seed 42 --output-dir results/framework
"""
import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
from collections import Counter
from importlib import metadata
from pathlib import Path

from baseline.compute_difficulty import compute_difficulty, load_trials
from baseline.validate_difficulty import load_labels, scatter, spearman, tau2_write_counts
from coverage.attribute_diversity import DOMAINS, compute_attribute_diversity
from coverage.vendi_score import MODEL_NAME, embed, vendi_score
from difficulty.write_counts import count_actions

ROOT = Path(__file__).resolve().parent
# Resolved from the public model's snapshot during the first framework run.
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_inputs(tasks_path, labels_dir):
    tasks = [json.loads(line) for line in tasks_path.read_text().splitlines() if line.strip()]
    seen = set()
    for task in tasks:
        key = (task["dataset"], task["domain"], task["task_id"])
        if task["dataset"] not in DOMAINS or key in seen:
            raise ValueError(f"Unknown dataset or duplicate task: {key}")
        if not task["description"].strip() or not isinstance(task["actions"], list):
            raise ValueError(f"Missing description or actions: {key}")
        seen.add(key)
    labels = {}
    for dataset in DOMAINS:
        subset = [t for t in tasks if t["dataset"] == dataset]
        if not subset:
            raise ValueError(f"No tasks for {dataset}")
        rows = read_csv(labels_dir / f"labels_{dataset}.csv")
        expected = {(t["domain"] + ":" if dataset == "tau2" else "") + t["task_id"]
                    for t in subset}
        if len(rows) != len(expected) or {r["task_id"] for r in rows} != expected:
            raise ValueError(f"{dataset}: labels must match task IDs exactly")
        labels[dataset] = rows
    return tasks, labels


def structural_difficulty(tasks, tasks_path, tau_labels_path, synthetic_labels_path):
    rows = tau2_write_counts(tasks_path, load_labels(tau_labels_path))
    labels = {}
    for row in read_csv(synthetic_labels_path):
        labels.setdefault(row["domain"], {})[row["tool"]] = row["label"]
    for task in tasks:
        if task["dataset"] != "synthetic":
            continue
        actions, writes, unknown = count_actions(task["actions"], labels.get(task["domain"], {}))
        if unknown:
            raise ValueError(f"Unlabeled synthetic tools in {task['task_id']}: {unknown}")
        rows.append(dict(dataset="synthetic", domain=task["domain"], task_id=task["task_id"],
                         num_actions=actions, num_write=writes, num_write_agent=writes))
    return sorted(rows, key=lambda r: (r["dataset"], r["domain"], r["task_id"]))


def empirical_difficulty(path, expected):
    if path is None:
        return {}
    trials = load_trials([path])
    seen = set()
    for row in trials:
        key = (row["domain"], row["task_id"])
        identity = (*key, int(row["trial"]))
        if key not in expected or identity in seen or identity[-1] < 0:
            raise ValueError(f"Unknown task or duplicate/invalid trial: {identity}")
        seen.add(identity)
        if row.get("reward") not in (None, "", "None"):
            if not math.isfinite(float(row["reward"])) or row["passed"] not in ("0", "1"):
                raise ValueError(f"Invalid reward/pass outcome: {identity}")
            if int(row["passed"]) != int(float(row["reward"]) >= 0.999):
                raise ValueError(f"Reward and passed disagree: {identity}")
    results = {(r["domain"], r["task_id"]): r for r in compute_difficulty(trials)}
    for key, result in results.items():
        statuses = Counter(r.get("evaluation_status") or ("evaluated" if r.get("reward") not in (None, "", "None")
                                                           else "no_reward")
                           for r in trials if (r["domain"], r["task_id"]) == key)
        result["evaluation_status_counts"] = dict(statuses)
    return results


def evaluate(args):
    tasks, labels = load_inputs(args.tasks, args.labels_dir)
    counts, attributes = compute_attribute_diversity(labels)
    structural = structural_difficulty(tasks, args.tasks, args.tau_tool_labels, args.synthetic_tool_labels)
    empirical = {}
    for dataset, path in (("tau2", args.tau_trials), ("synthetic", args.synthetic_trials)):
        if path and (path.parent / "manifest.json").exists():
            manifest = json.loads((path.parent / "manifest.json").read_text())
            if "planned_trials" in manifest and manifest.get("completed_trials", 0) != manifest["planned_trials"]:
                raise ValueError(f"{dataset}: baseline run is still incomplete; wait for it to finish before scoring")
        expected = {(t["domain"], t["task_id"]) for t in tasks if t["dataset"] == dataset}
        empirical[dataset] = empirical_difficulty(path, expected)
    if args.synthetic_trials:
        manifests = [p.parent / "manifest.json" for p in (args.tau_trials, args.synthetic_trials)]
        if all(p.exists() for p in manifests):
            configs = [json.loads(p.read_text())["config"] for p in manifests]
            for field in ("baseline_version", "model", "user_model", "decoding", "user_decoding", "seed", "max_steps"):
                if configs[0].get(field) != configs[1].get(field):
                    raise ValueError(f"Baseline settings differ between datasets: {field}")

    print(f"Embedding {len(tasks)} descriptions with {args.model} on CPU...", flush=True)
    embeddings = embed([t["description"] for t in tasks], args.model, args.seed, args.model_revision)
    if len(embeddings) != len(tasks):
        raise ValueError("Embedding count differs from task count")
    scores = []
    for dataset in DOMAINS:
        domains = sorted({t["domain"] for t in tasks if t["dataset"] == dataset})
        for domain in ["all", *domains]:
            indices = [i for i, t in enumerate(tasks) if t["dataset"] == dataset
                       and (domain == "all" or t["domain"] == domain)]
            value = vendi_score(embeddings[indices])
            if not math.isfinite(value) or not 1 - 1e-5 <= value <= len(indices) + 1e-5:
                raise ValueError("Invalid Vendi score")
            scores.append(dict(dataset=dataset, domain=domain, n_tasks=len(indices),
                               vendi_score=round(value, 8), vendi_score_norm=round(value / len(indices), 8)))

    per_task = []
    for row in structural:
        e = empirical[row["dataset"]].get((row["domain"], row["task_id"]), {})
        per_task.append({**row, "n_trials": e.get("n_trials", 0), "n_valid": e.get("n_valid", 0),
                         "c_passed": e.get("c_passed", 0), "empirical_difficulty": e.get("difficulty"),
                         "evaluation_status": "|".join(sorted(e.get("evaluation_status_counts", {}))) or "not_run"})
    summaries = []
    for score in scores:
        rows = [r for r in per_task if r["dataset"] == score["dataset"]
                and (score["domain"] == "all" or r["domain"] == score["domain"])]
        observed = [r["empirical_difficulty"] for r in rows if r["empirical_difficulty"] is not None]
        diversity = next((r["score"] for r in attributes if r["dataset"] == score["dataset"]
                          and r["attribute"] == "average"), None) if score["domain"] == "all" else None
        summaries.append({**score, "attribute_diversity": diversity,
                          "mean_write_count": round(statistics.mean(r["num_write"] for r in rows), 8),
                          "median_write_count": statistics.median(r["num_write"] for r in rows),
                          "empirical_tasks_scored": len(observed),
                          "empirical_tasks_unscored": len(rows) - len(observed),
                          "empirical_trials_valid": sum(r["n_valid"] for r in rows),
                          "mean_empirical_difficulty": round(statistics.mean(observed), 8) if observed else None})
    validation = {}
    for dataset in DOMAINS:
        rows = [r for r in per_task if r["dataset"] == dataset and r["empirical_difficulty"] is not None]
        validation[dataset] = {"all": spearman([r["num_write"] for r in rows],
                                               [r["empirical_difficulty"] for r in rows])}
        for domain in sorted({r["domain"] for r in rows}):
            subset = [r for r in rows if r["domain"] == domain]
            validation[dataset][domain] = spearman([r["num_write"] for r in subset],
                                                   [r["empirical_difficulty"] for r in subset])

    inputs = [args.tasks, args.tau_tool_labels, args.synthetic_tool_labels,
              *(args.labels_dir / f"labels_{dataset}.csv" for dataset in DOMAINS)]
    for path in (args.tau_trials, args.synthetic_trials):
        if path:
            inputs.append(path)
            manifest = path.parent / "manifest.json"
            if manifest.exists():
                inputs.append(manifest)
    summary = {
        "status": "complete", "scope": "committed tau2 base split and synthetic tasks",
        "task_counts": dict(Counter(t["dataset"] for t in tasks)),
        "metrics": ["coverage", "structural_difficulty"],
        "datasets": {r["dataset"]: r for r in summaries if r["domain"] == "all"},
        "limitations": ["Vendi VS/n depends on sample size and repeated descriptions.",
                         "Attribute tool entropy uses each dataset's observed tool vocabulary.",
                         "Synthetic attributes use four broad domains; task/Vendi groups use seven agent categories.",
                         "Write counts measure structural difficulty; higher difficulty does not imply higher quality."],
    }
    for dataset in DOMAINS:
        result = summary["datasets"][dataset]
        if result["empirical_tasks_scored"] < result["n_tasks"]:
            summary["limitations"].append(f"{dataset}: empirical difficulty available for "
                                           f"{result['empirical_tasks_scored']}/{result['n_tasks']} tasks.")
    summary["empirical_status"] = ("complete" if all(r["empirical_tasks_unscored"] == 0
                                                     for r in summary["datasets"].values()) else "partial")
    if summary["empirical_status"] == "partial":
        summary["status"] = "complete_with_unscored_empirical_tasks"
    if args.synthetic_trials:
        summary["limitations"].append("Synthetic empirical scores use a reference-trajectory/structured-outcome "
                                       "oracle, whereas tau2 uses its native evaluator; the scores are not strictly equivalent.")
        summary["limitations"].append("Missing scenario information and reference constraints can cause synthetic "
                                       "failures; the empirical score does not isolate intrinsic task difficulty.")
        summary["synthetic_evaluation_status_counts"] = dict(sum(
            (Counter(r["evaluation_status_counts"]) for r in empirical["synthetic"].values()), Counter()))
    def path_label(path):
        path = path.resolve()
        return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    provenance = {
        "seed": args.seed, "embedding_model": args.model, "model_revision_requested": args.model_revision,
        "embedding_device": "cpu", "python": platform.python_version(),
        "inputs": {path_label(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        "sources": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                    ["run_all.py", "coverage/attribute_diversity.py", "coverage/vendi_score.py",
                     "difficulty/write_counts.py", "baseline/compute_difficulty.py",
                     "baseline/validate_difficulty.py"]},
        "packages": {name: metadata.version(name) for name in
                     ["numpy", "sentence-transformers", "torch", "transformers", "scipy", "matplotlib",
                      "openai", "pydantic", "langchain-core", "PyYAML"]},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in [("coverage_vendi.csv", scores), ("coverage_attribute_counts.csv", counts),
                           ("coverage_attribute_scores.csv", attributes), ("difficulty_tasks.csv", per_task),
                           ("metrics_by_domain.csv", summaries)]:
        write_csv(args.output_dir / filename, rows)
    write_json(args.output_dir / "metrics_summary.json", summary)
    write_json(args.output_dir / "difficulty_validation.json", validation)
    write_json(args.output_dir / "run_metadata.json", provenance)
    tau_rows = [{**r, "difficulty": r["empirical_difficulty"]} for r in per_task
                if r["dataset"] == "tau2" and r["empirical_difficulty"] is not None]
    if tau_rows:
        scatter(tau_rows, args.output_dir / "difficulty_scatter.png", validation["tau2"]["all"])
    for dataset, score in summary["datasets"].items():
        print(f"{dataset}: n={score['n_tasks']}, VS/n={score['vendi_score_norm']:.4f}, "
              f"Attribute Diversity={score['attribute_diversity']:.4f}, "
              f"mean writes={score['mean_write_count']:.4f}, "
              f"empirical={score['mean_empirical_difficulty']}")
    print(f"Saved results to {args.output_dir}")
    return summary


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tasks", type=Path, default=ROOT / "data/processed/tasks.jsonl")
    p.add_argument("--labels-dir", type=Path, default=ROOT / "coverage/labels")
    p.add_argument("--tau-tool-labels", type=Path, default=ROOT / "difficulty/tau2_tool_labels.csv")
    p.add_argument("--synthetic-tool-labels", type=Path, default=ROOT / "difficulty/synthetic_tool_labels.csv")
    p.add_argument("--tau-trials", type=Path, default=ROOT / "results/baseline/v2_full/trials.csv")
    synthetic = ROOT / "results/baseline/v2_synthetic_full/trials.csv"
    p.add_argument("--synthetic-trials", type=Path, default=synthetic if synthetic.exists() else None)
    p.add_argument("--output-dir", type=Path, default=ROOT / "results/framework")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--model", default=MODEL_NAME)
    p.add_argument("--model-revision", default=MODEL_REVISION,
                   help="Pinned Hugging Face model commit; override alongside --model for a different model")
    return p


if __name__ == "__main__":
    args = parser().parse_args()
    try:
        evaluate(args)
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Evaluation failed: {exc}") from exc
