"""Create coverage summaries from the merged labels and scores.

Run from the repository root: python coverage/plot_coverage.py
"""

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "coverage"
NAMES = {"tau2": "τ²-bench", "synthetic": "Synthetic"}
COLORS = {"tau2": "#2878A5", "synthetic": "#C56635"}
TASK_TYPES = ["information_lookup", "record_modification", "cancellation_or_refund",
              "new_creation", "troubleshooting", "verification_or_compliance",
              "policy_edge_case_or_refusal", "other"]
DOMAINS = {"tau2": ["airline", "retail", "telecom"],
           "synthetic": ["banking", "healthcare", "insurance", "manufacturing"]}


def label(text):
    return text.replace("_", " ").capitalize()


def load_inputs():
    labels = {}
    paths = [FOLDER / "attribute_scores.csv", FOLDER / "vendi_scores.csv",
             ROOT / "data/processed/tasks.jsonl"]
    tasks = [json.loads(line) for line in paths[-1].read_text().splitlines() if line.strip()]
    vendi = pd.read_csv(paths[1])
    attributes = pd.read_csv(paths[0])
    for dataset in NAMES:
        path = FOLDER / "labels" / f"labels_{dataset}.csv"
        paths.append(path)
        df = pd.read_csv(path, dtype={"task_id": str}, keep_default_na=False)
        expected = [t for t in tasks if t["dataset"] == dataset]
        ids = [(t["domain"] + ":" if dataset == "tau2" else "") + t["task_id"]
               for t in expected]
        if df["task_id"].duplicated().any() or set(df["task_id"]) != set(ids):
            raise ValueError(f"{dataset}: labels do not match the tasks used for Vendi scoring")
        if not set(df["domain"]).issubset(DOMAINS[dataset]):
            raise ValueError(f"{dataset}: unexpected domain labels")
        if not set(df["task_type"]).issubset(TASK_TYPES):
            raise ValueError(f"{dataset}: unexpected task-type labels")
        total = vendi[(vendi.dataset == dataset) & (vendi.domain == "all")]
        if len(total) != 1 or int(total.iloc[0]["n"]) != len(df):
            raise ValueError(f"{dataset}: Vendi task count does not match the labels")
        if len(attributes[(attributes.dataset == dataset) & (attributes.attribute == "average")]) != 1:
            raise ValueError(f"{dataset}: missing or duplicate Attribute Diversity score")
        labels[dataset] = df
    return labels, attributes, vendi, paths


def distributions(labels):
    rows = []
    for dataset, df in labels.items():
        for domain in ["all", *DOMAINS[dataset]]:
            subset = df if domain == "all" else df[df.domain == domain]
            if subset.empty:
                continue
            tools = subset["tools"].map(lambda text: sorted({t.strip() for t in text.split("|") if t.strip()}))
            categories = {
                "task_type": (subset.task_type.value_counts(), TASK_TYPES),
                "tools": (tools.explode().dropna().value_counts(),
                          sorted({t.strip() for text in df.tools for t in text.split("|") if t.strip()})),
            }
            if domain == "all":
                categories["domain"] = (subset.domain.value_counts(), DOMAINS[dataset])
            for attribute, (counts, names) in categories.items():
                for category in names:
                    count = int(counts.get(category, 0))
                    rows.append({"dataset": dataset, "domain": domain, "attribute": attribute,
                                 "category": category, "count": count, "n_tasks": len(subset),
                                 "percent": 100 * count / len(subset)})
    return pd.DataFrame(rows)


def save(fig, output, name):
    for suffix in ["png", "svg"]:
        path = output / f"{name}.{suffix}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        if suffix == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def bar_panels(data, labels, output, attribute, title, name, top=None):
    fig, axes = plt.subplots(1, 2, figsize=(13, 7 if top else 4), layout="constrained")
    for ax, dataset in zip(axes, NAMES):
        rows = data[(data.dataset == dataset) & (data.domain == "all") & (data.attribute == attribute)]
        rows = rows.sort_values(["percent", "category"], ascending=[False, True])
        if top:
            rows = rows.head(top)
        bars = ax.barh([label(c) for c in rows.category], rows.percent, color=COLORS[dataset])
        ax.invert_yaxis()
        ax.set_xlim(0, 112)
        ax.xaxis.set_major_formatter(PercentFormatter())
        ax.set_xlabel("Percentage of tasks")
        ax.set_title(f"{NAMES[dataset]} (n={len(labels[dataset])})")
        ax.bar_label(bars, labels=[f"{p:.1f}% ({n})" for p, n in zip(rows.percent, rows["count"])],
                     padding=4, fontsize=8)
        sns.despine(ax=ax)
    fig.suptitle(title)
    save(fig, output, name)


def task_type_chart(data, labels, output):
    fig, ax = plt.subplots(figsize=(11, 6), layout="constrained")
    for offset, dataset in zip([-0.2, 0.2], NAMES):
        rows = data[(data.dataset == dataset) & (data.domain == "all") & (data.attribute == "task_type")]
        rows = rows.set_index("category").loc[TASK_TYPES]
        bars = ax.barh([i + offset for i in range(len(TASK_TYPES))], rows.percent,
                       height=0.38, color=COLORS[dataset], label=f"{NAMES[dataset]} (n={len(labels[dataset])})")
        ax.bar_label(bars, labels=[f"{p:.1f}%" for p in rows.percent], padding=3, fontsize=8)
    ax.set_yticks(range(len(TASK_TYPES)), [label(t) for t in TASK_TYPES])
    ax.invert_yaxis()
    maximum = data[(data.domain == "all") & (data.attribute == "task_type")].percent.max()
    ax.set_xlim(0, max(65, maximum + 12))
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.set_xlabel("Percentage of tasks")
    ax.set_title("Task types across datasets")
    ax.legend(loc="lower right")
    sns.despine(ax=ax)
    save(fig, output, "task_type_distribution")


def heatmaps(data, output, attribute):
    for dataset in NAMES:
        rows = data[(data.dataset == dataset) & (data.domain != "all") & (data.attribute == attribute)]
        matrix = rows.pivot(index="category", columns="domain", values="percent")
        order = TASK_TYPES if attribute == "task_type" else sorted(matrix.index)
        matrix = matrix.reindex(index=order, columns=DOMAINS[dataset])
        matrix.index = [label(x) for x in matrix.index]
        matrix.columns = [label(x) for x in matrix.columns]
        fig, ax = plt.subplots(figsize=(10, max(5, len(matrix) * 0.29)), layout="constrained")
        sns.heatmap(matrix, ax=ax, cmap="Blues", vmin=0, vmax=100, annot=True, fmt=".0f",
                    annot_kws={"fontsize": 8}, cbar_kws={"label": "% of tasks within domain"})
        ax.set_title(f"{NAMES[dataset]}: {'task types' if attribute == 'task_type' else 'tools'} by domain")
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", rotation=0)
        save(fig, output, f"{attribute}_by_domain_{dataset}")


def score_charts(attributes, vendi, output):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    totals = vendi[vendi.domain == "all"].set_index("dataset")
    averages = attributes[attributes.attribute == "average"].set_index("dataset")
    for ax, values, title in [(axes[0], averages.score, "Attribute Diversity"),
                               (axes[1], totals.vendi_score_norm, "Normalized Vendi (VS/n)")]:
        bars = ax.bar([NAMES[d] for d in NAMES], [values[d] for d in NAMES], color=list(COLORS.values()))
        ax.set_ylim(0, 1.1)
        ax.bar_label(bars, fmt="%.4f", padding=4)
        ax.set_title(title)
        ax.set_ylabel("Score")
        sns.despine(ax=ax)
    fig.suptitle("Coverage scores — " + "; ".join(
        f"{NAMES[d]}: {int(totals.loc[d, 'n'])} tasks" for d in NAMES))
    save(fig, output, "coverage_scores")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), layout="constrained")
    for ax, dataset in zip(axes, NAMES):
        rows = vendi[(vendi.dataset == dataset) & (vendi.domain != "all")].sort_values("vendi_score_norm")
        bars = ax.barh([f"{label(r.domain)} (n={r.n})" for r in rows.itertuples()],
                       rows.vendi_score_norm, color=COLORS[dataset])
        ax.set_xlim(0, 1)
        ax.bar_label(bars, fmt="%.3f", padding=4)
        ax.set_title(f"{NAMES[dataset]} — {'domains' if dataset == 'tau2' else 'agent categories'}")
        ax.set_xlabel("Normalized Vendi (VS/n)")
        sns.despine(ax=ax)
    fig.suptitle("Description diversity by group — group sizes differ")
    save(fig, output, "vendi_by_domain")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/coverage/summaries")
    args = parser.parse_args()
    labels, attributes, vendi, paths = load_inputs()
    data = distributions(labels)
    counts_path = FOLDER / "attribute_counts.csv"
    keys = ["dataset", "attribute", "category"]
    saved_counts = pd.read_csv(counts_path).set_index(keys)["count"].sort_index()
    current_counts = data[data.domain == "all"].set_index(keys)["count"].sort_index()
    if not saved_counts.equals(current_counts):
        raise ValueError("Labels differ from the saved attribute counts. Recompute the scores first.")
    paths.append(counts_path)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=0.9)
    data.to_csv(output / "distribution_counts.csv", index=False, float_format="%.6f")
    attributes.to_csv(output / "attribute_scores.csv", index=False)
    vendi.to_csv(output / "vendi_scores.csv", index=False)
    bar_panels(data, labels, output, "domain", "Tasks by domain — labels differ between datasets", "domain_distribution")
    task_type_chart(data, labels, output)
    bar_panels(data, labels, output, "tools", "15 most common tools — tasks may use several tools", "tool_usage", top=15)
    heatmaps(data, output, "task_type")
    heatmaps(data, output, "tools")
    score_charts(attributes, vendi, output)
    metadata = {
        "task_counts": {d: len(df) for d, df in labels.items()},
        "scope": "tau2 base split and synthetic tasks from the merged coverage labels",
        "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "packages": {p: version(p) for p in ["pandas", "matplotlib", "seaborn"]},
    }
    (output / "plot_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Saved 9 charts (PNG and SVG), source tables, and metadata to {output}")


if __name__ == "__main__":
    main()
