
"""Domain-level Coverage and Difficulty profiles (#65)."""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

path = Path(__file__).resolve().parent.parent
frozen = path / "results" / "scoring" / "weekend_weight_trials_v1" / "inputs"
labels_path = frozen / "workflow_labels.csv"
catalog_path = frozen / "workflow_catalog.csv"
coverage_csv_path = frozen / "workflow_coverage_scores.csv"
difficulty_path = path / "results" / "difficulty" / "designed_final_v27" / "task_scores.json"
domain_difficulty_path = path / "results" / "difficulty" / "designed_final_v27" / "domain_summary.csv"
diagnostics_path = path / "results" / "framework" / "metrics_by_domain.csv"
output_dir = path / "results" / "domain_analysis"

TAU2_DOMAINS = ["airline", "retail", "telecom"]
COLORS = {"airline": "#202833", "retail": "#8c7344", "telecom": "#b9b4a8"}
WEIGHT = 0.5


def split(value):
    if pd.isna(value) or value == "":
        return set()
    return set(value.split("|"))


def coverage_by_group():
    """Workflow completeness and entropy for each group, from the frozen labels and catalog."""
    labels = pd.read_csv(labels_path)
    catalog = pd.read_csv(catalog_path)
    rows = []
    for (dataset, group), tasks in labels.groupby(["dataset", "agent_category"]):
        workflows = sorted(catalog[(catalog["dataset"] == dataset) & (catalog["agent_category"] == group)]["workflow_key"])
        counts = Counter(w for v in tasks["workflow_keys"] for w in split(v) if w in workflows)
        total = sum(counts.values())
        represented = sum(1 for w in workflows if counts[w] > 0)
        entropy = sum(-counts[w] / total * math.log(counts[w] / total) for w in workflows if counts[w]) / math.log(len(workflows))
        rows.append({"dataset": dataset, "domain": group, "n_tasks": len(tasks),
                     "workflows_declared": len(workflows), "workflows_represented": represented,
                     "workflow_completeness": represented / len(workflows), "workflow_entropy": entropy})
    return pd.DataFrame(rows)


def task_scores():
    data = json.loads(difficulty_path.read_text())
    return pd.DataFrame([{"dataset": t["dataset"], "domain": t["domain"], "task_id": t["task_id"],
                          "score": t["score"]} for t in data["tasks"]]), data


def check(profiles, tasks, data):
    """Stop if anything disagrees with the published files."""
    published = pd.read_csv(coverage_csv_path)
    published = published[published["attribute"] == "workflow"].set_index(["dataset", "group"])
    for _, r in profiles.iterrows():
        p = published.loc[(r["dataset"], r["domain"])]
        assert abs(p["catalog_coverage"] - r["workflow_completeness"]) < 5e-5, r["domain"]
        assert abs(p["normalized_entropy"] - r["workflow_entropy"]) < 5e-5, r["domain"]
    domain_summary = pd.read_csv(domain_difficulty_path).set_index(["dataset", "domain"])
    for (dataset, domain), d in tasks.groupby(["dataset", "domain"]):
        assert abs(d["score"].mean() - domain_summary.loc[(dataset, domain), "mean"]) < 1e-9, domain
    for dataset in ["tau2", "synthetic"]:
        p = profiles[profiles["dataset"] == dataset]
        rebuilt = (p["difficulty_mean"] * p["n_tasks"]).sum() / p["n_tasks"].sum()
        assert abs(rebuilt - data["datasets"][dataset]["mean"]) < 1e-9, dataset
    return "all checks passed"


def plot(profiles, tasks):
    tau2 = profiles[profiles["dataset"] == "tau2"].set_index("domain").loc[TAU2_DOMAINS]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    width = 0.27
    metrics = {"workflow_completeness": "Workflow\ncompleteness", "workflow_entropy": "Workflow\nentropy",
               "coverage": "Coverage C\n(0.5 + 0.5)"}
    for i, domain in enumerate(TAU2_DOMAINS):
        positions = [x + (i - 1) * width for x in range(len(metrics))]
        bars = axes[0].bar(positions, tau2.loc[domain, list(metrics)], width, label=domain, color=COLORS[domain])
        axes[0].bar_label(bars, fmt="%.2f", fontsize=8)
    axes[0].set_xticks(range(len(metrics)), metrics.values())
    axes[0].set_ylim(0, 1.12)
    axes[0].set_title("Coverage within each domain's own workflow catalog")
    axes[0].legend(frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, -0.18))

    data = [tasks[(tasks["dataset"] == "tau2") & (tasks["domain"] == d)]["score"] for d in TAU2_DOMAINS]
    box = axes[1].boxplot(data, tick_labels=[f"{d}\n(n={len(x)})" for d, x in zip(TAU2_DOMAINS, data)],
                          patch_artist=True, showmeans=True,
                          meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black"})
    for patch, d in zip(box["boxes"], TAU2_DOMAINS):
        patch.set_facecolor(COLORS[d])
        patch.set_alpha(0.7)
    for x, d in enumerate(TAU2_DOMAINS, start=1):
        axes[1].text(x + 0.3, tau2.loc[d, "difficulty_mean"], f"{tau2.loc[d, 'difficulty_mean']:.2f}", va="center", fontsize=8)
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("Designed difficulty (0-100)")
    axes[1].set_title("Designed difficulty v1.1 (diamond = mean)")

    fig.tight_layout()
    fig.savefig(output_dir / "tau2_domain_profiles.png", dpi=150)
    plt.close(fig)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


if __name__ == "__main__":
    output_dir.mkdir(parents=True, exist_ok=True)

    profiles = coverage_by_group()
    profiles["coverage"] = 0.5 * profiles["workflow_completeness"] + 0.5 * profiles["workflow_entropy"]

    difficulty = pd.read_csv(domain_difficulty_path).rename(columns={
        "mean": "difficulty_mean", "median": "difficulty_median", "q1": "difficulty_q1",
        "q3": "difficulty_q3", "min": "difficulty_min", "max": "difficulty_max"})
    profiles = profiles.merge(difficulty[["dataset", "domain", "difficulty_mean", "difficulty_median",
                                          "difficulty_q1", "difficulty_q3", "difficulty_min", "difficulty_max"]],
                              on=["dataset", "domain"])
    profiles["composite_50_50"] = 100 * (WEIGHT * profiles["coverage"] + (1 - WEIGHT) * profiles["difficulty_mean"] / 100)

    diagnostics = pd.read_csv(diagnostics_path)
    diagnostics = diagnostics[diagnostics["domain"] != "all"][["dataset", "domain", "vendi_score_norm",
                                                               "mean_write_count", "mean_empirical_difficulty"]]
    profiles = profiles.merge(diagnostics, on=["dataset", "domain"], how="left")

    tasks, data = task_scores()
    result = check(profiles, tasks, data)

    profiles = profiles.sort_values(["dataset", "domain"], ascending=[False, True])
    profiles.to_csv(output_dir / "domain_profiles.csv", index=False)
    plot(profiles, tasks)

    provenance = {
        "api_calls": 0,
        "selected_weights": "50% Coverage / 50% Difficulty (#62)",
        "checks": result,
        "inputs": {str(p.relative_to(path)): sha256(p) for p in
                   [labels_path, catalog_path, coverage_csv_path, difficulty_path, domain_difficulty_path, diagnostics_path]},
    }
    (output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    show = ["dataset", "domain", "n_tasks", "workflow_completeness", "workflow_entropy", "coverage",
            "difficulty_mean", "composite_50_50"]
    print(profiles[show].round(4).to_string(index=False))
    print(f"\n{result}. Saved results to {output_dir}")
