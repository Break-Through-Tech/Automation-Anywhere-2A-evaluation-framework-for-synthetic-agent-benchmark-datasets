#!/usr/bin/env python3
"""Empirical difficulty = 1 - c/n for each task, from saved baseline trial results.

  c = number of trials the baseline agent passed
  n = number of VALID trials (trials that produced a reward; API errors and invalid references are excluded)

Input:  one or more trials.csv files written by run_baseline.py
        (columns: domain, task_id, trial, seed, reward, passed, ...)
Output: <out>/empirical_difficulty.csv          one row per task
        <out>/empirical_difficulty_summary.json per-domain summary

Usage:
  python baseline/compute_difficulty.py --trials results/baseline/<run_id>/trials.csv

Notes:
  * Tasks are keyed by (domain, task_id), so ids that repeat across domains don't collide.
  * Pass several --trials files only if they came from the SAME baseline_version;
    their trials are pooled, which raises n.
  * With few trials, difficulty is coarse (n=4 gives only 0, .25, .5, .75, 1), which
    creates many ties in the Spearman validation. More trials give a finer score.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def load_trials(paths):
    rows = []
    for p in paths:
        with open(p, newline="") as f:
            rows += list(csv.DictReader(f))
    return rows


def _task_sort_key(key):
    domain, task_id = key
    return (domain, 0, int(task_id), "") if str(task_id).isdigit() else (domain, 1, 0, str(task_id))


def compute_difficulty(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["domain"], r["task_id"])].append(r)

    results = []
    for key in sorted(groups, key=_task_sort_key):
        domain, task_id = key
        trials = groups[key]
        valid = [t for t in trials if t.get("reward") not in (None, "", "None")]
        n = len(valid)
        c = sum(int(t["passed"]) for t in valid)
        results.append({
            "domain": domain,
            "task_id": task_id,
            "n_trials": len(trials),
            "n_valid": n,
            "c_passed": c,
            "pass_rate": round(c / n, 4) if n else None,
            "difficulty": round(1 - c / n, 4) if n else None,
        })
    return results


def summarize(results):
    by_domain = defaultdict(list)
    for r in results:
        by_domain[r["domain"]].append(r)
    by_domain["ALL"] = list(results)

    summary = {}
    for domain, rs in by_domain.items():
        scored = [r for r in rs if r["difficulty"] is not None]
        diffs = [r["difficulty"] for r in scored]
        summary[domain] = {
            "n_tasks": len(rs),
            "n_scored": len(scored),
            "mean_difficulty": round(sum(diffs) / len(diffs), 4) if diffs else None,
            "never_solved (difficulty=1)": sum(d == 1 for d in diffs),
            "always_solved (difficulty=0)": sum(d == 0 for d in diffs),
            "mixed": sum(0 < d < 1 for d in diffs),
            "distinct_difficulty_values": len(set(diffs)),
            "tasks_with_infra_errors": sum(r["n_valid"] < r["n_trials"] for r in rs),
            "min_valid_trials_per_task": min((r["n_valid"] for r in rs), default=0),
            "max_valid_trials_per_task": max((r["n_valid"] for r in rs), default=0),
        }
    return summary


def run(trials_paths, out_dir):
    """Compute and save empirical difficulty. Returns the summary dict."""
    trials = load_trials(trials_paths)
    results = compute_difficulty(trials)
    if not results:
        raise ValueError(f"No trial rows found in {list(map(str, trials_paths))}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "empirical_difficulty.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    summary = summarize(results)
    for domain, info in summary.items():
        selected = [r for r in trials if domain == "ALL" or r["domain"] == domain]
        invalid = {r["task_id"] if domain != "ALL" else (r["domain"], r["task_id"])
                   for r in selected if r.get("evaluation_status") == "invalid_reference"}
        infra = {r["task_id"] if domain != "ALL" else (r["domain"], r["task_id"])
                 for r in selected if r.get("reward") in (None, "", "None")
                 and r.get("evaluation_status") != "invalid_reference"}
        info["tasks_with_invalid_references"] = len(invalid)
        info["tasks_with_infra_errors"] = len(infra)
    (out_dir / "empirical_difficulty_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--trials", nargs="+", required=True, help="trials.csv file(s) from run_baseline.py")
    ap.add_argument("--out", default="results/difficulty", help="output folder (default results/difficulty)")
    args = ap.parse_args()

    summary = run(args.trials, args.out)
    print(f"Saved to {args.out}/")
    for domain, s in summary.items():
        print(f"  {domain}: {s['n_tasks']} tasks, mean difficulty {s['mean_difficulty']}, "
              f"never solved {s['never_solved (difficulty=1)']}, always solved {s['always_solved (difficulty=0)']}, "
              f"mixed {s['mixed']}")
        if s["tasks_with_infra_errors"]:
            print(f"    WARNING: {s['tasks_with_infra_errors']} task(s) had infra-error trials excluded from n")
        if s["tasks_with_invalid_references"]:
            print(f"    WARNING: {s['tasks_with_invalid_references']} task(s) have invalid references and are unscored")


if __name__ == "__main__":
    main()
