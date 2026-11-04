#!/usr/bin/env python3
"""Joint overall summary (Issue #21).

Creates a single radar chart comparing τ²-bench vs synthetic across:
- Structural difficulty score (mean write-action count, normalized to [0, 1])
- Coverage: normalized Vendi score (`coverage/vendi_scores.csv`, domain=all)
- Coverage: attribute diversity average (`coverage/attribute_scores.csv`)

Outputs (default):
- `results/overall/overall_scores.csv`
- `results/overall/overall_radar.png`
- `results/overall/overall_radar.svg`

Run:
  python plot_overall_summary.py
"""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Dict, List


def _configure_matplotlib_cache() -> None:
    """Force matplotlib to use a writable cache directory.

    This must run *before* importing matplotlib, otherwise matplotlib may try to
    initialize its default cache under the user profile.
    """

    if os.environ.get("MPLCONFIGDIR"):
        return
    try:
        cache_dir = Path(tempfile.gettempdir()) / "matplotlib"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)
    except Exception:
        pass


_configure_matplotlib_cache()

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from difficulty.summarize_difficulty import compute_tau2_write_counts, load_synthetic_write_counts


REPO = Path(__file__).resolve().parent


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def load_coverage_metrics() -> Dict[str, Dict[str, float]]:
    vendi_rows = _read_csv(REPO / "coverage" / "vendi_scores.csv")
    attr_rows = _read_csv(REPO / "coverage" / "attribute_scores.csv")

    vendi_norm = {}
    for r in vendi_rows:
        if (r.get("domain") or "").strip() == "all":
            vendi_norm[(r.get("dataset") or "").strip()] = float(r["vendi_score_norm"])

    attr_avg = {}
    for r in attr_rows:
        if (r.get("attribute") or "").strip() == "average":
            attr_avg[(r.get("dataset") or "").strip()] = float(r["score"])

    out = {}
    for ds in ("tau2", "synthetic"):
        out[ds] = {
            "coverage_vendi_norm": vendi_norm.get(ds, 0.0),
            "coverage_attribute_diversity": attr_avg.get(ds, 0.0),
        }
    return out


def load_structural_difficulty_means() -> Dict[str, float]:
    tau2_writes = [float(r["num_write"]) for r in compute_tau2_write_counts()]
    syn_writes = [float(r["num_write"]) for r in load_synthetic_write_counts()]
    return {"tau2": _mean(tau2_writes), "synthetic": _mean(syn_writes)}


def radar_plot(metrics_by_dataset: Dict[str, Dict[str, float]], out_png: Path, out_svg: Path) -> None:
    labels = [
        "difficulty_write_norm",
        "coverage_vendi_norm",
        "coverage_attribute_diversity",
    ]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(6.5, 6.0))
    ax = plt.subplot(111, polar=True)

    for ds, color in [("tau2", "tab:blue"), ("synthetic", "tab:orange")]:
        vals = [metrics_by_dataset[ds][k] for k in labels]
        vals += vals[:1]
        ax.plot(angles, vals, linewidth=2, label=ds, color=color)
        ax.fill(angles, vals, alpha=0.15, color=color)

    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0, 1)
    ax.set_title("Overall summary: Difficulty + Coverage (τ² vs Synthetic)")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10), frameon=False)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=160)
    fig.savefig(out_svg)
    plt.close(fig)


def main() -> int:
    out_dir = REPO / "results" / "overall"
    out_dir.mkdir(parents=True, exist_ok=True)

    coverage = load_coverage_metrics()
    write_means = load_structural_difficulty_means()
    max_mean = max(write_means.values()) or 1.0

    metrics = {}
    for ds in ("tau2", "synthetic"):
        metrics[ds] = {
            "difficulty_write_norm": round(write_means[ds] / max_mean, 4),
            "coverage_vendi_norm": round(coverage[ds]["coverage_vendi_norm"], 4),
            "coverage_attribute_diversity": round(coverage[ds]["coverage_attribute_diversity"], 4),
            "difficulty_mean_num_write": round(write_means[ds], 4),
        }

    out_csv = out_dir / "overall_scores.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["dataset"] + list(metrics["tau2"].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for ds in ("tau2", "synthetic"):
            w.writerow({"dataset": ds, **metrics[ds]})

    radar_plot(metrics, out_dir / "overall_radar.png", out_dir / "overall_radar.svg")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_dir / 'overall_radar.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
