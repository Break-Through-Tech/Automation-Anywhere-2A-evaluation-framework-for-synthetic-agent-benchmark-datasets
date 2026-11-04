#!/usr/bin/env python3
"""Difficulty summaries (Issue #19).

Generates plots for:
- Write-action count distributions (τ²-bench + synthetic), with τ² broken down by domain.
- Empirical difficulty distributions (τ² required; synthetic optional).
- Scatter plot of write count vs empirical difficulty (τ²; synthetic optional).

Empirical difficulty input format:
- CSV produced by `baseline/compute_difficulty.py` (columns include: domain, task_id, difficulty)

Outputs (default): `results/difficulty/summaries/`

Example (τ² only):
  python difficulty/summarize_difficulty.py --tau-empirical results/difficulty/empirical_difficulty.csv

Example (τ² + synthetic empirical):
  python difficulty/summarize_difficulty.py \
    --tau-empirical results/difficulty/empirical_difficulty.csv \
    --synthetic-empirical results/difficulty/synthetic/empirical_difficulty.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


REPO = Path(__file__).resolve().parent.parent
TAU2_TASKS_PATH = REPO / "data" / "processed" / "tasks.jsonl"
TAU2_LABELS_PATH = REPO / "difficulty" / "tau2_tool_labels.csv"
SYNTHETIC_WRITE_COUNTS_PATH = REPO / "difficulty" / "write_counts.csv"


def _configure_matplotlib_cache() -> None:
    if os.environ.get("MPLCONFIGDIR"):
        return
    try:
        cache_dir = Path(tempfile.gettempdir()) / "matplotlib"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)
    except Exception:
        pass


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _safe_float(v: object) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() == "none":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_empirical(path: Path) -> Dict[Tuple[str, str], float]:
    """Returns mapping (domain, task_id) -> empirical difficulty."""

    out: Dict[Tuple[str, str], float] = {}
    for row in _read_csv(path):
        domain = (row.get("domain") or "").strip()
        task_id = (row.get("task_id") or "").strip()
        d = _safe_float(row.get("difficulty"))
        if domain and task_id and d is not None:
            out[(domain, task_id)] = float(d)
    return out


def load_synthetic_write_counts(path: Path = SYNTHETIC_WRITE_COUNTS_PATH) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for r in _read_csv(path):
        if (r.get("dataset") or "synthetic").strip() not in ("", "synthetic"):
            continue
        rows.append(
            {
                "dataset": "synthetic",
                "domain": (r.get("domain") or "").strip(),
                "task_id": (r.get("task_id") or "").strip(),
                "num_actions": int(float(r.get("num_actions") or 0)),
                "num_write": int(float(r.get("num_write") or 0)),
            }
        )
    return rows


def load_tau2_labels(path: Path = TAU2_LABELS_PATH) -> Dict[Tuple[str, str, str], str]:
    labels: Dict[Tuple[str, str, str], str] = {}
    for row in _read_csv(path):
        labels[(row["domain"], row["side"], row["tool"])]= row["label"]
    return labels


def compute_tau2_write_counts(
    tasks_path: Path = TAU2_TASKS_PATH,
    labels_path: Path = TAU2_LABELS_PATH,
) -> List[Dict[str, object]]:
    import json as _json

    labels = load_tau2_labels(labels_path)
    rows: List[Dict[str, object]] = []

    with open(tasks_path, encoding="utf-8") as f:
        for line in f:
            t = _json.loads(line)
            if t.get("dataset") != "tau2":
                continue
            domain = t["domain"]
            task_id = str(t["task_id"])
            num_actions = len(t.get("actions", []))
            num_write = 0
            for a in t.get("actions", []):
                side = "user" if a.get("requestor") == "user" else "agent"
                tool = a["name"]
                label = labels.get((domain, side, tool))
                if label is None:
                    raise KeyError(
                        f"No read/write label for {domain}/{side}/{tool} (task {task_id}). "
                        f"Add it to {labels_path}."
                    )
                if label == "write":
                    num_write += 1
            rows.append(
                {
                    "dataset": "tau2",
                    "domain": domain,
                    "task_id": task_id,
                    "num_actions": num_actions,
                    "num_write": num_write,
                }
            )
    return rows


def _values_by_domain(rows: Iterable[Dict[str, object]], key: str) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        v = r.get(key)
        if v is None:
            continue
        out[str(r["domain"])].append(float(v))
    return out


def _save_hist_by_domain(
    *,
    by_domain: Dict[str, List[float]],
    title: str,
    xlabel: str,
    out_png: Path,
    focus_domains: Optional[List[str]] = None,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_png.parent.mkdir(parents=True, exist_ok=True)

    domains = focus_domains or sorted(by_domain)
    domains = [d for d in domains if d in by_domain]

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for d in domains:
        xs = by_domain[d]
        if xs:
            ax.hist(xs, bins=12, alpha=0.45, label=f"{d} (n={len(xs)})")

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _save_scatter(
    *,
    rows: List[Dict[str, object]],
    title: str,
    out_png: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_png.parent.mkdir(parents=True, exist_ok=True)

    by_domain = defaultdict(list)
    for r in rows:
        if r.get("difficulty") is None:
            continue
        by_domain[str(r["domain"])].append(r)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    cmap = plt.get_cmap("tab10")
    for i, domain in enumerate(sorted(by_domain)):
        rs = by_domain[domain]
        ax.scatter(
            [float(rr["num_write"]) for rr in rs],
            [float(rr["difficulty"]) for rr in rs],
            s=24,
            alpha=0.7,
            label=f"{domain} (n={len(rs)})",
            color=cmap(i % 10),
        )

    ax.set_title(title)
    ax.set_xlabel("write actions")
    ax.set_ylabel("empirical difficulty (1 - pass_rate)")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _merge_empirical(rows: List[Dict[str, object]], empirical: Dict[Tuple[str, str], float]) -> List[Dict[str, object]]:
    merged: List[Dict[str, object]] = []
    for r in rows:
        key = (str(r["domain"]), str(r["task_id"]))
        out = dict(r)
        out["difficulty"] = empirical.get(key)
        merged.append(out)
    return merged


def _write_domain_summary(out_dir: Path, datasets: List[Tuple[str, List[Dict[str, object]]]]) -> None:
    def _mean(xs: List[float]) -> Optional[float]:
        return sum(xs) / len(xs) if xs else None

    domain_rows: List[Dict[str, object]] = []
    for dataset, rows in datasets:
        by_domain = defaultdict(list)
        for r in rows:
            by_domain[str(r[domain])].append(r)
        for domain in sorted(by_domain):
            rs = by_domain[domain]
            writes = [float(r[num_write]) for r in rs]
            diffs = [float(r[difficulty]) for r in rs if r.get(difficulty) is not None]
            domain_rows.append(
                {
                    dataset: dataset,
                    domain: domain,
                    n_tasks: len(rs),
                    mean_num_write: round(_mean(writes) or 0.0, 4),
                    n_tasks_with_empirical: len(diffs),
                    mean_empirical_difficulty: round(_mean(diffs), 4) if diffs else None,
                }
            )
    _write_csv(out_dir / domain_summary.csv, domain_rows)


def main(argv: Optional[List[str]] = None) -> int:
    _configure_matplotlib_cache()

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument(
        "--tau-empirical",
        required=True,
        type=Path,
        help="Tau2 empirical difficulty CSV (from baseline/compute_difficulty.py)",
    )
    ap.add_argument(
        "--synthetic-empirical",
        type=Path,
        default=None,
        help="Optional synthetic empirical difficulty CSV (from baseline/compute_difficulty.py)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO / "results" / "difficulty" / "summaries",
        help="Output folder",
    )
    args = ap.parse_args(argv)

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    tau2_counts = compute_tau2_write_counts()
    synthetic_counts = load_synthetic_write_counts()

    tau2_empirical = load_empirical(args.tau_empirical)
    tau2_merged = _merge_empirical(tau2_counts, tau2_empirical)

    synthetic_empirical = load_empirical(args.synthetic_empirical) if args.synthetic_empirical else {}
    synthetic_merged = _merge_empirical(synthetic_counts, synthetic_empirical)

    _save_hist_by_domain(
        by_domain=_values_by_domain(tau2_counts, "num_write"),
        title="τ²-bench: write-action count distribution (by domain)",
        xlabel="num_write",
        out_png=out_dir / "tau2_write_count_distribution.png",
        focus_domains=["retail", "airline", "telecom"],
    )

    _save_hist_by_domain(
        by_domain=_values_by_domain(synthetic_counts, "num_write"),
        title="Synthetic: write-action count distribution (by domain)",
        xlabel="num_write",
        out_png=out_dir / "synthetic_write_count_distribution.png",
    )

    tau2_diffs_by_domain = defaultdict(list)
    for r in tau2_merged:
        if r.get("difficulty") is not None:
            tau2_diffs_by_domain[str(r["domain"])].append(float(r["difficulty"]))

    _save_hist_by_domain(
        by_domain=tau2_diffs_by_domain,
        title="τ²-bench: empirical difficulty distribution (by domain)",
        xlabel="difficulty (1 - pass_rate)",
        out_png=out_dir / "tau2_empirical_difficulty_distribution.png",
        focus_domains=["retail", "airline", "telecom"],
    )

    if synthetic_empirical:
        syn_diffs_by_domain = defaultdict(list)
        for r in synthetic_merged:
            if r.get("difficulty") is not None:
                syn_diffs_by_domain[str(r["domain"])].append(float(r["difficulty"]))

        _save_hist_by_domain(
            by_domain=syn_diffs_by_domain,
            title="Synthetic: empirical difficulty distribution (by domain)",
            xlabel="difficulty (1 - pass_rate)",
            out_png=out_dir / "synthetic_empirical_difficulty_distribution.png",
        )

    _save_scatter(
        rows=[r for r in tau2_merged if r.get("difficulty") is not None],
        title="τ²-bench: write actions vs empirical difficulty",
        out_png=out_dir / "tau2_scatter_write_vs_empirical.png",
    )

    if synthetic_empirical:
        _save_scatter(
            rows=[r for r in synthetic_merged if r.get("difficulty") is not None],
            title="Synthetic: write actions vs empirical difficulty",
            out_png=out_dir / "synthetic_scatter_write_vs_empirical.png",
        )

    def _mean(xs: List[float]) -> Optional[float]:
        return sum(xs) / len(xs) if xs else None

    summary_rows: List[Dict[str, object]] = []
    for dataset, rows in [("tau2", tau2_merged), ("synthetic", synthetic_merged)]:
        writes = [float(r["num_write"]) for r in rows]
        diffs = [float(r["difficulty"]) for r in rows if r.get("difficulty") is not None]
        summary_rows.append(
            {
                "dataset": dataset,
                "n_tasks": len(rows),
                "mean_num_write": round(_mean(writes) or 0.0, 4),
                "n_tasks_with_empirical": len(diffs),
                "mean_empirical_difficulty": round(_mean(diffs), 4) if diffs else None,
            }
        )

    _write_csv(out_dir / "difficulty_summary.csv", summary_rows)
    (out_dir / "difficulty_summary.json").write_text(json.dumps(summary_rows, indent=2), encoding="utf-8")

    print(f"Saved plots to {out_dir}")
    if not synthetic_empirical:
        print("NOTE: No synthetic empirical difficulty file provided; synthetic empirical plots were skipped.")

    # Write a per-domain summary table for plotting/analysis.
    (out_dir / 'README.md').write_text(
        '# Difficulty summaries\n\nSee difficulty_summary.csv and domain_summary.csv.\n',
        encoding='utf-8',
    )
    _write_domain_summary(out_dir, [('tau2', tau2_merged), ('synthetic', synthetic_merged)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
