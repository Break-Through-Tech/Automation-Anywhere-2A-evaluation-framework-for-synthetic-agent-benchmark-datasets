#!/usr/bin/env python3
"""Validate the Difficulty metric: do tasks with more write actions fail more often?

Spearman correlation between each tau-bench task's write-action count (the
structural difficulty metric) and its empirical difficulty (1 - c/n from the
baseline agent runs). If the metric works, the correlation is positive.

Inputs
  --difficulty  empirical_difficulty.csv from compute_difficulty.py
                (columns: domain, task_id, difficulty, n_valid, ...)
  write counts  computed here from data/processed/tasks.jsonl, using tau2's own
                read/write tool labels in difficulty/tau2_tool_labels.csv

Outputs (in --out, default results/difficulty/)
  tau2_write_counts.csv          write counts for every tau-bench task
  difficulty_validation.csv      one row per scored task: write count + difficulty
  difficulty_validation.json     Spearman rho and p-value, overall and per domain
  difficulty_scatter.png         write count vs empirical difficulty

Write count definition
  num_write        ALL ground-truth write actions, including telecom actions the
                   customer performs on their phone (the agent has to get them to).
                   This is the main metric.
  num_write_agent  only write actions the agent itself calls. Reported as a
                   sensitivity check; it only differs for telecom.

Usage
  python baseline/compute_difficulty.py --trials results/baseline/v2_full/trials.csv
  python baseline/validate_difficulty.py --difficulty results/difficulty/empirical_difficulty.csv
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS_PATH = REPO / "data" / "processed" / "tasks.jsonl"
LABELS_PATH = REPO / "difficulty" / "tau2_tool_labels.csv"


def load_labels(path=LABELS_PATH):
    labels = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            labels[(row["domain"], row["side"], row["tool"])] = row["label"]
    return labels


def tau2_write_counts(tasks_path=TASKS_PATH, labels=None):
    labels = labels or load_labels()
    rows = []
    with open(tasks_path) as f:
        for line in f:
            t = json.loads(line)
            if t["dataset"] != "tau2":
                continue
            num_write = num_write_agent = 0
            for a in t["actions"]:
                side = "user" if a.get("requestor") == "user" else "agent"
                label = labels.get((t["domain"], side, a["name"]))
                if label is None:
                    raise KeyError(f"No read/write label for {t['domain']}/{side}/{a['name']} "
                                   f"(task {t['task_id']}). Add it to {LABELS_PATH.name}.")
                if label == "write":
                    num_write += 1
                    num_write_agent += side == "agent"
            rows.append({
                "dataset": "tau2",
                "domain": t["domain"],
                "task_id": str(t["task_id"]),
                "num_actions": len(t["actions"]),
                "num_write": num_write,
                "num_write_agent": num_write_agent,
            })
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def spearman(x, y):
    from scipy.stats import spearmanr

    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return {"n": len(x), "rho": None, "p_value": None,
                "note": "not enough tasks or no variation to correlate"}
    res = spearmanr(x, y)
    return {"n": len(x), "rho": round(float(res.statistic), 4), "p_value": float(res.pvalue)}


def scatter(rows, path, rho_info):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(0)  # fixed jitter so the plot is reproducible
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for domain in sorted({r["domain"] for r in rows}):
        rs = [r for r in rows if r["domain"] == domain]
        x = np.array([r["num_write"] for r in rs], float) + rng.uniform(-0.15, 0.15, len(rs))
        y = np.array([r["difficulty"] for r in rs], float) + rng.uniform(-0.02, 0.02, len(rs))
        ax.scatter(x, y, s=22, alpha=0.65, label=f"{domain} (n={len(rs)})")

    # Mean difficulty at each write count, to show the trend through the ties
    by_w = defaultdict(list)
    for r in rows:
        by_w[r["num_write"]].append(r["difficulty"])
    ws = sorted(by_w)
    ax.plot(ws, [sum(by_w[w]) / len(by_w[w]) for w in ws], color="black", lw=1.5,
            marker="o", ms=4, label="mean difficulty")

    rho, p = rho_info["rho"], rho_info["p_value"]
    title = "Write actions vs empirical difficulty (tau-bench)"
    if rho is not None:
        title += f"\nSpearman rho = {rho:.3f}, p = {p:.2g}, n = {rho_info['n']}"
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Ground-truth write actions (jittered)")
    ax.set_ylabel("Empirical difficulty, 1 - c/n (jittered)")
    ax.set_ylim(-0.08, 1.08)
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--difficulty", required=True, help="empirical_difficulty.csv from compute_difficulty.py")
    ap.add_argument("--out", default=str(REPO / "results" / "difficulty"), help="output folder")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    counts = tau2_write_counts()
    write_csv(out / "tau2_write_counts.csv", counts)
    by_key = {(c["domain"], c["task_id"]): c for c in counts}

    merged, missing = [], []
    with open(args.difficulty, newline="") as f:
        for d in csv.DictReader(f):
            if d["difficulty"] in ("", "None"):
                continue  # task had no valid trials (all infra errors)
            c = by_key.get((d["domain"], str(d["task_id"])))
            if c is None:
                missing.append((d["domain"], d["task_id"]))
                continue
            merged.append({
                "domain": d["domain"],
                "task_id": d["task_id"],
                "num_write": c["num_write"],
                "num_write_agent": c["num_write_agent"],
                "n_valid": int(d["n_valid"]),
                "difficulty": float(d["difficulty"]),
            })
    if not merged:
        raise SystemExit("No tasks matched between the difficulty file and tau2 tasks.")
    write_csv(out / "difficulty_validation.csv", merged)

    def corr(rows, key):
        return spearman([r[key] for r in rows], [r["difficulty"] for r in rows])

    result = {
        "difficulty_file": str(args.difficulty),
        "expected": "positive rho: more write actions -> higher empirical difficulty",
        "n_tasks_scored": len(merged),
        "n_tasks_unmatched": len(missing),
        "overall": {"num_write": corr(merged, "num_write"),
                    "num_write_agent": corr(merged, "num_write_agent")},
        "by_domain": {},
    }
    for domain in sorted({r["domain"] for r in merged}):
        rs = [r for r in merged if r["domain"] == domain]
        result["by_domain"][domain] = {"num_write": corr(rs, "num_write"),
                                       "num_write_agent": corr(rs, "num_write_agent")}
    (out / "difficulty_validation.json").write_text(json.dumps(result, indent=2))
    scatter(merged, out / "difficulty_scatter.png", result["overall"]["num_write"])

    o = result["overall"]["num_write"]
    print(f"Saved to {out}/")
    print(f"  Overall: rho = {o['rho']}, p = {o['p_value']}, n = {o['n']} tasks")
    for domain, r in result["by_domain"].items():
        s = r["num_write"]
        print(f"  {domain}: rho = {s['rho']}, p = {s['p_value']}, n = {s['n']}")
    if missing:
        print(f"  WARNING: {len(missing)} task(s) in the difficulty file had no tau2 match, e.g. {missing[:2]}")


if __name__ == "__main__":
    main()
