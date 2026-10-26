#!/usr/bin/env python3
"""Validate issue #22's Vendi coverage metric with tau2 domain removal.

From the repository root::

    python coverage/validate_coverage.py --matched-samples 5

This uses the committed tau2 ``base`` split in data/processed/tasks.jsonl.
Descriptions are embedded once with the same model used by vendi_score.py;
every scenario reuses those embeddings. It runs no agents and needs no API key.
"""

import argparse
import csv
import hashlib
from importlib.metadata import version
import json
import math
import random
import statistics
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "data" / "processed" / "tasks.jsonl"
DEFAULT_OUTPUT = ROOT / "results" / "coverage"
RESULT_COLUMNS = (
    "run_id", "comparison", "removed_domain", "repeat", "seed",
    "n_tasks", "n_domains", "domains_remaining", "vendi_score", "normalized_score",
)
MEMBERSHIP_COLUMNS = ("run_id", "dataset", "domain", "task_id")
SUMMARY_COLUMNS = (
    "removed_domain", "removed_tasks", "remaining_tasks", "full_vendi_score",
    "full_normalized_score", "reduced_vendi_score", "reduced_normalized_score",
    "delta_vs_full", "matched_full_mean_normalized_score", "delta_vs_matched_full",
)


def load_tau2_tasks(path: Path) -> list[dict]:
    if not path.is_file():
        raise ValueError(f"Task file not found: {path}. Run python data/loaders.py first.")

    tasks = []
    seen = set()
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                task = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(task, dict):
                raise ValueError(f"Expected a task object at {path}:{line_number}")
            if task.get("dataset") != "tau2":
                continue
            for field in ("domain", "task_id", "description"):
                if not isinstance(task.get(field), str) or not task[field].strip():
                    raise ValueError(f"Missing {field} at {path}:{line_number}")
            identity = (task["domain"], task["task_id"])
            if identity in seen:
                raise ValueError(f"Duplicate tau2 task {identity} at {path}:{line_number}")
            seen.add(identity)
            tasks.append(task)

    if not tasks:
        raise ValueError(f"No tau2 tasks found in {path}")
    if len({task["domain"] for task in tasks}) < 2:
        raise ValueError("Domain-removal validation needs at least two tau2 domains")
    return tasks


def score_tasks(tasks, embeddings, index_by_task, vendi_score_fn) -> tuple[float, float]:
    selected = embeddings[[index_by_task[(t["domain"], t["task_id"])] for t in tasks]]
    vendi_score = float(vendi_score_fn(selected))
    normalized_score = vendi_score / len(tasks)
    if not all(math.isfinite(value) for value in (vendi_score, normalized_score)):
        raise ValueError("Vendi scorer returned a non-finite score")
    if vendi_score < 1 - 1e-6 or vendi_score > len(tasks) + 1e-6:
        raise ValueError(f"Vendi Score {vendi_score} is outside [1, {len(tasks)}]")
    return vendi_score, normalized_score


def write_run(results_writer, membership_writer, run_id: str, comparison: str,
              removed_domain: str, repeat: int, seed: int,
              tasks: list[dict], embeddings, index_by_task, vendi_score_fn) -> dict:
    vendi_score, normalized_score = score_tasks(tasks, embeddings, index_by_task, vendi_score_fn)
    domains = sorted({task["domain"] for task in tasks})
    row = {
        "run_id": run_id,
        "comparison": comparison,
        "removed_domain": removed_domain,
        "repeat": repeat,
        "seed": seed,
        "n_tasks": len(tasks),
        "n_domains": len(domains),
        "domains_remaining": "|".join(domains),
        "vendi_score": vendi_score,
        "normalized_score": normalized_score,
    }
    results_writer.writerow(row)
    for task in tasks:
        membership_writer.writerow({
            "run_id": run_id,
            "dataset": task["dataset"],
            "domain": task["domain"],
            "task_id": task["task_id"],
        })
    print(f"{run_id}: n={len(tasks)}, VS={vendi_score:.4f}, VS/n={normalized_score:.4f}")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS,
                        help="Unified tasks.jsonl from data/loaders.py")
    parser.add_argument("--split-label", default="base",
                        help="Split recorded in metadata; does not filter tasks (default: base)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--matched-samples", type=int, default=0,
                        help="Equal-sized random full-set samples per removed domain (default: 0)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for matched samples (default: 42)")
    args = parser.parse_args()
    if args.matched_samples < 0:
        parser.error("--matched-samples must be nonnegative")

    try:
        tasks = load_tau2_tasks(args.tasks)
        sys.path.insert(0, str(ROOT))
        from coverage.vendi_score import MODEL_NAME, embed, vendi_score

        domains = sorted({task["domain"] for task in tasks})
        print(f"Loaded {len(tasks)} tau2 tasks: {dict(sorted(Counter(t['domain'] for t in tasks).items()))}")
        print(f"Embedding task descriptions once with {MODEL_NAME}...")
        embeddings = embed([task["description"] for task in tasks])
        index_by_task = {(task["domain"], task["task_id"]): i for i, task in enumerate(tasks)}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        results_path = args.output_dir / "coverage_results.csv"
        membership_path = args.output_dir / "run_tasks.csv"
        summary_path = args.output_dir / "coverage_summary.csv"
        metadata_path = args.output_dir / "run_metadata.json"
        rng = random.Random(args.seed)
        rows = []

        with results_path.open("w", newline="", encoding="utf-8") as results_file, \
             membership_path.open("w", newline="", encoding="utf-8") as membership_file:
            results_writer = csv.DictWriter(results_file, fieldnames=RESULT_COLUMNS, lineterminator="\n")
            membership_writer = csv.DictWriter(membership_file, fieldnames=MEMBERSHIP_COLUMNS, lineterminator="\n")
            results_writer.writeheader()
            membership_writer.writeheader()

            full_row = write_run(results_writer, membership_writer, "full", "full", "none",
                                 0, args.seed, tasks, embeddings, index_by_task, vendi_score)
            rows.append(full_row)
            for domain in domains:
                reduced = [task for task in tasks if task["domain"] != domain]
                reduced_row = write_run(results_writer, membership_writer,
                                        f"without_{domain}", "domain_removed", domain,
                                        0, args.seed, reduced, embeddings, index_by_task,
                                        vendi_score)
                rows.append(reduced_row)
                change = reduced_row["normalized_score"] - full_row["normalized_score"]
                print(f"  Change from full VS/n: {change:+.4f}")

                # Compare with random subsets containing the same number of tasks.
                for repeat in range(1, args.matched_samples + 1):
                    sampled_full = rng.sample(tasks, len(reduced))
                    rows.append(write_run(results_writer, membership_writer,
                                          f"matched_{domain}_{repeat:03d}", "matched_full", domain,
                                          repeat, args.seed, sampled_full, embeddings,
                                          index_by_task, vendi_score))
                results_file.flush()
                membership_file.flush()

        with summary_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for domain in domains:
                reduced = next(row for row in rows if row["run_id"] == f"without_{domain}")
                matched = [row["normalized_score"] for row in rows
                           if row["comparison"] == "matched_full" and row["removed_domain"] == domain]
                matched_mean = statistics.mean(matched) if matched else None
                writer.writerow({
                    "removed_domain": domain,
                    "removed_tasks": len(tasks) - reduced["n_tasks"],
                    "remaining_tasks": reduced["n_tasks"],
                    "full_vendi_score": full_row["vendi_score"],
                    "full_normalized_score": full_row["normalized_score"],
                    "reduced_vendi_score": reduced["vendi_score"],
                    "reduced_normalized_score": reduced["normalized_score"],
                    "delta_vs_full": reduced["normalized_score"] - full_row["normalized_score"],
                    "matched_full_mean_normalized_score": matched_mean,
                    "delta_vs_matched_full": (reduced["normalized_score"] - matched_mean
                                              if matched_mean is not None else None),
                })

        task_path = args.tasks.resolve()
        task_label = str(task_path.relative_to(ROOT)) if task_path.is_relative_to(ROOT) else task_path.name
        metadata = {
            "dataset": "tau2", "split": args.split_label, "model": MODEL_NAME,
            "task_file": task_label,
            "task_file_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
            "task_count": len(tasks), "domains": dict(Counter(t["domain"] for t in tasks)),
            "matched_samples_per_domain": args.matched_samples, "seed": args.seed,
            "packages": {name: version(name) for name in
                         ("numpy", "sentence-transformers", "torch", "transformers")},
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"Saved scores to {results_path}")
        print(f"Saved summary to {summary_path}")
        print(f"Saved task membership to {membership_path}")
        print(f"Saved run metadata to {metadata_path}")
        print("Interpret the observed differences; removing a domain does not guarantee VS/n falls.")
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
