"""Recompute and validate coverage with the new workflow labels."""

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

path = Path(__file__).resolve().parent.parent
labels_path = path / "coverage" / "labels" / "workflows" / "workflow_labels.csv"
catalog_path = path / "coverage" / "labels" / "workflows" / "workflow_catalog.csv"
conditions_path = path / "labeling" / "workflow_sources" / "tau2" / "conditions.json"
tasks_path = path / "data" / "processed" / "tasks.jsonl"
output_dir = path / "results" / "coverage" / "workflow"

SEED = 42
RANDOM_TRIES = 20


def split(value):
    if pd.isna(value) or value == "":
        return set()
    return set(value.split("|"))


def score(tasks, categories):
    counts = Counter(label for labels in tasks for label in labels)
    total = sum(counts[c] for c in categories)
    found = sum(1 for c in categories if counts[c] > 0)
    coverage = found / len(categories)

    if total == 0:
        return coverage, float("nan")
    probabilities = [counts[c] / total for c in categories if counts[c] > 0]
    entropy = sum(-p * math.log(p) for p in probabilities)
    return coverage, entropy / math.log(len(categories))


def load_groups():
    labels = pd.read_csv(labels_path)
    catalog = pd.read_csv(catalog_path)
    conditions = sorted(json.loads(conditions_path.read_text()))

    groups = []
    for (dataset, group), tasks in labels.groupby(["dataset", "agent_category"]):
        workflows = catalog[(catalog["dataset"] == dataset) & (catalog["agent_category"] == group)]
        attributes = {"workflow": ("workflow_keys", sorted(workflows["workflow_key"]))}
        if group == "telecom":
            attributes["telecom_condition"] = ("telecom_conditions", conditions)
        groups.append((dataset, group, tasks, attributes))
    return groups


def removal_test(tasks, categories, rng):
    full_coverage, full_entropy = score(tasks, categories)
    rows = []
    for category in categories:
        kept = [t for t in tasks if category not in t]
        if len(kept) == len(tasks):
            continue

        coverage, entropy = score(kept, categories)
        random_scores = [score(rng.sample(tasks, len(kept)), categories) for _ in range(RANDOM_TRIES)]

        rows.append({
            "removed": category,
            "num_removed": len(tasks) - len(kept),
            "coverage_full": round(full_coverage, 4),
            "coverage_after": round(coverage, 4),
            "coverage_random": round(sum(c for c, e in random_scores) / RANDOM_TRIES, 4),
            "entropy_full": round(full_entropy, 4),
            "entropy_after": round(entropy, 4),
            "entropy_random": round(sum(e for c, e in random_scores) / RANDOM_TRIES, 4),
        })
    return rows


def run_vendi(groups, rng):
    sys.path.insert(0, str(path))
    from coverage.vendi_score import embed, vendi_score

    descriptions = {}
    for line in tasks_path.read_text().splitlines():
        task = json.loads(line)
        task_id = f"{task['domain']}:{task['task_id']}" if task["dataset"] == "tau2" else task["task_id"]
        descriptions[task_id] = task["description"]

    catalog = pd.read_csv(catalog_path)
    names = dict(zip(catalog["workflow_key"], catalog["workflow_name"]))

    score_rows, removal_rows = [], []
    for dataset, group, tasks, attributes in groups:
        workflows = [split(v) for v in tasks["workflow_keys"]]
        plain = [descriptions[t] for t in tasks["task_id"]]
        with_names = [f"{d}\nWorkflows: {', '.join(sorted(names[w] for w in wf))}"
                      for d, wf in zip(plain, workflows)]

        for text_type, texts in [("description", plain), ("description_plus_workflow", with_names)]:
            embeddings = embed(texts)
            n = len(texts)
            vs = vendi_score(embeddings)
            score_rows.append({"dataset": dataset, "group": group, "text": text_type, "n": n,
                               "vendi_score": round(vs, 4), "vendi_score_norm": round(vs / n, 4)})

            for workflow in sorted(set().union(*workflows)):
                keep = [i for i, wf in enumerate(workflows) if workflow not in wf]
                if len(keep) < 2:
                    continue
                random_vs = [vendi_score(embeddings[sorted(rng.sample(range(n), len(keep)))])
                             for _ in range(RANDOM_TRIES)]
                removal_rows.append({"dataset": dataset, "group": group, "text": text_type,
                                     "removed": workflow, "n_left": len(keep),
                                     "vs_full": round(vs, 4),
                                     "vs_after": round(vendi_score(embeddings[keep]), 4),
                                     "vs_random": round(sum(random_vs) / RANDOM_TRIES, 4)})

    pd.DataFrame(score_rows).to_csv(output_dir / "workflow_vendi_scores.csv", index=False)
    pd.DataFrame(removal_rows).to_csv(output_dir / "workflow_vendi_removal.csv", index=False)


def make_plots(scores, removal):
    workflow = scores[scores["attribute"] == "workflow"]
    names = workflow["dataset"] + ": " + workflow["group"]
    colors = ["#202833" if d == "tau2" else "#8c7344" for d in workflow["dataset"]]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, column in zip(axes, ["catalog_coverage", "normalized_entropy"]):
        ax.barh(names, workflow[column], color=colors)
        ax.set_xlim(0, 1)
        ax.set_title(column.replace("_", " ").capitalize())
    fig.suptitle("Workflow coverage by group (dark = tau2, gold = synthetic)")
    fig.tight_layout()
    fig.savefig(output_dir / "workflow_coverage_by_group.png", dpi=150)
    plt.close(fig)

    removed = removal[removal["attribute"] == "workflow"]
    names = removed["dataset"] + ": " + removed["group"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(removed["coverage_full"] - removed["coverage_random"], names,
               facecolors="none", edgecolors="gray", label="random removal (same size)")
    ax.scatter(removed["coverage_full"] - removed["coverage_after"], names,
               marker="x", color="#b23a2b", label="workflow removed")
    ax.set_xlabel("Drop in catalog coverage")
    ax.set_title("Removing a workflow vs removing random tasks")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_dir / "workflow_removal_validation.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    groups = load_groups()

    score_rows, removal_rows = [], []
    for dataset, group, tasks, attributes in groups:
        for attribute, (column, categories) in attributes.items():
            label_sets = [split(v) for v in tasks[column]]
            coverage, entropy = score(label_sets, categories)
            score_rows.append({"dataset": dataset, "group": group, "attribute": attribute,
                               "num_tasks": len(tasks), "num_categories": len(categories),
                               "catalog_coverage": round(coverage, 4),
                               "normalized_entropy": round(entropy, 4)})
            for row in removal_test(label_sets, categories, rng):
                removal_rows.append({"dataset": dataset, "group": group, "attribute": attribute, **row})

    scores = pd.DataFrame(score_rows)
    removal = pd.DataFrame(removal_rows)
    scores.to_csv(output_dir / "workflow_coverage_scores.csv", index=False)
    removal.to_csv(output_dir / "workflow_removal_validation.csv", index=False)
    make_plots(scores, removal)

    if "--vendi" in sys.argv:
        run_vendi(groups, rng)

    print(scores.to_string(index=False))
    workflow_removals = removal[removal["attribute"] == "workflow"]
    worse_than_random = (workflow_removals["coverage_after"] < workflow_removals["coverage_random"]).mean()
    print(f"\n{len(workflow_removals)} workflow removals; coverage fell more than random in {worse_than_random:.0%}")
    print(f"Saved results to {output_dir}")
